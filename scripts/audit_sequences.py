"""Audit the current verifier on retained images; this does not rerun the game."""

import argparse
import asyncio
import base64
import hashlib
import json
from pathlib import Path

import yaml

from repro.agents.openai import Model
from repro.agents.oracle import verify
from repro.config import Settings
from repro.models import Action, Case, CaseInput, OracleSpec
from repro.storage.store import Store

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "12620": "A data patch deleted from a map returns after saving, leaving the editor, and reopening that same map. Correct behavior retains the deletion. Confirm a patch existed, was visibly deleted, and inspect the reopened map's patch list.",
    "12623": "The editor fails to preserve a manually entered RGB hex color after confirming and reopening the picker. Compare visible entered and readback RGB values for Colored Floor and Colored Wall. Appending opaque alpha ff is normal; changing RGB is the defect. Both pickers and their transitions must be demonstrated.",
}


async def audit(output: Path, *, include_trace: bool):
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose a new or empty output directory; prior audits are retained")
    output.mkdir(parents=True, exist_ok=True)
    settings = Settings(max_model_calls=6, reasoning_effort="low")
    store = Store(output / "store")
    rows, hashes, usage = [], {}, {}

    def read(path):
        raw = path.read_bytes()
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
        return raw

    def save():
        (output / "audit.json").write_text(
            json.dumps(
                {
                    "scope": "Current verifier judgments on retained evidence; no new game runs",
                    "model": settings.model,
                    "reasoning_effort": settings.reasoning_effort,
                    "include_input_trace": include_trace,
                    "rules": RULES,
                    "source_sha256": hashes,
                    "runs": rows,
                    "usage": usage,
                },
                indent=2,
            )
            + "\n"
        )

    async with asyncio.timeout(600):
        for issue, description in RULES.items():
            manifest = yaml.safe_load(
                read(ROOT / f"benchmarks/candidates/MD-candidate-{issue}.yaml")
            )
            case = Case(
                id=f"retained-audit-{issue}", report=CaseInput.model_validate(manifest["input"])
            )
            model = Model(settings, store, case)
            try:
                for role in ("baseline", "human-fixed"):
                    directory = ROOT / f"docs/evidence/qualification/{issue}"
                    data = json.loads(read(directory / f"{role}.json"))
                    events = [
                        json.loads(line)
                        for line in read(directory / f"{role}-events.jsonl").splitlines()
                        if line.strip()
                    ]
                    for run in data["runs"]:
                        checkpoints = {}
                        for index, frame in enumerate(run["frames"], 1):
                            artifact = frame["artifact"]
                            recorded = [
                                event["data"]
                                for event in events
                                if event["kind"] == "action"
                                and event["data"].get("screenshot_after") == artifact
                            ]
                            if not recorded:
                                raise ValueError(f"Missing action/process record for {artifact}")
                            observation = {
                                "screenshot": base64.b64encode(
                                    read(directory / "artifacts" / artifact)
                                ).decode(),
                                "screenshot_artifact": artifact,
                                "process": recorded[-1]["process"],
                            }
                            action = dict(recorded[-1]["action"])
                            action.pop("semantic", None)
                            checkpoints[f"checkpoint-{index}"] = {
                                "index": frame["step"],
                                "action": action,
                                "observation": observation,
                            }
                        oracle = OracleSpec(
                            kind="sequence", description=description, checkpoints=list(checkpoints)
                        )
                        verdict = await verify(
                            model,
                            oracle,
                            observation,
                            launched_ok=True,
                            checkpoints=checkpoints,
                            actions=[Action.model_validate(a) for a in data["steps"]]
                            if include_trace
                            else [],
                        )
                        matched = (
                            verdict.observed
                            if role == "baseline"
                            else not verdict.observed
                            and verdict.expected_state_reached
                            and verdict.symptom_absent
                        )
                        rows.append(
                            {
                                "issue": issue,
                                "source": f"docs/evidence/qualification/{issue}/{role}.json",
                                "recorded_trial": run["trial"],
                                "expected": "symptom observed"
                                if role == "baseline"
                                else "correct behavior demonstrated",
                                "matched": matched,
                                "verdict": verdict.model_dump(),
                            }
                        )
                        usage[case.id] = case.usage.model_dump()
                        save()
                        print(f"{issue} {role} trial {run['trial']}: matched={matched}", flush=True)
            finally:
                usage[case.id] = case.usage.model_dump()
                save()
                await model.close()
    print(f"Agreement: {sum(row['matched'] for row in rows)}/{len(rows)} retained recordings")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="A new audit directory")
    parser.add_argument(
        "--without-trace", action="store_true", help="Omit intervening input actions"
    )
    args = parser.parse_args()
    asyncio.run(audit(args.output.resolve(), include_trace=not args.without_trace))
