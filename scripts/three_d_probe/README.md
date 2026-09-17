# Synthetic 3D feasibility probe

This optional experiment tests screenshot-guided first-person control and ordered
visual verification in a tiny Panda3D scene. It is not a production game adapter,
an AI-generated fix, or a new discovered game bug. It never creates a case in the
running REPRO database and does not change the app's selected model.

The model sees screenshots and controls, not coordinates, scene source, evaluator
state, a minimap or a solution path. The environment pauses between inputs. It
supports WASD, keyboard camera yaw/pitch, collection, save and reload. Inputs use
REPRO's `Action` schema. The intentionally seeded defect omits a collected flag
from save data. The hand-authored reference preserves that flag.

## Run

Install the normal repository dependencies first. These optional dependencies stay
outside the production environment:

```sh
uv pip install --python .venv/bin/python --target .repro/3d-probe-deps panda3d==1.10.16 imageio-ffmpeg==0.6.0
PYTHONPATH=.repro/3d-probe-deps:. .venv/bin/python -m scripts.three_d_probe.run --output .repro/three-d-probe/run-01
PYTHONPATH=.repro/3d-probe-deps:. .venv/bin/python -m scripts.three_d_probe.run --output .repro/three-d-probe/run-02 --start-heading 90
PYTHONPATH=.repro/3d-probe-deps:. .venv/bin/python -m scripts.three_d_probe.run --output .repro/three-d-probe/run-03 --start-x 1 --start-heading -35
PYTHONPATH=.repro/3d-probe-deps:. .venv/bin/python -m scripts.three_d_probe.verify .repro/three-d-probe
PYTHONPATH=.repro/3d-probe-deps:. .venv/bin/python -m scripts.three_d_probe.movie .repro/three-d-probe/run-02 .repro/three-d-probe/astra-3d-replay.mp4
```

Model-backed commands require the existing local `OPENAI_API_KEY`. Each control
trial defaults to `gpt-6-astra`, low reasoning, 24 responses and 600 seconds, with
no automatic API retries. Each output directory must be new. `verify` adds two
model requests per completed trial. `movie` makes no model requests. It renders a
fresh animated replay of the saved inputs, omitting API waiting time.

The renderer was checked on macOS with Panda3D's offscreen Cocoa graphics buffer.
Linux headless graphics setup may differ. Panda3D is optional and is not installed
by the app or CI; evaluator unit tests do not require graphics dependencies.

## Evidence and scoring

- `input.json` retains the initial task, tool definitions, budget and a separately
  labeled evaluator start state. The evaluator state is not sent to the API.
- `requests.json` records every model response receipt, model identity, usage and
  latency. It excludes private reasoning and credentials. The original run logger
  retains executed actions, not rejected tool arguments or non-tool messages.
- `frames.json` links each executed input to its screenshot hash and evaluator
  state. `actions.json` is the frozen executed sequence. `model-conclusion.json`
  retains the model's claim; that claim alone does not establish success.
- `replays.json` contains five fresh-state replays per variant. Replay scoring
  checks collection, save, reload, inventory and object persistence using scene
  state that is withheld from the model. The fixed branch is a human-authored
  reference, not a model proposal.
- `verification.json` uses the existing
  `repro.agents.oracle.verify_sequence` implementation. Each verdict sees four
  chronological screenshots from one fresh replay, with the recorded inputs.
  It receives neither evaluator state nor the investigator's conclusion.
  These are separate model calls, not independent ground truth.

Three selected starts in one deterministic scene are a feasibility check, not a
general success-rate estimate. Timing includes rendering and model waits, not
environment installation. The same defect appears in all starts. Native desktop
input, relative mouse capture, continuous-time gameplay, physics determinism,
large maps, source localization and AI patch generation are outside this probe.

For a real 3D game, an adapter still needs a reliable launch/reset/fixture setup,
camera and held-input controls, stable checkpoints, and reproducibility under its
physics and frame timing. REPRO's Luanti adapter remains experimental.

## Components

The room geometry and experiment code were authored for REPRO. No third-party
game assets are included. Panda3D 1.10.16 uses the Modified BSD license.
The optional imageio-ffmpeg wrapper uses the BSD-2-Clause license; its bundled
FFmpeg is used locally for encoding, not redistributed in the evidence bundle.
The existing project uses the OpenAI Python SDK (Apache-2.0).

Sources: [Panda3D](https://pypi.org/project/Panda3D/1.10.16/),
[OpenAI computer use](https://developers.openai.com/api/docs/guides/tools-computer-use),
[GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra).
