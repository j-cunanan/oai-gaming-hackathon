import json

from fastapi.testclient import TestClient

from repro.activity import activity_snapshot
from repro.api import create_app
from repro.config import Settings
from repro.models import Case, CaseInput
from repro.storage.store import Store


def saved_case(store):
    case = Case(
        report=CaseInput(
            title="Weather controls",
            body="Weather appears twice in the rules menu.",
            target_commit="a" * 40,
        )
    )
    store.save(case)
    return case


def insert(store, case, records):
    with store.connect() as db:
        db.executemany(
            "INSERT INTO events(case_id,created_at,kind,data) VALUES (?,?,?,?)",
            [
                (
                    case.id,
                    f"2026-09-13T16:{index // 60:02d}:{index % 60:02d}+00:00",
                    kind,
                    json.dumps(data),
                )
                for index, (kind, data) in enumerate(records)
            ],
        )


def test_stage_history_preserves_reruns_and_failure_context(tmp_path):
    store = Store(tmp_path)
    case = saved_case(store)
    insert(
        store,
        case,
        [
            ("received", {"state": "RECEIVED"}),
            ("state", {"state": "READY"}),
            ("model_call", {"purpose": "triage", "input_tokens": 2, "output_tokens": 3}),
            ("state", {"state": "TRIAGED"}),
            ("state", {"state": "INVESTIGATING"}),
            ("state", {"state": "MINIMIZING"}),
            ("action", {"phase": "reduced-confirmation", "action": {"semantic": "Search Weather"}}),
            ("state", {"state": "CANCELLED", "summary": "Reduction cancelled"}),
            ("state", {"state": "MINIMIZING"}),
            ("state", {"state": "VALIDATING"}),
            (
                "action",
                {"phase": "baseline-revalidation", "action": {"semantic": "Replay baseline"}},
            ),
            ("state", {"state": "FAILED", "summary": "Build failed"}),
            ("state", {"state": "VALIDATING"}),
            ("state", {"state": "AWAITING_HUMAN"}),
        ],
    )
    history = activity_snapshot(store, case.id)
    groups = {s["key"]: s for s in history["stages"]}
    assert groups["triage"]["first_at"] == "2026-09-13T16:00:00+00:00"
    assert groups["triage"]["last_at"] == "2026-09-13T16:00:03+00:00"
    assert groups["reduce"]["event_count"] == 4
    assert groups["localize"]["first_at"] is None
    assert history["events"][7]["stage"] == "reduce"
    assert history["events"][7]["attention"]
    assert history["events"][10]["stage"] == "validate"
    assert history["events"][11]["stage"] == "validate"
    assert history["events"][11]["attention"]
    assert history["events"][-1]["stage"] == "review"
    assert activity_snapshot(store, case.id, history["last_seq"])["events"] == []


def test_activity_keeps_early_stages_beyond_sse_page_and_scopes_raw_records(tmp_path):
    store = Store(tmp_path)
    case, other = saved_case(store), saved_case(store)
    insert(store, other, [("received", {"summary": "OTHER_CASE_PRIVATE"})])
    insert(
        store,
        case,
        [("stage_started", {"stage": "triage", "summary": "Starting report triage"})]
        + [
            (
                "action",
                {
                    "phase": "investigation",
                    "action": {"semantic": f"Step {i}"},
                    "screenshot_after": f"{case.id}-screen.png",
                    "log_artifact": f"{other.id}-private.log",
                },
            )
            for i in range(520)
        ],
    )
    settings = Settings(_env_file=None, data_dir=tmp_path, OPENAI_API_KEY="")
    with TestClient(create_app(settings)) as client:
        response = client.get(f"/api/cases/{case.id}/activity")
        history = response.json()
        assert history["total_events"] == 521
        assert history["events"][0]["summary"] == "Starting report triage"
        assert history["stages"][0]["event_count"] == 1
        assert "OTHER_CASE_PRIVATE" not in response.text
        assert len(history["events"][-1]["artifacts"]) == 1
        cursor = history["events"][-3]["seq"]
        delta = client.get(f"/api/cases/{case.id}/activity?after={cursor}").json()
        assert len(delta["events"]) == 2
        assert delta["stages"] == history["stages"]
        seq = history["events"][0]["seq"]
        assert client.get(f"/api/cases/{case.id}/events/{seq}").json()["data"]["stage"] == "triage"
        assert client.get(f"/api/cases/{other.id}/events/{seq}").status_code == 404
        assert client.get("/api/cases/missing/activity").status_code == 404
        assert client.get(f"/api/cases/{case.id}/activity?after=-1").status_code == 422
