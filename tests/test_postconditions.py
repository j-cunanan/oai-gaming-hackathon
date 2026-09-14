import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from repro.agents.openai import BudgetExceeded
from repro.computer.recorder import Recorder
from repro.config import Settings
from repro.models import (
    Action,
    CandidateVerification,
    Case,
    CaseInput,
    OracleSpec,
    Reproduction,
    SequenceVerdict,
)
from repro.orchestration.manager import Manager
from repro.orchestration.postconditions import (
    Conclusion,
    current_plan,
    plan_postconditions,
    trigger_identity,
)
from repro.storage.store import Store


def example():
    return Case(
        report=CaseInput(
            title="Save crash",
            body="Saving crashes; the resulting map also cannot reopen.",
            target_commit="a" * 40,
        ),
        patch_artifact="candidate-A.patch",
        reproduction=Reproduction(
            game="mindustry",
            commit="a" * 40,
            steps=[Action(action="wait", checkpoint="trigger", semantic="Save the map")],
            oracle=OracleSpec(
                kind="crash",
                description="Saving crashes; the resulting map cannot reopen.",
                log_pattern="TargetDummy",
            ),
            successful_runs=5,
            total_runs=5,
            deterministic=True,
        ),
    )


def plan_for(case):
    return CandidateVerification(
        trigger_sha256=trigger_identity(case),
        patch_artifact=case.patch_artifact,
        followup_steps=[
            Action(action="wait", checkpoint="reopened", semantic="Inspect the reopened map")
        ],
        oracle=OracleSpec(
            kind="sequence",
            description=case.reproduction.oracle.description,
            checkpoints=["trigger", "reopened"],
        ),
    )


def observation(running=True):
    return {
        "screenshot": base64.b64encode(b"recorded test image").decode(),
        "process": {"running": running},
        "logs": "",
    }


@pytest.mark.parametrize("change", ["report", "trigger", "oracle", "patch"])
def test_plan_is_bound_to_the_report_trigger_oracle_and_patch(change):
    case = example()
    case.candidate_verification = plan_for(case)
    assert current_plan(case) is case.candidate_verification
    if change == "report":
        case.report.body += " Additional required behavior."
    elif change == "trigger":
        case.reproduction.steps.append(Action(action="wait"))
    elif change == "oracle":
        case.reproduction.oracle.log_pattern = "DifferentCrash"
    else:
        case.patch_artifact = "candidate-B.patch"
    assert current_plan(case) is None


async def test_planning_rejects_incomplete_proof_and_preserves_the_confirmed_trigger(
    tmp_path, monkeypatch
):
    case = example()
    original = case.reproduction.model_copy(deep=True)
    store = Store(tmp_path)
    sandbox = SimpleNamespace(
        reset=AsyncMock(return_value=observation()),
        action=AsyncMock(return_value=observation()),
        observe=AsyncMock(return_value=observation()),
    )
    recorder = Recorder(store, case, sandbox)
    verdicts = [
        SequenceVerdict(
            observed=False,
            expected_state_reached=False,
            symptom_absent=False,
            confidence=0.9,
            explanation="Reload not visible",
            evidence=["screen"],
        ),
        SequenceVerdict(
            observed=False,
            expected_state_reached=True,
            symptom_absent=True,
            confidence=0.95,
            explanation="Saved map reopened with object retained",
            evidence=["screen"],
        ),
    ]
    verifier = AsyncMock(side_effect=verdicts)
    monkeypatch.setattr("repro.orchestration.postconditions.verify", verifier)

    async def loop(prompt, tools, **kwargs):
        assert case.report.body in prompt
        handlers = {t.name: t.handler for t in tools}
        await handlers["computer"](Action(action="wait", checkpoint="after-save"))
        rejected = await handlers["finish"](
            Conclusion(
                outcome="verified",
                summary="Attempt",
                oracle=OracleSpec(
                    kind="sequence",
                    description="A weaker claim",
                    checkpoints=["trigger", "after-save"],
                ),
            )
        )
        assert not rejected["accepted"] and case.candidate_verification is None
        await handlers["computer"](Action(action="wait", checkpoint="reopened"))
        accepted = await handlers["finish"](
            Conclusion(
                outcome="verified",
                summary="Reopened",
                oracle=OracleSpec(
                    kind="sequence",
                    description="Another weaker claim",
                    checkpoints=["after-save", "reopened"],
                ),
            )
        )
        assert accepted["recorded"] and kwargs["done"]()

    model = SimpleNamespace(remaining_calls=50, loop=loop)
    plan = await plan_postconditions(
        Settings(_env_file=None), store, case, sandbox, model, recorder, []
    )
    assert len(plan.followup_steps) == 2
    assert case.reproduction == original
    assert current_plan(case) == plan
    for call in verifier.await_args_list:
        assert call.args[1].description == original.oracle.description
    assert all(e["kind"] != "validation_replay" for e in store.events(case.id))
    assert any(a["name"] == "candidate-verification.json" for a in store.artifacts(case.id))


async def test_stopped_candidate_cannot_plan_postconditions(tmp_path):
    case = example()
    store = Store(tmp_path)
    sandbox = SimpleNamespace(reset=AsyncMock(return_value=observation(False)))
    model = SimpleNamespace(remaining_calls=50, loop=AsyncMock())
    assert (
        await plan_postconditions(
            Settings(_env_file=None),
            store,
            case,
            sandbox,
            model,
            Recorder(store, case, sandbox),
            [],
        )
        is None
    )
    model.loop.assert_not_awaited()
    assert not case.candidate_verification


async def test_planning_reserves_calls_for_fresh_repetitions(tmp_path):
    case = example()
    model = SimpleNamespace(remaining_calls=7)
    sandbox = SimpleNamespace(reset=AsyncMock())
    with pytest.raises(BudgetExceeded, match="Insufficient calls"):
        await plan_postconditions(
            Settings(_env_file=None, repetitions=5), Store(tmp_path), case, sandbox, model, None, []
        )
    sandbox.reset.assert_not_awaited()


@pytest.mark.parametrize("available", [True, False, "budget_exhausted"])
async def test_candidate_validation_repeats_frozen_followups_or_leaves_gate_unrun(
    tmp_path, monkeypatch, available
):
    case = example()
    store = Store(tmp_path)
    has_plan = available is True
    plan = plan_for(case) if has_plan else None
    planner = AsyncMock(return_value=plan)
    if available == "budget_exhausted":
        planner.side_effect = BudgetExceeded("Planning reached its turn budget")
    monkeypatch.setattr("repro.orchestration.manager.plan_postconditions", planner)
    sandbox = SimpleNamespace(
        case=case,
        adapter=SimpleNamespace(build=["build"]),
        start=AsyncMock(),
        exec=AsyncMock(return_value=(0, "built")),
        reset=AsyncMock(return_value=observation()),
    )
    model = SimpleNamespace(structured=AsyncMock())
    recorder = SimpleNamespace(
        capture=lambda data, label: {**data, "screenshot_artifact": "smoke.png"}
    )

    async def replay(worker, recorder, model, steps, oracle, **kwargs):
        assert steps == case.reproduction.steps + plan.followup_steps
        assert oracle == plan.oracle and kwargs["phase"] == "post-patch"
        return SequenceVerdict(
            observed=False,
            expected_state_reached=True,
            symptom_absent=True,
            confidence=0.95,
            explanation="Complete save/reload",
            evidence=["image"],
        ), {**observation(), "screenshot_artifact": "image"}

    replay_mock = AsyncMock(side_effect=replay)
    monkeypatch.setattr("repro.orchestration.manager.replay", replay_mock)
    manager = Manager(Settings(_env_file=None, repetitions=2), store)
    manager.check_existing_tests = AsyncMock()
    await manager.validate(case, sandbox, model, recorder)
    assert replay_mock.await_count == (2 if has_plan else 0)
    assert case.reproduction.successful_runs == case.reproduction.total_runs == 5
    assert len(case.reproduction.steps) == 1
    gate = next(c for c in case.checks if c.name == "Original replay after patch")
    assert gate.status == ("pass" if has_plan else "not_run")
    assert next(c for c in case.checks if c.name == "Smoke test").status == "pass"
    if available == "budget_exhausted":
        assert any(e["kind"] == "fix_check_unavailable" for e in store.events(case.id))
        assert not any(e["kind"] == "validation_replay" for e in store.events(case.id))
    model.structured.assert_not_awaited()
