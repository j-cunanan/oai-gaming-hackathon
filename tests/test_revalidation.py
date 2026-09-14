from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import (
    Action,
    Case,
    CaseInput,
    Check,
    OracleSpec,
    Reproduction,
    State,
    Verdict,
    patch_validated,
)
from repro.orchestration.manager import Manager
from repro.storage.store import Store


def example_case():
    return Case(
        report=CaseInput(
            title="Duplicate controls",
            body="Two Weather buttons are visible.",
            target_commit="a" * 40,
        ),
        patch_artifact="candidate.patch",
        checks=[Check(name="Regression before patch", status="pass", detail="Old run")],
        reproduction=Reproduction(
            game="mindustry",
            commit="a" * 40,
            steps=[Action(action="wait")],
            oracle=OracleSpec(kind="visual", description="Duplicate buttons"),
            deterministic=True,
            successful_runs=5,
            total_runs=5,
        ),
    )


@pytest.mark.parametrize("observed", [True, False])
async def test_revalidation_replaces_old_baseline_gate_with_fresh_evidence(
    tmp_path, monkeypatch, observed
):
    settings = Settings(_env_file=None, data_dir=tmp_path, repetitions=2)
    store = Store(tmp_path)
    case = example_case()
    store.save(case)
    sandbox = SimpleNamespace(use_baseline=False, stop=AsyncMock())
    model = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr("repro.orchestration.manager.DockerSandbox", lambda *args: sandbox)
    monkeypatch.setattr("repro.orchestration.manager.Model", lambda *args: model)
    monkeypatch.setattr("repro.orchestration.manager.Recorder", lambda *args: None)

    async def replay(worker, *args, **kwargs):
        assert worker.use_baseline
        return Verdict(
            observed=observed, confidence=1, explanation="Fresh result", evidence=["fresh.png"]
        ), {}

    async def candidate_checks(case, worker, *args):
        assert not worker.use_baseline
        case.checks.extend(
            Check(name=name, status="pass", detail="Candidate check")
            for name in (
                "Candidate build",
                "Existing tests",
                "Original replay after patch",
                "Smoke test",
            )
        )

    monkeypatch.setattr("repro.orchestration.manager.replay", replay)
    manager = Manager(settings, store)
    monkeypatch.setattr(manager, "validate", candidate_checks)
    await manager.validate_case(case)
    assert case.state == State.AWAITING_HUMAN
    assert case.reproduction.total_runs == 2
    assert case.reproduction.successful_runs == (2 if observed else 0)
    assert case.reproduction.evidence == ["fresh.png", "fresh.png"]
    assert patch_validated(case) is observed
    assert len(case.checks) == 5
    snapshot = next(
        a for a in store.artifacts(case.id) if a["name"] == "validation-before-rerun.json"
    )
    path, _ = store.artifact_path(case.id, snapshot["id"])
    assert Case.model_validate_json(path.read_text()).checks[0].detail == "Old run"


@pytest.mark.parametrize("crashed", [True, False])
async def test_launch_waits_for_ready_marker_or_returns_crash_evidence(
    tmp_path, monkeypatch, crashed
):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    sandbox = DockerSandbox(settings, Store(tmp_path), example_case())
    loading = {"process": {"running": True}, "logs": "Loading assets"}
    ready = {"process": {"running": True}, "logs": "Total time to load: 9100ms"}
    exited = {"process": {"running": False, "exit_code": 1}, "logs": "Startup crash"}
    sandbox.rpc = AsyncMock()
    sandbox.observe = AsyncMock(
        side_effect=[loading, exited] if crashed else [loading, ready, ready]
    )
    monkeypatch.setattr("repro.computer.sandbox.asyncio.sleep", AsyncMock())
    result = await sandbox.launch()
    assert result == (exited if crashed else ready)
    assert sandbox.observe.await_count >= 2
    assert sandbox.rpc.call_args.args[0] == "launch"
