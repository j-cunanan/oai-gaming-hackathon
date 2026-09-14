"""Rehydrate exported recordings; no investigation or inferred evidence is created."""

import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path

import yaml

from repro.models import Case, CaseInput, ImportedRecording, now
from repro.storage.store import Store


class EvidenceError(ValueError):
    """An invalid package or unsafe target; the existing store is left intact."""


def import_evidence(
    store: Store,
    directory: Path,
    case_id: str | None = None,
    force: bool = False,
    manifest: Path | None = None,
) -> Case:
    root = directory.resolve(strict=True)
    consumed: dict[str, bytes] = {}

    def read(name: str) -> bytes:
        path = (root / name).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():
            raise EvidenceError(f"Evidence path escapes package: {name}")
        if name not in consumed:
            consumed[name] = path.read_bytes()
        return consumed[name]

    def document(name: str):
        return json.loads(read(name))

    original = document("result.json")
    latest = (
        document("network-validation/result.json")
        if (root / "network-validation/result.json").exists()
        else original
    )
    original_id = original["case_id"]
    target = case_id or original_id
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", target):
        raise EvidenceError("Invalid case id")
    if latest["case_id"] != original_id:
        raise EvidenceError("Results refer to different original cases")
    benchmark = original.get("benchmark_id", root.name)
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", benchmark):
        raise EvidenceError("Invalid benchmark id")
    manifest = manifest or Path(__file__).resolve().parents[2] / "benchmarks/manifests" / (
        benchmark + ".yaml"
    )
    # Deliberately discard evaluator metadata before constructing or fingerprinting the case.
    report = CaseInput.model_validate(yaml.safe_load(manifest.read_text())["input"])
    artifacts = {}
    for folder in ("", "network-validation/"):
        index = folder + "artifacts.json"
        if not (root / index).exists():
            continue
        for name, metadata in document(index).items():
            raw = read(folder + name)
            digest = hashlib.sha256(raw).hexdigest()
            if digest != metadata["sha256"]:
                raise EvidenceError(f"SHA-256 mismatch: {folder + name}")
            artifact_id = metadata["artifact_id"]
            if not re.fullmatch(r"[a-zA-Z0-9_.-]+", artifact_id) or artifact_id in {".", ".."}:
                raise EvidenceError(f"Invalid artifact id: {artifact_id}")
            entry = (Path(name).name, digest, metadata["media_type"], raw)
            if artifact_id in artifacts and artifacts[artifact_id][1:] != entry[1:]:
                raise EvidenceError(f"Conflicting artifact id: {artifact_id}")
            artifacts.setdefault(artifact_id, entry)
    if not artifacts:
        raise EvidenceError("Package has no artifact checksum manifest")

    events_by_seq = {}
    for name in ("events.jsonl", "network-validation/events.jsonl"):
        if not (root / name).exists():
            continue
        for line in read(name).splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if (
                event["case_id"] != original_id
                or not isinstance(event["seq"], int)
                or event["seq"] < 1
                or not isinstance(event["data"], dict)
                or not isinstance(event["kind"], str)
            ):
                raise EvidenceError(f"Invalid event in {name}")
            previous = events_by_seq.get(event["seq"])
            if previous is not None and previous != event:
                raise EvidenceError(f"Conflicting recorded event sequence: {event['seq']}")
            events_by_seq[event["seq"]] = event
    events = [events_by_seq[seq] for seq in sorted(events_by_seq)]
    created_at = original.get("created_at") or (events[0]["created_at"] if events else None)
    updated_at = latest.get("updated_at") or (events[-1]["created_at"] if events else None)
    if not created_at or not updated_at:
        raise EvidenceError("Recording lacks case/event timestamps")
    values = {
        "id": target,
        "report": report,
        "benchmark_id": original.get("benchmark_id"),
        "created_at": created_at,
        "updated_at": updated_at,
        "state": latest["state"],
        "summary": latest.get("summary", ""),
    }
    # Copy only explicit snapshot fields. Rerun-only counters are not lifetime totals.
    for field in (
        "spec",
        "usage",
        "elapsed_seconds",
        "first_reproduced_seconds",
        "baseline_tests",
        "candidate_verification",
    ):
        if field in original:
            values[field] = original[field]
        if field in latest:
            values[field] = latest[field]
    for field in ("usage", "elapsed_seconds"):
        values.setdefault(field, None)
    hypotheses = {}
    for event in events:
        if event["kind"] == "hypothesis":
            hypotheses[event["data"]["id"]] = event["data"]
    values["hypotheses"] = list(hypotheses.values())
    for filename, field in (
        ("source-findings.json", "findings"),
        ("patch-rationale.json", "patch_rationale"),
    ):
        if (root / filename).exists():
            values[field] = document(filename)
    replay_name = (
        "network-validation/repro.yaml"
        if (root / "network-validation/repro.yaml").exists()
        else "repro.yaml"
    )
    if (root / replay_name).exists():
        values["reproduction"] = yaml.safe_load(read(replay_name))
    values["checks"] = latest.get("checks", [])
    # The original export omitted artifacts.json. Its patch id is in the audit,
    # and the subsequent result records the full SHA-256 of the unchanged patch.
    if (root / "candidate.patch").exists():
        raw = read("candidate.patch")
        digest = hashlib.sha256(raw).hexdigest()
        expected = latest.get("patch_unchanged_sha256")
        if expected and expected != digest:
            raise EvidenceError("SHA-256 mismatch: candidate.patch")
        patches = [e["data"]["artifact"] for e in events if e["kind"] == "patch"]
        patch_id = patches[-1] if patches else None
        if patch_id:
            if patch_id not in artifacts:
                if not expected or patch_id != f"{original_id}-{digest[:20]}-candidate.patch":
                    raise EvidenceError("Candidate patch has no matching recorded checksum/id")
                artifacts[patch_id] = ("candidate.patch", digest, "text/x-diff", raw)
            elif artifacts[patch_id][3] != raw:
                raise EvidenceError("Candidate patch conflicts with artifact manifest")
            values["patch_artifact"] = patch_id
    # Only select a screenshot whose actual bytes were exported and verified.
    for event in events:
        for field in ("screenshot_after", "screenshot", "screenshot_artifact"):
            artifact_id = event["data"].get(field)
            if artifact_id in artifacts and artifacts[artifact_id][2].startswith("image/"):
                values["latest_screenshot"] = artifact_id
    fingerprint = hashlib.sha256(report.model_dump_json().encode())
    for name, raw in sorted(consumed.items()):
        fingerprint.update(name.encode() + b"\0" + hashlib.sha256(raw).digest())
    values["imported_from"] = ImportedRecording(
        source_dir=str(root),
        imported_at=now(),
        original_case_id=original_id,
        package_sha256=fingerprint.hexdigest(),
    )
    case = Case.model_validate(values)
    _persist(store, case, artifacts, events, force)
    return store.get(target)


def _persist(store: Store, case: Case, artifacts: dict, events: list, force: bool):
    # Stage verified bytes before the transaction. Roll back the directory swap
    # on any database/write error; existing local cases and artifacts are never touched.
    with tempfile.TemporaryDirectory(prefix="evidence-", dir=store.root) as temporary:
        staging = Path(temporary) / "artifacts"
        staging.mkdir()
        for artifact_id, (_, _, _, raw) in artifacts.items():
            (staging / artifact_id).write_bytes(raw)
        destination = store.root / "cases" / case.id / "artifacts"
        backup = Path(temporary) / "previous"
        swapped = False
        try:
            with store.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT data FROM cases WHERE id=?", (case.id,)).fetchone()
                if row:
                    existing = Case.model_validate_json(row["data"])
                    if not existing.imported_from:
                        raise EvidenceError(f"Refusing to replace local case {case.id}; use --id")
                    if not force:
                        if (
                            existing.imported_from.package_sha256
                            == case.imported_from.package_sha256
                        ):
                            return
                        raise EvidenceError("Imported case differs; use --force to replace it")
                for artifact_id in artifacts:
                    owner = db.execute(
                        "SELECT case_id FROM artifacts WHERE id=?", (artifact_id,)
                    ).fetchone()
                    if owner and owner["case_id"] != case.id:
                        raise EvidenceError(f"Artifact id belongs to another case: {artifact_id}")
                db.execute("DELETE FROM events WHERE case_id=?", (case.id,))
                db.execute("DELETE FROM artifacts WHERE case_id=?", (case.id,))
                db.execute(
                    "INSERT OR REPLACE INTO cases VALUES (?,?)", (case.id, case.model_dump_json())
                )
                for artifact_id, (name, digest, media_type, raw) in artifacts.items():
                    db.execute(
                        "INSERT INTO artifacts VALUES (?,?,?,?,?,?)",
                        (artifact_id, case.id, name, digest, len(raw), media_type),
                    )
                for event in events:
                    db.execute(
                        "INSERT INTO events(case_id,created_at,kind,data,recorded_seq) "
                        "VALUES (?,?,?,?,?)",
                        (
                            case.id,
                            event["created_at"],
                            event["kind"],
                            json.dumps(event["data"]),
                            event["seq"],
                        ),
                    )
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    destination.rename(backup)
                staging.rename(destination)
                swapped = True
        except BaseException:
            if swapped:
                shutil.rmtree(destination)
            if backup.exists():
                backup.rename(destination)
            raise
