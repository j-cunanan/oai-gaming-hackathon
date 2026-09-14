"""Compact, timestamped stage history derived from the durable event audit."""

import json

from repro.storage.store import Store

STAGES = ("triage", "reproduce", "reduce", "localize", "validate", "review")
STATE_STAGE = {
    "RECEIVED": "triage",
    "TRIAGED": "triage",
    "ENVIRONMENT_PREPARING": "reproduce",
    "READY": "reproduce",
    "INVESTIGATING": "reproduce",
    "REPRODUCED": "reproduce",
    "MINIMIZING": "reduce",
    "REPRO_CONFIRMED": "reduce",
    "LOCALIZING": "localize",
    "TEST_GENERATING": "localize",
    "PATCH_PROPOSING": "validate",
    "VALIDATING": "validate",
    "AWAITING_HUMAN": "review",
    "COMPLETE": "review",
}
PHASE_STAGE = {
    "investigation": "reproduce",
    "confirmation": "reproduce",
    "manual-baseline": "reproduce",
    "minimization": "reduce",
    "reduced-confirmation": "reduce",
    "post-patch": "validate",
    "baseline-revalidation": "validate",
    "manual-candidate": "validate",
}
PURPOSE_STAGE = {
    "triage": "triage",
    "game investigation": "reproduce",
    "source localization": "localize",
    "candidate patch": "validate",
    "semantic replay reduction": "reduce",
}
QUIET_KINDS = {"model_call", "observation"}


def stage_for(kind: str, data: dict, previous: str) -> str:
    if kind == "stage_started" and data.get("stage") in STAGES:
        return data["stage"]
    if kind in {"state", "received"}:
        # Failure/cancellation belongs to the stage that encountered it.
        return STATE_STAGE.get(data.get("state"), previous)
    if kind in {"action", "replay"}:
        return PHASE_STAGE.get(data.get("phase"), previous)
    if kind == "model_call":
        return PURPOSE_STAGE.get(data.get("purpose"), previous)
    return {
        "localization": "localize",
        "patch": "validate",
        "validation_replay": "validate",
        "validation_environment": "validate",
        "minimization": "reduce",
        "reduction_proposal": "reduce",
        "reduction_proposal_rejected": "reduce",
    }.get(kind, previous)


def event_summary(kind: str, data: dict) -> str:
    if kind == "action":
        action = data.get("action", {})
        return str(action.get("semantic") or action.get("action", "Game action"))
    if kind == "model_call":
        return (
            f"{data.get('purpose', 'Model call')} · {data.get('model', 'AI')} · "
            f"{data.get('input_tokens', 0):,} input / {data.get('output_tokens', 0):,} output tokens"
        )
    if kind == "hypothesis":
        return str(data.get("statement", "Hypothesis recorded"))
    if kind == "replay":
        verdict = data.get("verdict", {})
        outcome = "Symptom observed" if verdict.get("observed") else "Symptom not confirmed"
        return f"{outcome}. {verdict.get('explanation', '')}".strip()
    if kind == "minimization":
        return f"Replay reduced from {data.get('original')} to {data.get('reduced')} actions."
    if kind == "validation_replay":
        return (
            "Expected state reached; symptom absent."
            if data.get("fixed")
            else "Fix not established. " + str(data.get("expected", {}).get("explanation", ""))
        )
    if kind == "validation_environment":
        return f"{data.get('phase', 'Validation')}; network: {data.get('network', 'unspecified')}."
    for field in ("summary", "explanation", "root_cause", "reason", "log_delta"):
        if data.get(field):
            return str(data[field])
    return kind.replace("_", " ").capitalize()


def activity_snapshot(store: Store, case_id: str, after: int = 0) -> dict:
    """Return stage timestamps plus only new compact entries after the caller's cursor.

    First/last are event times, not invented job start/end times or active durations.
    Scan the full audit (not the 500-event SSE page) to retain earlier stages.
    """
    imported = store.get(case_id).imported_from is not None
    available_artifacts = {a["id"] for a in store.artifacts(case_id)} if imported else set()
    stages = {
        key: {
            "key": key,
            "label": key.capitalize(),
            "first_at": None,
            "last_at": None,
            "event_count": 0,
            "log_count": 0,
        }
        for key in STAGES
    }
    stage, last_seq, total = "triage", 0, 0
    entries = []
    with store.connect() as db:
        for row in db.execute(
            "SELECT seq, created_at, kind, data FROM events WHERE case_id=? ORDER BY seq",
            (case_id,),
        ):
            data = json.loads(row["data"])
            kind, timestamp = row["kind"], row["created_at"]
            stage = stage_for(kind, data, stage)
            info = stages[stage]
            info["first_at"] = info["first_at"] or timestamp
            info["last_at"] = timestamp
            info["event_count"] += 1
            info["log_count"] += kind not in QUIET_KINDS
            last_seq, total = row["seq"], total + 1
            if last_seq <= after:
                continue
            links = []
            for field, label in (
                ("screenshot_after", "Screenshot"),
                ("screenshot", "Screenshot"),
                ("screenshot_artifact", "Screenshot"),
                ("log_artifact", "Game log"),
                ("artifact", "Artifact"),
            ):
                artifact = data.get(field)
                if isinstance(artifact, str) and (
                    artifact in available_artifacts
                    if imported
                    else artifact.startswith(case_id + "-")
                ):
                    links.append({"id": artifact, "label": label})
            state = data.get("state", "")
            attention = (
                kind == "error"
                or state
                in {
                    "FAILED",
                    "CANCELLED",
                    "ENVIRONMENT_UNSUPPORTED",
                    "INSUFFICIENT_EVIDENCE",
                    "NOT_REPRODUCED",
                }
                or (kind == "validation_replay" and not data.get("fixed"))
            )
            entries.append(
                {
                    "seq": last_seq,
                    "created_at": timestamp,
                    "kind": kind,
                    "stage": stage,
                    "summary": event_summary(kind, data),
                    "artifacts": links,
                    "attention": attention,
                }
            )
    return {
        "case_id": case_id,
        "stages": list(stages.values()),
        "events": entries,
        "last_seq": last_seq,
        "total_events": total,
    }
