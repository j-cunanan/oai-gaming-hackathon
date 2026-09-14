"""Build an explicitly operator-prepared scene with a retained historical game JAR."""

import argparse
import asyncio
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from repro.github.history import audit_history


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace", type=Path, required=True, help="Prepared REPRO game workspace"
    )
    parser.add_argument("--commit", required=True, help="Exact pre-fix game revision")
    parser.add_argument("--scene", choices=("generator", "unit"), required=True)
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--image", default="repro-worker:local")
    args = parser.parse_args()
    root = args.workspace.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        parser.error(
            "Output already exists; keep earlier construction records and choose a new directory"
        )
    if json.loads((root / "prepared.json").read_text())["commit"] != args.commit:
        parser.error("Prepared workspace revision differs from --commit")
    asyncio.run(audit_history(root / "repo", args.commit))
    changes = subprocess.check_output(["git", "-C", str(root / "repo"), "status", "--porcelain"])
    if changes.strip():
        parser.error("Use an unchanged historical source workspace")
    backends = sorted((root / "gradle/caches").rglob("backend-headless-*.jar"))
    if len(backends) != 1:
        parser.error("Expected one prepared Arc headless backend; use a fresh prepared workspace")
    backend = backends[0]
    game = root / "baseline/Mindustry.jar"
    java = Path(__file__).parent / "fixtures/OperatorSceneBuilder.java"
    image = json.loads(subprocess.check_output(["docker", "image", "inspect", args.image]))[0]["Id"]
    provenance = {
        "origin": "operator_setup",
        "scene": args.scene,
        "game_commit": args.commit,
        "game_jar_sha256": digest(game),
        "headless_jar_sha256": digest(backend),
        "builder_source_sha256": digest(java),
        "worker_image_id": image,
        "worker_platform": "linux/amd64",
        "network": "none",
        "source_workspace_unchanged": True,
        "historical_source_isolation_verified": True,
        "symptom_tested": False,
    }
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="repro-fixture-construction-") as temporary:
        work = Path(temporary)
        shutil.copy2(java, work / java.name)
        (work / "classes").mkdir()
        configuration = {
            "classpath": "/game/baseline/Mindustry.jar:/game/" + str(backend.relative_to(root)),
            "scene": args.scene,
        }
        (work / "inputs.json").write_text(json.dumps(configuration))
        (work / "invoke.py").write_text(
            "import json, subprocess\n"
            "c = json.load(open('/work/inputs.json'))\n"
            "subprocess.run(['javac', '-cp', c['classpath'], '-d', '/work/classes', "
            "'/work/OperatorSceneBuilder.java'], check=True, timeout=45)\n"
            "subprocess.run(['java', '-cp', '/work/classes:' + c['classpath'], "
            "'OperatorSceneBuilder', c['scene'], '/work/output'], "
            "cwd='/game/repo/core/assets', check=True, timeout=90)\n"
        )
        command = [
            "docker",
            "run",
            "--rm",
            "--platform",
            "linux/amd64",
            "--network",
            "none",
            "--cpus",
            "2",
            "--memory",
            "2g",
            "--pids-limit",
            "256",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,size=256m",
            "--entrypoint",
            "python3",
            "-v",
            f"{root}:/game:ro",
            "-v",
            f"{work}:/work",
            image,
            "/work/invoke.py",
        ]
        with (output / "construction.log").open("w") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=150)
        if result.returncode:
            raise RuntimeError(f"Scene construction failed; inspect {output / 'construction.log'}")
        for path in (work / "output").iterdir():
            shutil.copy2(path, output / path.name)
    fixture = output / f"operator-{args.scene}-setup.msav"
    audit = json.loads((output / f"{args.scene}-setup-audit.json").read_text())
    if not audit["save_reload_preconditions_pass"] or audit["symptom_tested"]:
        raise RuntimeError("Expected a successful precondition audit without a symptom claim")
    provenance["fixture"] = {
        "filename": fixture.name,
        "bytes": fixture.stat().st_size,
        "sha256": digest(fixture),
    }
    provenance["preconditions"] = audit
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
