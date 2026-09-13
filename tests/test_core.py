import asyncio

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from repro.agents.openai import strict_schema
from repro.api import create_app
from repro.config import Settings
from repro.github.history import audit_history, isolate_history, isolate_snapshot
from repro.minimization.ddmin import minimize
from repro.models import REQUIRED_VALIDATION_GATES, Action, Case, CaseInput, Check, State
from repro.process import run
from repro.storage.store import Store


def report():
    return CaseInput(
        title="Missing game item",
        body="An item disappears when the player dies.",
        target_commit="a" * 40,
    )


def test_action_validation_and_strict_schema():
    with pytest.raises(ValidationError):
        Action(action="click", x=1280, y=4)
    with pytest.raises(ValidationError):
        Action(action="click")
    with pytest.raises(ValidationError):
        Action(action="keypress")
    schema = strict_schema(Action)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])


async def test_minimizer_removes_irrelevant_actions_and_respects_budget():
    trials = []

    async def reproduces(steps):
        trials.append(steps)
        return "load" in steps and "die" in steps and steps.index("load") < steps.index("die")

    reduced, count = await minimize(
        ["open", "load", "walk", "map", "die", "close"], reproduces, max_trials=30
    )
    assert reduced == ["load", "die"]
    assert count == len(trials)
    _, count = await minimize(
        list(range(30)), lambda _: asyncio.sleep(0, result=False), max_trials=3
    )
    assert count == 3


async def test_minimizer_handles_startup_bug_without_actions():
    reduced, _ = await minimize(["wait"], lambda _: asyncio.sleep(0, result=True))
    assert reduced == []


def test_store_events_and_artifact_access(tmp_path):
    store = Store(tmp_path)
    a, b = Case(report=report()), Case(report=report())
    store.save(a, "received")
    store.save(b, "received")
    store.transition(a, State.READY, "Ready")
    events = store.events(a.id)
    assert [e["kind"] for e in events] == ["received", "state"]
    assert store.events(a.id, events[0]["seq"])[0]["seq"] == events[1]["seq"]
    assert store.latest_events(a.id, 1)[0]["seq"] == events[1]["seq"]
    artifact = store.artifact(a.id, "../../evidence.txt", "original")
    path, _ = store.artifact_path(a.id, artifact)
    assert path.is_relative_to(store.workspace(a.id))
    assert path.read_text() == "original"
    with pytest.raises(KeyError):
        store.artifact_path(b.id, artifact)
    with pytest.raises(ValueError):
        store.workspace("../../escape")


async def test_history_export_has_no_future_objects_or_remote(tmp_path):
    source = tmp_path / "upstream"
    await run(["git", "init", str(source)])
    await run(["git", "-C", str(source), "config", "user.email", "tests@localhost"])
    await run(["git", "-C", str(source), "config", "user.name", "Test"])
    (source / "game.txt").write_text("buggy")
    await run(["git", "-C", str(source), "add", "."])
    await run(["git", "-C", str(source), "commit", "-m", "pre-fix"])
    _, before = await run(["git", "-C", str(source), "rev-parse", "HEAD"])
    (source / "game.txt").write_text("secret future solution")
    await run(["git", "-C", str(source), "commit", "-am", "future fix"])
    _, after = await run(["git", "-C", str(source), "rev-parse", "HEAD"])
    await run(["git", "-C", str(source), "tag", "future-fix"])
    for mode in ("bundle", "snapshot"):
        dest = tmp_path / mode
        if mode == "bundle":
            await isolate_history(source, before.strip(), dest)
        else:
            await isolate_snapshot(source.as_uri(), before.strip(), dest)
        assert (dest / "game.txt").read_text() == "buggy"
        assert (await audit_history(dest, before.strip()))["isolated"]
        code, _ = await run(["git", "-C", str(dest), "cat-file", "-e", after.strip()], check=False)
        assert code != 0
        _, refs = await run(["git", "-C", str(dest), "show-ref"], check=False)
        assert "future-fix" not in refs


def test_api_missing_ai_and_review_validation(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, OPENAI_API_KEY="")
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.post("/api/cases", json=report().model_dump())
        assert response.status_code == 201
        case_id = response.json()["id"]
        assert client.post(f"/api/cases/{case_id}/investigate").status_code == 503
        assert client.post(f"/api/cases/{case_id}/approve").status_code == 409
        case = app.state.store.get(case_id)
        case.state = State.AWAITING_HUMAN
        case.patch_artifact = "candidate.patch"
        case.checks = [
            Check(
                name="Regression before patch", status="pass", detail="Expected failure confirmed"
            )
        ]
        case.benchmark_id = "MD-test"
        app.state.store.save(case)
        assert client.post(f"/api/cases/{case_id}/approve").status_code == 409
        assert client.get("/api/benchmarks").json()["validated_patches"] == 0
        case.checks = [Check(name="Replay", status="fail", detail="Still broken")]
        app.state.store.save(case)
        assert client.post(f"/api/cases/{case_id}/approve").status_code == 409
        case.checks = [
            Check(name=name, status="pass", detail="Verified") for name in REQUIRED_VALIDATION_GATES
        ]
        app.state.store.save(case)
        assert client.get("/api/benchmarks").json()["validated_patches"] == 1
        assert client.post(f"/api/cases/{case_id}/approve").status_code == 200
        assert "openai_api_key" not in client.get("/api/health").text
        assert (
            client.post(
                "/api/cases", json=report().model_dump(), headers={"Origin": "https://evil.example"}
            ).status_code
            == 403
        )


def test_api_artifacts_scoped_and_restart_recorded(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, OPENAI_API_KEY="")
    store = Store(tmp_path)
    a, b = Case(report=report(), state=State.INVESTIGATING), Case(report=report())
    store.save(a)
    store.save(b)
    artifact = store.artifact(a.id, "screen.txt", "private case evidence")
    with TestClient(create_app(settings)) as client:
        assert client.get(f"/api/cases/{a.id}").json()["state"] == "FAILED"
        assert client.get(f"/api/cases/{b.id}/artifacts/{artifact}").status_code == 404
        assert client.get(f"/api/cases/{a.id}/artifacts/{artifact}").text == "private case evidence"
        assert client.get("/api/cases/missing/stream").status_code == 404


async def test_subprocess_timeout_stops_work():
    with pytest.raises(TimeoutError):
        await run(["python3", "-c", "import time; time.sleep(20)"], timeout=0.05)
