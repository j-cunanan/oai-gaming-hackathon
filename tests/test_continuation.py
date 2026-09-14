import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from repro.api import create_app
from repro.config import Settings
from repro.models import (
    Action,
    BugSpec,
    Case,
    CaseInput,
    Check,
    ImportedRecording,
    OracleSpec,
    Reproduction,
    State,
    Verdict,
)
from repro.orchestration.manager import Manager, ReadSource, SearchSource
from repro.storage.store import Store


def confirmed_case():
    return Case(
        state=State.INSUFFICIENT_EVIDENCE,
        summary="Source analysis paused after its stage budget.",
        report=CaseInput(
            title="Save crashes",
            body="Saving a map with a dummy crashes the game.",
            target_commit="a" * 40,
        ),
        spec=BugSpec(
            summary="Save crashes",
            bug_class="crash",
            observed_behavior="Game exits while saving a dummy",
            expected_behavior="Map saves",
            known_preconditions=[],
            uncertain_conditions=[],
            reproduction_hints=[],
            required_artifacts=[],
            severity="high",
            confidence=1,
        ),
        reproduction=Reproduction(
            game="mindustry",
            commit="a" * 40,
            steps=[Action(action="keypress", keys=["s"])],
            oracle=OracleSpec(kind="crash", description="Save crashes", log_pattern="unitTeam"),
            deterministic=True,
            successful_runs=5,
            total_runs=5,
        ),
        checks=[Check(name="Regression before patch", status="pass", detail="Prior worker")],
    )


@pytest.mark.parametrize("observed", [True, False])
async def test_continuation_preserves_snapshot_and_only_advances_after_fresh_proof(
    tmp_path,
    monkeypatch,
    observed,
):
    settings = Settings(_env_file=None, data_dir=tmp_path, repetitions=2)
    store = Store(tmp_path)
    case = confirmed_case()
    store.save(case, "received")
    steps = list(case.reproduction.steps)
    sandbox = SimpleNamespace(
        use_baseline=False, baseline_source_is_clean=AsyncMock(), stop=AsyncMock()
    )
    model = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr("repro.orchestration.manager.DockerSandbox", lambda *a: sandbox)
    monkeypatch.setattr("repro.orchestration.manager.Model", lambda *a: model)
    monkeypatch.setattr("repro.orchestration.manager.Recorder", lambda *a: None)

    async def replay(worker, recorder, model, actions, oracle, **kwargs):
        assert worker.use_baseline and actions == steps
        assert kwargs["phase"] == "resume-baseline"
        return Verdict(
            observed=observed,
            confidence=1,
            explanation="Fresh worker evidence",
            evidence=["new.png"],
        ), {}

    monkeypatch.setattr("repro.orchestration.manager.replay", replay)
    manager = Manager(settings, store)
    manager.record_baseline_tests = AsyncMock()
    manager.finish_confirmed_case = AsyncMock()
    await manager.continue_case(case)
    sandbox.baseline_source_is_clean.assert_awaited_once()
    manager.record_baseline_tests.assert_awaited_once_with(case, sandbox)
    assert manager.finish_confirmed_case.await_count == int(observed)
    assert case.reproduction.steps == steps
    assert case.reproduction.total_runs == 2
    assert case.reproduction.successful_runs == (2 if observed else 0)
    assert case.reproduction.deterministic is observed
    if not observed:
        assert case.state == State.INSUFFICIENT_EVIDENCE and case.checks == []
    snapshot = next(
        a for a in store.artifacts(case.id) if a["name"] == "analysis-before-resume.json"
    )
    path, _ = store.artifact_path(case.id, snapshot["id"])
    prior = Case.model_validate_json(path.read_text())
    assert prior.reproduction.successful_runs == 5
    assert prior.checks[0].detail == "Prior worker"
    assert store.events(case.id)[0]["kind"] == "received"
    sandbox.stop.assert_awaited_once()
    model.close.assert_awaited_once()


@pytest.mark.parametrize("problem", ["unconfirmed", "candidate", "untriaged", "imported"])
async def test_continuation_guards_before_spending_on_a_model(tmp_path, monkeypatch, problem):
    case = confirmed_case()
    if problem == "unconfirmed":
        case.reproduction.deterministic = False
    elif problem == "candidate":
        case.patch_artifact = "candidate.patch"
    elif problem == "untriaged":
        case.spec = None
    else:
        case.imported_from = ImportedRecording(
            source_dir="recorded",
            original_case_id=case.id,
            package_sha256="a" * 64,
            imported_at="2026-09-14T16:00:00Z",
        )
    create_model = AsyncMock()
    monkeypatch.setattr("repro.orchestration.manager.Model", create_model)
    with pytest.raises(ValueError):
        await Manager(Settings(_env_file=None, data_dir=tmp_path), Store(tmp_path)).continue_case(
            case
        )
    create_model.assert_not_called()


def test_continuation_api_rejects_duplicate_jobs_and_existing_candidates(tmp_path):
    app = create_app(Settings(_env_file=None, data_dir=tmp_path, OPENAI_API_KEY="test-only"))
    case = confirmed_case()
    app.state.store.save(case)

    async def pending(_):
        await asyncio.Event().wait()

    app.state.manager.continue_case = pending
    with TestClient(app) as client:
        assert client.post(f"/api/cases/{case.id}/continue").status_code == 202
        assert client.post(f"/api/cases/{case.id}/continue").status_code == 409
        assert client.post(f"/api/cases/{case.id}/cancel").status_code == 200
        case.patch_artifact = "already-proposed.patch"
        app.state.store.save(case)
        assert client.post(f"/api/cases/{case.id}/continue").status_code == 409


async def test_source_tool_outputs_are_retained_as_inspectable_artifacts(tmp_path):
    case = confirmed_case()
    store = Store(tmp_path)
    sandbox = SimpleNamespace(
        case=case,
        read_source=AsyncMock(return_value="12: actual pre-fix source\n"),
        search=AsyncMock(return_value="Dummy.java:12: actual match\n"),
    )
    read, search = Manager(Settings(_env_file=None, data_dir=tmp_path), store).source_tools(sandbox)
    assert await read.handler(ReadSource(path="Dummy.java", start_line=12, line_count=1)) == {
        "source": "12: actual pre-fix source\n"
    }
    assert await search.handler(SearchSource(query="unitTeam")) == {
        "matches": "Dummy.java:12: actual match\n"
    }
    events = store.events(case.id)
    assert [e["kind"] for e in events] == ["source_read", "source_search"]
    for event, expected in zip(events, ["actual pre-fix source", "actual match"], strict=True):
        path, _ = store.artifact_path(case.id, event["data"]["artifact"])
        assert expected in path.read_text()
