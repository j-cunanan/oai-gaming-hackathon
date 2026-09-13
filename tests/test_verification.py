import base64
import time
from types import SimpleNamespace

from repro.agents.oracle import verify
from repro.config import Settings
from repro.models import BugSpec, Case, CaseInput, OracleSpec, State, Verdict
from repro.orchestration.manager import InvestigationResult, Manager
from repro.storage.store import Store


def observation():
    return {
        "screenshot": base64.b64encode(b"test-only-image").decode(),
        "screenshot_artifact": "actual-screen",
        "logs": "game started normally",
        "process": {"running": True, "launched": True, "exit_code": None},
    }


async def test_crash_oracle_does_not_count_failed_environment_startup():
    obs = observation()
    obs["process"] = {"running": False, "launched": True, "exit_code": 1}
    oracle = OracleSpec(kind="crash", description="Player reports a crash in gameplay")
    assert not (await verify(None, oracle, obs, launched_ok=False)).observed
    assert (await verify(None, oracle, obs, launched_ok=True)).observed


async def test_log_signatures_are_literal_and_visual_confidence_is_gated():
    oracle = OracleSpec(kind="log", description="Crash exception", log_pattern=".*")
    assert not (await verify(None, oracle, observation(), launched_ok=True)).observed

    async def uncertain(*args, **kwargs):
        return Verdict(
            observed=True, confidence=0.4, explanation="Unclear", evidence=["invented-id"]
        )

    verdict = await verify(
        SimpleNamespace(structured=uncertain),
        OracleSpec(kind="visual", description="Two duplicate buttons"),
        observation(),
        launched_ok=True,
    )
    assert not verdict.observed
    assert verdict.evidence == ["actual-screen"]


async def test_rejected_visual_proof_returns_to_investigator(tmp_path):
    store = Store(tmp_path / "data")
    case = Case(
        report=CaseInput(
            title="Duplicate buttons",
            body="The menu shows two identical buttons.",
            target_commit="a" * 40,
        ),
        spec=BugSpec(
            summary="Duplicate buttons",
            bug_class="ui",
            observed_behavior="Two identical buttons are visible",
            expected_behavior="One button",
            known_preconditions=[],
            uncertain_conditions=[],
            reproduction_hints=[],
            required_artifacts=[],
            severity="low",
            confidence=0.8,
        ),
    )
    store.save(case)
    root = tmp_path / "sandbox"
    repo = root / "repo"
    (repo / ".git").mkdir(parents=True)
    (root / "prepared.json").write_text("{}")

    async def observe():
        return observation()

    sandbox = SimpleNamespace(repo=repo, root=root, reset=observe, observe=observe)

    class Investigator:
        async def structured(self, *args, **kwargs):
            return Verdict(
                observed=False,
                confidence=0.99,
                explanation="Only one button is visible",
                evidence=["actual-screen"],
            )

        async def loop(self, prompt, tools, *, done, **kwargs):
            finish = next(t for t in tools if t.name == "finish")
            proposed = InvestigationResult(
                outcome="observed",
                summary="Claimed success",
                oracle=OracleSpec(kind="visual", description="A different, easier symptom"),
                limitations=[],
            )
            result = await finish.handler(proposed)
            assert result["accepted"] is False
            assert proposed.oracle.description == case.spec.observed_behavior
            assert not done()
            assert case.reproduction is None
            await finish.handler(
                InvestigationResult(
                    outcome="not_reproduced",
                    summary="No reliable proof after investigation",
                    oracle=None,
                    limitations=[],
                )
            )
            assert done()

    await Manager(Settings(_env_file=None, data_dir=tmp_path / "data"), store)._investigate(
        case, sandbox, Investigator(), time.monotonic()
    )
    assert store.get(case.id).state == State.NOT_REPRODUCED
    assert not store.get(case.id).reproduction
