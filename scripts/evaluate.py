"""Evaluator-only result export. It never feeds ground truth back into the agent."""

import argparse
import json
from pathlib import Path

import yaml

from repro.config import Settings
from repro.storage.store import Store


def evaluate(case, manifest):
    ground_truth = set(manifest["evaluator"]["changed_files"])
    predictions = [c.path for c in case.findings.candidates] if case.findings else []
    ranks = [i + 1 for i, path in enumerate(predictions) if path in ground_truth]
    rep = case.reproduction
    return {
        "case_id": case.id,
        "benchmark_id": case.benchmark_id,
        "state": case.state,
        "summary": case.summary,
        "positive_case": manifest["evaluator"]["positive_case"],
        "reproduced": bool(rep and rep.deterministic),
        "successful_replays": rep.successful_runs if rep else 0,
        "total_replays": rep.total_runs if rep else 0,
        "original_actions": rep.original_actions if rep else None,
        "reduced_actions": len(rep.steps) if rep else None,
        "top1": bool(ranks and min(ranks) <= 1),
        "top3": bool(ranks and min(ranks) <= 3),
        "top5": bool(ranks and min(ranks) <= 5),
        "reciprocal_rank": 1 / min(ranks) if ranks else 0,
        "ground_truth_files": sorted(ground_truth),
        "predicted_files": predictions,
        "candidate_validated": bool(
            case.patch_artifact and case.checks and all(c.status == "pass" for c in case.checks)
        ),
        "checks": [c.model_dump() for c in case.checks],
        "usage": case.usage.model_dump(),
        "first_reproduced_seconds": case.first_reproduced_seconds,
        "elapsed_seconds": case.elapsed_seconds,
        "limitations": [
            "Selected visual case, not representative accuracy.",
            "Independent verifier uses the same model family as the investigator.",
            "Startup-only smoke coverage.",
            "Report platform and evaluation platform may differ.",
            "No negative-case calibration in this single-case result.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_id")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    store = Store(Settings().root)
    case = store.get(args.case_id)
    manifest = yaml.safe_load(args.manifest.read_text())
    if case.report.target_commit != manifest["input"]["target_commit"]:
        raise SystemExit("Refusing to score a different target revision")
    result = evaluate(case, manifest)
    result["artifacts"] = store.artifacts(case.id)
    result["state_history"] = [e for e in store.events(case.id) if e["kind"] == "state"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Exported evaluator result to {args.output}")


if __name__ == "__main__":
    main()
