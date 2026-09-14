"""Rebuild this walkthrough from frozen evidence, without API calls or new experiments."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1] / "evidence/overnight-2026-09-15/md-12620-terra-overnight-02"
case = json.loads((PACKAGE / "result.json").read_text())
events = [json.loads(line) for line in (PACKAGE / "events.jsonl").read_text().splitlines()]
artifacts = json.loads((PACKAGE / "artifacts.json").read_text())
labels = case["reproduction"]["oracle"]["checkpoints"]
assert len(labels) == 8
assert len(case["checks"]) == 5 and all(check["status"] == "pass" for check in case["checks"])


def recording(phase, selection):
    groups, actions = [], []
    for event in events:
        data = event["data"]
        if event["kind"] == "action" and data.get("phase") == phase:
            actions.append(event)
        if event["kind"] == "replay" and data.get("phase") == phase:
            groups.append((actions, event))
            actions = []
    actions, verdict = groups[selection]
    assert [event["data"]["action"] for event in actions] == case["reproduction"]["steps"]
    selected = [event for event in actions if event["data"]["action"]["checkpoint"] in labels]
    assert [event["data"]["action"]["checkpoint"] for event in selected] == labels
    frames = []
    for event in selected:
        artifact = "artifacts/" + event["data"]["screenshot_after"]
        metadata = artifacts[artifact]
        assert hashlib.sha256((PACKAGE / artifact).read_bytes()).hexdigest() == metadata["sha256"]
        frames.append(
            {
                "label": event["data"]["action"]["checkpoint"],
                "event_seq": event["seq"],
                "recorded_at": event["created_at"],
                "sha256": metadata["sha256"],
                "url": "../../evidence/overnight-2026-09-15/" + PACKAGE.name + "/" + artifact,
            }
        )
    return {
        "phase": phase,
        "replay_event_seq": verdict["seq"],
        "recorded_verdict": verdict["data"]["verdict"],
        "frames": frames,
    }


data = {
    "case_id": case["case_id"],
    "commit": case["report"]["target_commit"],
    "model": "gpt-5.6-terra",
    "reasoning": "medium",
    "usage": case["usage"],
    "checks": case["checks"],
    "actions": len(case["reproduction"]["steps"]),
    "baseline": recording("reduced-confirmation", -1),
    "candidate": recording("post-patch", 0),
    "patch": (PACKAGE / "candidate.patch").read_text(),
    "patch_sha256": hashlib.sha256((PACKAGE / "candidate.patch").read_bytes()).hexdigest(),
    "note": "Eight selected recorded checkpoints from one baseline and one candidate replay. Intermediate actions are omitted. This is not real-time video or a new execution.",
}
assert data["baseline"]["recorded_verdict"]["observed"] is True
assert data["candidate"]["recorded_verdict"]["expected_state_reached"] is True
assert data["candidate"]["recorded_verdict"]["symptom_absent"] is True
serialized = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
(HERE / "recording.json").write_text(serialized)
(HERE / "recording.js").write_text("const recording = " + serialized.rstrip() + ";\n")
print("Verified 30 matching actions and 16 screenshot hashes; wrote the recorded walkthrough data.")
