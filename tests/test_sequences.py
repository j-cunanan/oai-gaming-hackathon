import base64
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from repro.agents.oracle import verify
from repro.computer.recorder import Recorder
from repro.computer.replay import replay
from repro.config import Settings
from repro.models import Action, Case, CaseInput, Check, OracleSpec, Reproduction, SequenceVerdict
from repro.orchestration.manager import Manager
from repro.storage.store import Store


def screen(label="screen"):
    return {
        "screenshot": base64.b64encode(label.encode()).decode(),
        "screenshot_artifact": label,
        "process": {"running": True, "launched": True, "exit_code": None},
        "logs": "",
    }


def oracle():
    return OracleSpec(
        kind="sequence",
        description="A deleted patch returns after saving and reopening.",
        checkpoints=["deleted", "reopened"],
    )


def frames():
    return {
        label: {"index": index, "action": {"action": "wait"}, "observation": screen(label)}
        for index, label in enumerate(oracle().checkpoints, 1)
    }


def verdict(**updates):
    fields = dict(
        observed=True,
        expected_state_reached=True,
        symptom_absent=False,
        confidence=0.95,
        explanation="The recorded object returned.",
        evidence=["model-id"],
    )
    return SequenceVerdict(**(fields | updates))


@pytest.mark.parametrize("labels", [[], ["one"], ["one", "one"], ["one", " "], list("123456789")])
def test_sequence_requires_distinct_bounded_checkpoints(labels):
    with pytest.raises(ValidationError):
        OracleSpec(kind="sequence", description="Reported state change", checkpoints=labels)


@pytest.mark.parametrize(
    "problem", ["missing", "reversed", "duplicate_index", "missing_image", "crashed"]
)
async def test_missing_or_out_of_order_evidence_is_inconclusive_without_model_call(problem):
    checkpoints, observation = frames(), screen()
    if problem == "missing":
        del checkpoints["deleted"]
    elif problem == "reversed":
        checkpoints["deleted"]["index"] = 3
    elif problem == "duplicate_index":
        checkpoints["deleted"]["index"] = 2
    elif problem == "missing_image":
        del checkpoints["deleted"]["observation"]["screenshot"]
    else:
        observation["process"]["running"] = False
    model = SimpleNamespace(structured=AsyncMock())
    result = await verify(model, oracle(), observation, launched_ok=True, checkpoints=checkpoints)
    assert not result.observed and not result.symptom_absent
    assert result.confidence == 0
    model.structured.assert_not_called()


@pytest.mark.parametrize(
    "updates,observed,absent",
    [
        ({}, True, False),
        ({"observed": False, "symptom_absent": True}, False, True),
        ({"confidence": 0.4}, False, False),
        ({"expected_state_reached": False}, False, False),
        ({"symptom_absent": True}, False, False),
        ({"evidence": []}, False, False),
    ],
)
async def test_sequence_uses_chronological_images_and_fails_closed(updates, observed, absent):
    model = SimpleNamespace(structured=AsyncMock(return_value=verdict(**updates)))
    result = await verify(model, oracle(), screen(), launched_ok=True, checkpoints=frames())
    assert result.observed is observed and result.symptom_absent is absent
    assert result.evidence == ["deleted", "reopened"]
    images = model.structured.call_args.kwargs["screenshots"]
    assert [encoded for _, encoded in images] == [
        screen(k)["screenshot"] for k in oracle().checkpoints
    ]
    assert "not proof" in images[0][0]


async def test_replays_do_not_reuse_checkpoints_from_a_previous_attempt(tmp_path):
    store = Store(tmp_path)
    case = Case(
        report=CaseInput(
            title="Patch returned",
            body="Deleted patch returns on reopening.",
            target_commit="a" * 40,
        )
    )
    worker = SimpleNamespace(
        reset=AsyncMock(return_value=screen()), action=AsyncMock(return_value=screen())
    )
    recorder = Recorder(store, case, worker)
    model = SimpleNamespace(store=store, case=case, structured=AsyncMock(return_value=verdict()))
    steps = [Action(action="wait", checkpoint=label) for label in oracle().checkpoints]
    first, _ = await replay(worker, recorder, model, steps, oracle())
    assert first.observed
    second, _ = await replay(worker, recorder, model, steps[1:], oracle())
    assert not second.observed and not second.symptom_absent
    assert model.structured.await_count == 1
    assert list(recorder.checkpoints) == ["reopened"]
    assert recorder.attempt_actions == steps[1:]
    assert recorder.checkpoints["reopened"]["index"] == 1
    with pytest.raises(ValueError, match="already used"):
        await recorder.act(steps[1])
    assert worker.action.await_count == 3


async def test_sequence_includes_intervening_inputs_only_through_last_checkpoint():
    model = SimpleNamespace(structured=AsyncMock(return_value=verdict()))
    checkpoints = frames()
    checkpoints["reopened"]["index"] = 3
    actions = [
        Action(action="wait", checkpoint="deleted", semantic="Unverified claim"),
        Action(action="keypress", keys=["esc"]),
        Action(action="click", x=20, y=30, checkpoint="reopened"),
        Action(action="type", text="Later unrelated input"),
    ]
    await verify(
        model, oracle(), screen(), launched_ok=True, checkpoints=checkpoints, actions=actions
    )
    prompt = model.structured.call_args.args[1]
    trace = json.loads(prompt.split("through the final checkpoint: ", 1)[1].split("\n", 1)[0])
    assert trace == [
        {"step": 1, "action": "wait"},
        {"step": 2, "action": "keypress", "keys": ["esc"]},
        {"step": 3, "action": "click", "x": 20, "y": 30},
    ]


async def test_crash_signature_requires_both_nonzero_exit_and_matching_log():
    spec = OracleSpec(
        kind="crash", description="Save crashes with a specific signature", log_pattern="unitTeam"
    )
    obs = screen()
    obs["process"].update(running=False, exit_code=1)
    assert not (await verify(None, spec, obs, launched_ok=True)).observed
    obs["logs"] = "NullPointerException: unitTeam"
    assert (await verify(None, spec, obs, launched_ok=True)).observed
    obs["process"]["exit_code"] = 0
    assert not (await verify(None, spec, obs, launched_ok=True)).observed


@pytest.mark.parametrize(
    "reached,absent,passed", [(True, True, True), (False, True, False), (True, False, False)]
)
async def test_candidate_sequence_needs_positive_expected_behavior_evidence(
    tmp_path, monkeypatch, reached, absent, passed
):
    settings = Settings(_env_file=None, data_dir=tmp_path, repetitions=2)
    store = Store(tmp_path)
    case = Case(
        report=CaseInput(
            title="Patch returned",
            body="Deleted patch returns on reopening.",
            target_commit="a" * 40,
        ),
        reproduction=Reproduction(game="mindustry", commit="a" * 40, steps=[], oracle=oracle()),
    )
    worker = SimpleNamespace(
        start=AsyncMock(),
        exec=AsyncMock(return_value=(0, "Build passed")),
        reset=AsyncMock(return_value=screen()),
        adapter=SimpleNamespace(build=["build"]),
    )

    async def fresh_replay(*args, **kwargs):
        return verdict(
            observed=False, expected_state_reached=reached, symptom_absent=absent
        ), screen()

    monkeypatch.setattr("repro.orchestration.manager.replay", fresh_replay)
    manager = Manager(settings, store)

    async def tests(*args):
        case.checks.append(Check(name="Existing tests", status="pass", detail="Tests passed"))

    monkeypatch.setattr(manager, "check_existing_tests", tests)
    model = SimpleNamespace(structured=AsyncMock())
    await manager.validate(case, worker, model, Recorder(store, case, worker))
    gate = next(check for check in case.checks if check.name == "Original replay after patch")
    assert (gate.status == "pass") is passed
    model.structured.assert_not_called()
