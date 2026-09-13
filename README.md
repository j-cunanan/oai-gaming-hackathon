# REPRO

Autonomous BugOps for games. Turn a player report into inspectable evidence, a repeatable replay, source findings, and a candidate patch.

REPRO uses the OpenAI Responses API to investigate a real game through a disposable Linux desktop. A separate verifier checks observations, the runner repeats actions from clean profiles, and bounded delta debugging removes unnecessary actions. Source investigation and candidate changes follow behavioral confirmation. Every experiment is recorded.

This is an early working implementation of the [full build context](docs/REPRO_FULL_BUILD_CONTEXT.md). The specification describes the intended product; it is **not a claim that all its milestones or example benchmark numbers have been achieved**.

## Run locally

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Docker with about 6 GB available to a worker, and Git. Node.js 22 is needed to build the dashboard. Mindustry and its dependencies are downloaded during preparation, not vendored into this repository.

```bash
uv sync --frozen
cp .env.example .env
# Add OPENAI_API_KEY to .env. Keep this file local.
docker build --platform linux/amd64 -t repro-worker:local infra/docker
uv run repro serve
```

The API is available at `http://127.0.0.1:8000/api` and its interactive reference at `http://127.0.0.1:8000/docs`. Use one API process. The worker queue is intentionally local and serial.

On macOS, Docker may not have file-sharing access to a Documents folder. Set `REPRO_SANDBOX_DIR=/tmp/repro-workspaces` in `.env` in that situation. Case records and evidence stay under `REPRO_DATA_DIR`; only disposable build workspaces use the alternate directory. Temporary builds may need preparation again after a reboot.

Mindustry's pinned SDL desktop dependency does not ship a Linux ARM64 native library. Use the AMD64 image even on Apple Silicon (Docker emulates it); do not count an architecture-related launch failure as a reproduced game bug.

```bash
uv run repro ingest report.txt --commit FULL_40_CHARACTER_SHA --title 'Player report'
uv run repro prepare CASE_ID
uv run repro investigate CASE_ID
uv run repro replay CASE_ID
uv run repro replay CASE_ID --regression  # exit 1 when the known bug is observed
uv run repro validate CASE_ID
uv run repro report CASE_ID --output investigation.md
```

`replay` uses the retained pre-patch Mindustry build. `--candidate` uses the candidate build. A visual replay needs API access for its independent verifier. The validation workflow additionally checks that the expected game/UI state was reached; simply failing to observe the bug is insufficient to approve a patch.

## What is implemented

- Typed report intake, SQLite case snapshots, ordered events and reconnectable SSE.
- Responses API triage, hypothesis recording, screenshot-guided computer actions, source search and candidate diffs. Default: **`gpt-5.6-luna`**; `REPRO_MODEL=gpt-5.6-terra` is the requested alternative.
- A 1280 × 720 Xvfb desktop with recorded inputs, screenshots, logs and process state.
- Exact historical source snapshots, no future Git objects/remotes, and network-disabled investigation containers. The model controller keeps its API key outside the game sandbox.
- Independent visual/log/crash oracles, clean-profile replay, bounded action reduction, source localization, replay regressions, offline candidate builds/tests, post-patch replay, and a narrow launch smoke check.
- Artifact downloads, Markdown reports and local review decisions. Review approval **does not push or merge changes to target-game repositories**.

## Current limits

Mindustry is the primary implementation target. The Luanti adapter is experimental and has not established cross-game performance. Build dependencies and startup behavior vary by historical revision. Visual judgments are model-based, even though verification calls are separate from the investigator; they are not a ground-truth oracle.

Uploads are retained and hashed, but automatic video normalization, save installation and attachment-driven investigation are not implemented. Network/multiplayer experiments, distributed workers, automatic upstream PR publication and reliable ownership inference without CODEOWNERS remain future work. Smoke testing currently checks a clean desktop launch, not broad gameplay coverage. Bounded action reduction is not a proof of global minimality.

No benchmark success rate is implied by unit tests or mock observations. See [benchmark protocol](docs/benchmark.md) for the evidence boundaries and [development notes](docs/architecture.md) for extension points.

## Development

```bash
uv run ruff check repro tests scripts
uv run pytest -q
```

PRs are the collaboration unit. Keep changes scoped, include validation and limitations, and preserve team members' work. Never commit `.env`, runtime data, API keys, downloaded target-game source, or evaluator-only material inside a model-visible workspace.
