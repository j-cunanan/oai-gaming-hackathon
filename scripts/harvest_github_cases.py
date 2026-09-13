"""Preparation-only candidate harvester. Never run inside an investigation workspace."""

import argparse
import json
import re
import subprocess
from pathlib import Path

import yaml


def github(endpoint):
    return json.loads(subprocess.check_output(["gh", "api", endpoint], text=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=["mindustry", "luanti"], default="mindustry")
    parser.add_argument("--since", default="2026-05-01T00:00:00Z")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path(".repro/harvested"))
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error("limit must be between 1 and 50")
    repo = "Anuken/Mindustry" if args.game == "mindustry" else "luanti-org/luanti"
    commits = github(f"repos/{repo}/commits?since={args.since}&per_page=100")
    args.output.mkdir(parents=True, exist_ok=True)
    count, seen = 0, set()
    for commit in commits:
        match = re.search(
            r"\b(?:fix(?:ed|es)?|close[sd]?)\s+#(\d+)", commit["commit"]["message"], re.I
        )
        if not match or match[1] in seen:
            continue
        seen.add(match[1])
        issue = github(f"repos/{repo}/issues/{match[1]}")
        if issue.get("pull_request") or issue["state"] != "closed":
            continue
        fix = github(f"repos/{repo}/commits/{commit['sha']}")
        if len(fix["parents"]) != 1:
            continue
        source_files = [
            f["filename"]
            for f in fix["files"]
            if Path(f["filename"]).suffix in {".java", ".cpp", ".h", ".cc", ".c", ".lua"}
        ]
        if not source_files:
            continue
        case_id = f"{'MD' if args.game == 'mindustry' else 'LU'}-candidate-{match[1]}"
        data = {
            "id": case_id,
            "input": {
                "title": issue["title"],
                "body": issue["body"] or "Report body unavailable; collect original evidence.",
                "game": args.game,
                "target_commit": fix["parents"][0]["sha"],
                "platform": "Unverified",
            },
            "evaluator": {
                "issue_url": issue["html_url"],
                "reported_at": issue["created_at"],
                "fix_commit": fix["sha"],
                "changed_files": source_files,
                "positive_case": True,
                "reproducibility": "UNVERIFIED",
                "evidence_notes": "Fetched current issue body; may contain later edits. No comments fetched. Review original evidence and desktop compatibility before use.",
            },
        }
        (args.output / f"{case_id}.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
        print(f"{case_id}: candidate manifest saved (not a reproduced or scored case)")
        count += 1
        if count >= args.limit:
            break
    print(f"Saved {count} candidate manifests. Human dataset review is still required.")


if __name__ == "__main__":
    main()
