"""Render a fresh animated replay of recorded model inputs; omit API waiting time."""

import argparse
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg

from repro.models import Action
from scripts.three_d_probe.scene import Scene, World


def render(run: Path, output: Path):
    summary = json.loads((run / "summary.json").read_text())
    initial = summary["initial_state"]
    world = World(x=initial["x"], heading=initial["heading"])
    scene = Scene()
    scene.title.setText("REPRO / ASTRA INPUT REPLAY / SYNTHETIC 3D")
    frame = run.parent / "movie-frame.png"
    process = subprocess.Popen(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-loglevel",
            "error",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "-r",
            "15",
            "-i",
            "pipe:0",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "20",
            "-movflags",
            "+faststart",
            str(output),
        ],
        stdin=subprocess.PIPE,
    )

    def capture(repeats=1):
        scene.capture(world, frame)
        data = frame.read_bytes()
        for _ in range(repeats):
            process.stdin.write(data)

    try:
        capture(15)
        for raw in json.loads((run / "actions.json").read_text()):
            action = Action.model_validate(raw)
            if action.action == "keypress" and not set(action.keys) & {"e", "f5", "f9"}:
                ticks = max(1, round((action.hold_seconds or 0.1) * 60))
                one_tick = action.model_copy(update={"hold_seconds": 1 / 60})
                for tick in range(ticks):
                    world.apply(one_tick, fixed=False)
                    if (tick + 1) % 4 == 0 or tick + 1 == ticks:
                        capture()
            else:
                world.apply(action, fixed=False)
                capture(20)
            capture(3)
        capture(30)
        assert world.reproduced, "Animated replay did not reach the recorded failure"
    finally:
        process.stdin.close()
        code = process.wait(timeout=60)
        scene.close()
    if code:
        raise RuntimeError(f"Video encoder exited with {code}")
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.run, args.output)
