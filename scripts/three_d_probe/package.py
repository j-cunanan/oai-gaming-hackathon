"""Freeze the recorded probe, source snapshot, viewer and file hashes."""

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path


def package(root: Path, output: Path):
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).parent
    runs = []
    labels = {
        "run-01": "Facing the partition",
        "run-02": "Facing 90° away",
        "run-03": "Offset position, −35° camera",
    }
    for run in sorted(root.glob("run-*")):
        summary = json.loads((run / "summary.json").read_text())
        verification = json.loads((run / "verification.json").read_text())
        destination = output / "runs" / run.name
        destination.mkdir(parents=True)
        for file in sorted(run.iterdir()):
            if file.suffix in {".png", ".json"}:
                shutil.copy2(file, destination / file.name)
        runs.append(
            {
                "id": run.name,
                "label": labels[run.name],
                "summary": summary,
                "verification": verification,
            }
        )
    shutil.copy2(root / "astra-3d-replay.mp4", output / "astra-3d-replay.mp4")
    shutil.copy2(source / "viewer.html", output / "index.html")
    shutil.copy2(source / "README.md", output / "README.md")
    (output / "source").mkdir()
    for name in ("scene.py", "run.py", "verify.py", "movie.py"):
        shutil.copy2(source / name, output / "source" / name)
    shutil.copy2(
        source.parents[1] / "repro" / "agents" / "oracle.py", output / "source" / "repro-oracle.py"
    )
    files = {
        str(file.relative_to(output)): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted(output.rglob("*"))
        if file.is_file()
    }
    manifest = {
        "version": 1,
        "recorded_at": datetime.now(UTC).isoformat(),
        "scope": "Synthetic 3D feasibility only. One seeded defect, three selected starts. Not included in real bug Impact totals.",
        "model": "gpt-6-astra",
        "control_calls": sum(r["summary"]["calls"] for r in runs),
        "verification_calls": sum(len(r["verification"]) for r in runs),
        "runs": runs,
        "files": files,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Packaged {len(runs)} trials and {len(files)} hashed files in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    package(args.root, args.output)
