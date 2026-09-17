"""Apply REPRO's existing ordered-image verifier to fresh 3D replays.

Neither evaluator state nor the investigator's conclusion is sent to this pass.
Every checkpoint in a verdict comes from the same fresh replay and variant.
"""

import argparse
import asyncio
import base64
import hashlib
import json
import time
from pathlib import Path

from openai import AsyncOpenAI

from repro.agents.oracle import verify_sequence
from repro.config import Settings
from repro.models import Action, OracleSpec
from scripts.three_d_probe.run import write_json
from scripts.three_d_probe.scene import Scene, World


class ProbeVerifier:
    """A small structured-call interface for the shared production verifier."""

    def __init__(self, client, model):
        self.client, self.model = client, model
        self.requests = []

    async def structured(self, schema, prompt, *, purpose, screenshots):
        content = [{"type": "input_text", "text": prompt}]
        for label, encoded in screenshots:
            content.extend(
                [
                    {"type": "input_text", "text": label},
                    {
                        "type": "input_image",
                        "image_url": "data:image/png;base64," + encoded,
                        "detail": "original",
                    },
                ]
            )
        started = time.monotonic()
        response = await self.client.responses.parse(
            model=self.model,
            store=False,
            reasoning={"effort": "low"},
            max_output_tokens=1800,
            input=[{"role": "user", "content": content}],
            text_format=schema,
        )
        self.requests.append(
            {
                "response_id": response.id,
                "model": response.model,
                "purpose": purpose,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "usage": response.usage.model_dump() if response.usage else None,
            }
        )
        if response.status != "completed" or response.output_parsed is None:
            raise RuntimeError("Verifier did not return a complete structured verdict")
        return response.output_parsed


async def verify_runs(root, model):
    settings = Settings()
    scene = Scene()
    try:
        async with AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(), timeout=60, max_retries=0
        ) as client:
            verifier = ProbeVerifier(client, model)
            for run in sorted(root.glob("run-*")):
                summary = json.loads((run / "summary.json").read_text())
                if not summary["observed_by_private_evaluator"]:
                    continue
                actions = [
                    Action.model_validate(a) for a in json.loads((run / "actions.json").read_text())
                ]
                proofs = []
                for fixed in (False, True):
                    world = World(
                        x=summary["initial_state"]["x"], heading=summary["initial_state"]["heading"]
                    )
                    prefix = "reference-proof" if fixed else "buggy-proof"
                    observations = []
                    for index, action in enumerate(actions, 1):
                        world.apply(action, fixed=fixed)
                        path = run / f"{prefix}-{index:03d}.png"
                        scene.capture(world, path)
                        observations.append(
                            {
                                "index": index,
                                "action": action.model_dump(),
                                "observation": {
                                    "process": {"running": True},
                                    "screenshot": base64.b64encode(path.read_bytes()).decode(),
                                    "screenshot_artifact": path.name,
                                },
                                "world": world.snapshot(),
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            }
                        )
                    # Select the adjacent before/after collection frames, then save and reload.
                    collected = next(
                        i for i, frame in enumerate(observations) if frame["world"]["collected"]
                    )
                    saved = next(
                        i
                        for i, frame in enumerate(observations)
                        if i >= collected and "f5" in frame["action"]["keys"]
                    )
                    reloaded = next(
                        i
                        for i, frame in enumerate(observations)
                        if i > saved and "f9" in frame["action"]["keys"]
                    )
                    selected = [
                        observations[i] for i in (collected - 1, collected, saved, reloaded)
                    ]
                    labels = ["A", "B", "C", "D"]
                    oracle = OracleSpec(
                        kind="sequence",
                        checkpoints=labels,
                        description="The blue crystal is collected and disappears while inventory becomes 1. The room is saved and reloaded. The reported defect is that the crystal returns in the world while inventory still contains the collected crystal. Correct behavior is for the crystal to remain absent after reload, with inventory 1.",
                    )
                    checkpoints = {
                        label: {key: frame[key] for key in ("index", "action", "observation")}
                        for label, frame in zip(labels, selected, strict=True)
                    }
                    verdict = await verify_sequence(
                        verifier, oracle, selected[-1]["observation"], checkpoints, actions
                    )
                    proof = {
                        "variant": "human-authored reference correction" if fixed else "seeded bug",
                        "verdict": verdict.model_dump(),
                        "checkpoints": [
                            {
                                "label": label,
                                "action_index": frame["index"],
                                "image": frame["observation"]["screenshot_artifact"],
                                "sha256": frame["sha256"],
                            }
                            for label, frame in zip(labels, selected, strict=True)
                        ],
                        "request": verifier.requests[-1],
                        "source": "repro.agents.oracle.verify_sequence",
                        "evaluator_state_supplied": False,
                        "investigator_conclusion_supplied": False,
                    }
                    proofs.append(proof)
                    write_json(run / "verification.json", proofs)
                    print(
                        json.dumps(
                            {
                                "run": run.name,
                                "variant": proof["variant"],
                                "verdict": proof["verdict"],
                            }
                        ),
                        flush=True,
                    )
    finally:
        scene.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--model", default="gpt-6-astra")
    args = parser.parse_args()
    asyncio.run(verify_runs(args.root, args.model))
