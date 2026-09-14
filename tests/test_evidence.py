import hashlib
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from repro.activity import activity_snapshot
from repro.api import create_app
from repro.cli import app
from repro.config import Settings
from repro.models import Case, CaseInput, patch_validated
from repro.storage.evidence import EvidenceError, import_evidence
from repro.storage.store import Store

PACKAGE = Path(__file__).resolve().parents[1] / "docs/evidence/MD-001"


@pytest.fixture
def package(tmp_path):
    return Path(shutil.copytree(PACKAGE, tmp_path / "MD-001"))


def records(store, case_id):
    with store.connect() as db:
        return [
            dict(r)
            for r in db.execute("SELECT * FROM events WHERE case_id=? ORDER BY seq", (case_id,))
        ]


def test_clean_import_and_provenance_api_roundtrip(tmp_path):
    store = Store(tmp_path / "store")
    case = import_evidence(store, PACKAGE)
    assert case.id == "md-weather-terra-001"
    assert case.state == "AWAITING_HUMAN"
    assert patch_validated(case)
    assert len(case.reproduction.steps) == 8
    assert case.reproduction.original_actions == 23
    assert case.reproduction.successful_runs == case.reproduction.total_runs == 5
    assert case.findings.candidates[0].path.endswith("CustomRulesDialog.java")
    assert case.hypotheses[0].status == "supported"
    assert case.spec is None  # No structured triage response in the export.
    assert case.usage.model_calls == 84  # Recorded total; no invented rerun aggregate.
    assert case.imported_from.original_case_id == case.id
    assert case.created_at == "2026-09-13T16:40:24.411169+00:00"
    assert case.updated_at == "2026-09-14T04:52:05.416017+00:00"
    assert store.get(case.id) == case
    assert "ground_truth_files" not in case.model_dump_json()
    assert "60cc6a18392c25c241f7835fb104f16c1d475a1b" not in case.model_dump_json()
    assert (
        store.artifact_path(case.id, case.patch_artifact)[0].read_bytes()
        == (PACKAGE / "candidate.patch").read_bytes()
    )
    assert (
        store.artifact_path(case.id, case.latest_screenshot)[0].read_bytes()
        == (PACKAGE / "network-validation/after.png").read_bytes()
    )
    for artifact in store.artifacts(case.id):
        raw = store.artifact_path(case.id, artifact["id"])[0].read_bytes()
        assert hashlib.sha256(raw).hexdigest() == artifact["sha256"]
    settings = Settings(_env_file=None, data_dir=store.root, OPENAI_API_KEY="")
    with TestClient(create_app(settings)) as client:
        detail = client.get(f"/api/cases/{case.id}").json()
        assert detail["imported_from"] == case.imported_from.model_dump()
        assert client.get("/api/cases").json()[0]["imported_from"] == detail["imported_from"]
        assert client.post(f"/api/cases/{case.id}/validate").status_code == 409
        assert client.post(f"/api/cases/{case.id}/approve").status_code == 409


@pytest.mark.parametrize("name", ["network-validation/before.png", "candidate.patch"])
def test_corruption_aborts_without_partial_writes(tmp_path, package, name):
    store = Store(tmp_path / "store")
    (package / name).write_bytes((package / name).read_bytes() + b"!")
    with pytest.raises(EvidenceError, match="SHA-256 mismatch"):
        import_evidence(store, package)
    assert store.list() == []
    assert not (store.root / "cases").exists()


def test_idempotence_and_force_replace(tmp_path, package):
    store = Store(tmp_path / "store")
    case = import_evidence(store, package)
    before = records(store, case.id)
    assert import_evidence(store, package) == case
    assert records(store, case.id) == before
    result = package / "network-validation/result.json"
    data = json.loads(result.read_text())
    data["summary"] = "Recorded summary correction"
    result.write_text(json.dumps(data))
    with pytest.raises(EvidenceError, match="--force"):
        import_evidence(store, package)
    assert store.get(case.id) == case
    replaced = import_evidence(store, package, force=True)
    assert replaced.summary == data["summary"]
    assert len(records(store, case.id)) == len(before)
    assert len(store.artifacts(case.id)) == 10
    assert len(list((store.workspace(case.id) / "artifacts").iterdir())) == 10
    # Verify before even an idempotent/forced replacement.
    (package / "network-validation/before.png").write_bytes(b"bad")
    with pytest.raises(EvidenceError, match="SHA-256"):
        import_evidence(store, package, force=True)
    assert store.get(case.id) == replaced


def test_event_order_and_override_with_existing_local_sequences(tmp_path):
    store = Store(tmp_path / "store")
    local = Case(
        report=CaseInput(title="Local case", body="Actual local report", target_commit="a" * 40)
    )
    store.save(local, "received")
    local_events = records(store, local.id)
    case = import_evidence(store, PACKAGE, case_id="recording")
    expected = sorted(
        [
            json.loads(line)
            for path in (PACKAGE / "events.jsonl", PACKAGE / "network-validation/events.jsonl")
            for line in path.read_text().splitlines()
        ],
        key=lambda event: event["seq"],
    )
    actual = records(store, case.id)
    assert len(actual) == len(expected) == 738
    assert [e["recorded_seq"] for e in actual] == [e["seq"] for e in expected]
    assert [json.loads(e["data"]) for e in actual] == [e["data"] for e in expected]
    assert [e["created_at"] for e in actual] == [e["created_at"] for e in expected]
    assert records(store, local.id) == local_events
    activity = activity_snapshot(store, case.id)
    assert all(stage["event_count"] > 0 for stage in activity["stages"])
    assert any(e["artifacts"] for e in activity["events"])
    assert all(
        a["id"] in {a["id"] for a in store.artifacts(case.id)}
        for e in activity["events"]
        for a in e["artifacts"]
    )


def test_missing_optional_data_stays_empty(tmp_path, package):
    shutil.rmtree(package / "network-validation")
    for name in ("source-findings.json", "patch-rationale.json", "candidate.patch", "repro.yaml"):
        (package / name).unlink()
    result = json.loads((package / "result.json").read_text())
    for field in ("usage", "elapsed_seconds", "first_reproduced_seconds", "checks"):
        result.pop(field, None)
    (package / "result.json").write_text(json.dumps(result))
    (package / "events.jsonl").write_text(
        json.dumps(
            {
                "seq": 43,
                "case_id": result["case_id"],
                "created_at": "2026-09-13T16:40:24+00:00",
                "kind": "received",
                "data": {},
            }
        )
        + "\n"
    )
    raw = (package / "candidate-build.txt").read_bytes()
    (package / "artifacts.json").write_text(
        json.dumps(
            {
                "candidate-build.txt": {
                    "artifact_id": "recorded-build",
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "media_type": "text/plain",
                }
            }
        )
    )
    case = import_evidence(Store(tmp_path / "store"), package)
    assert case.hypotheses == case.checks == []
    assert case.spec is case.findings is case.reproduction is None
    assert case.patch_artifact is case.patch_rationale is case.latest_screenshot is None
    assert case.first_reproduced_seconds is None
    assert case.elapsed_seconds is None
    assert case.usage is None


def test_never_overwrites_local_case_or_other_artifacts(tmp_path):
    store = Store(tmp_path / "store")
    local = Case(
        id="md-weather-terra-001",
        report=CaseInput(
            title="Real local case", body="Actual local report", target_commit="a" * 40
        ),
    )
    store.save(local, "received")
    for force in (False, True):
        with pytest.raises(EvidenceError, match="Refusing to replace local"):
            import_evidence(store, PACKAGE, force=force)
    assert store.get(local.id) == local
    store.artifact(local.id, "candidate.patch", (PACKAGE / "candidate.patch").read_bytes())
    with pytest.raises(EvidenceError, match="belongs to another case"):
        import_evidence(store, PACKAGE, case_id="recording")
    assert len(store.list()) == 1


def test_cli(tmp_path, monkeypatch):
    monkeypatch.setenv("REPRO_DATA_DIR", str(tmp_path / "store"))
    result = CliRunner().invoke(app, ["import-evidence", str(PACKAGE), "--id", "recording"])
    assert result.exit_code == 0, result.output
    assert "Imported recording: recording" in result.output
    assert "8 replay steps" in result.output


def test_failed_directory_swap_restores_previous_import(tmp_path, package, monkeypatch):
    store = Store(tmp_path / "store")
    case = import_evidence(store, package)
    old_records = records(store, case.id)
    old_rename = Path.rename

    def fail_staging(path, target):
        if path.name == "artifacts" and path.parent.name.startswith("evidence-"):
            raise OSError("simulated write failure")
        return old_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_staging)
    with pytest.raises(OSError, match="simulated"):
        import_evidence(store, package, force=True)
    assert store.get(case.id) == case
    assert records(store, case.id) == old_records
    assert store.artifact_path(case.id, case.patch_artifact)[0].exists()


def test_conflicting_event_and_escaping_manifest_path_fail(tmp_path, package):
    store = Store(tmp_path / "store")
    stream = package / "network-validation/events.jsonl"
    event = json.loads((package / "events.jsonl").read_text().splitlines()[0])
    event["data"] = {"summary": "conflict"}
    stream.write_text(stream.read_text() + json.dumps(event) + "\n")
    with pytest.raises(EvidenceError, match="Conflicting recorded event"):
        import_evidence(store, package)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside")
    (package / "artifacts.json").write_text(
        json.dumps(
            {
                "../outside.txt": {
                    "artifact_id": "outside",
                    "sha256": hashlib.sha256(b"outside").hexdigest(),
                    "media_type": "text/plain",
                }
            }
        )
    )
    with pytest.raises(EvidenceError, match="escapes package"):
        import_evidence(store, package)
    assert store.list() == []
