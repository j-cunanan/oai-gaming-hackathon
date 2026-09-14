"""Freeze existing color-candidate test outputs and build identities; do not run new tests."""
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from repro.config import Settings
from repro.models import ACTIVE_STATES
from repro.storage.store import Store

store = Store(Settings().root)
case = store.get("md-12623-terra-replay-02")
assert case.state not in ACTIVE_STATES
root = Path("/tmp/repro-oai-gaming-workspaces") / case.id
out = Path("docs/evidence/overnight-2026-09-15/color-candidate-audit")
assert not out.exists()
out.mkdir()
hash_bytes = lambda raw: hashlib.sha256(raw).hexdigest()
checks = {check.name: check for check in case.checks}
assert checks["Existing tests"].status == "pass"
test_log, _ = store.artifact_path(case.id, checks["Existing tests"].artifact)
patch, _ = store.artifact_path(case.id, case.patch_artifact)
result = {
    "scope": __doc__,
    "captured_at": datetime.now(timezone.utc).isoformat(),
    "source_case_id": case.id,
    "target_commit": case.reproduction.commit,
    "candidate_patch_sha256": hash_bytes(patch.read_bytes()),
    "candidate_tests_log_artifact": checks["Existing tests"].artifact,
    "candidate_tests_log_sha256": hash_bytes(test_log.read_bytes()),
    "driver_sha256": hash_bytes(Path(__file__).read_bytes()),
    "counts": {key: 0 for key in ("tests", "failures", "errors", "skipped")},
    "suites": [],
    "builds": {},
}
for path in sorted((root / "repo/tests/build/test-results/test").glob("TEST-*.xml")):
    suite = ET.parse(path).getroot()
    item = {key: int(suite.get(key, "0")) for key in result["counts"]}
    for key, count in item.items():
        result["counts"][key] += count
    item.update(name=suite.get("name"), file=path.name, timestamp=suite.get("timestamp"),
                mtime_utc=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat())
    result["suites"].append(item)
    shutil.copy2(path, out / path.name)
assert len(result["suites"]) == 8
for label, path in {
    "baseline": root / "baseline/Mindustry.jar",
    "candidate": root / "repo/desktop/build/libs/Mindustry.jar",
}.items():
    with zipfile.ZipFile(path) as jar:
        classes = {name: hash_bytes(jar.read(name)) for name in jar.namelist()
                   if name.startswith("mindustry/ui/dialogs/ColorPicker") and name.endswith(".class")}
    result["builds"][label] = {"jar_sha256": hash_bytes(path.read_bytes()),
                               "jar_bytes": path.stat().st_size, "color_picker_classes": classes}
assert result["builds"]["baseline"] != result["builds"]["candidate"]
shutil.copy2(Path(__file__), out / "audit_driver.py")
result["files"] = {path.name: hash_bytes(path.read_bytes()) for path in sorted(out.iterdir())}
(out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"counts": result["counts"], "builds": result["builds"]}, indent=2))
