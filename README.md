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
cd apps/web && npm ci && npm run build && cd ../..
uv run repro serve
```

The API is available at `http://127.0.0.1:8000/api` and its interactive reference at `http://127.0.0.1:8000/docs`. Use one API process. The worker queue is intentionally local and serial. Rebuild the worker image after pulling driver changes: the backend now uses protocol 2 over a persistent connection.

The dashboard is served at `http://127.0.0.1:8000/`. For frontend development, run `npm run dev` in `apps/web` while the API runs on port 8000; Vite proxies API and event-stream requests. Its case viewport, activity, evidence, source, diff, validation and benchmark views read real backend records. New installations start empty.

To inspect the exported MD-001 recording without running Docker or making model calls:

```bash
uv run repro import-evidence docs/evidence/MD-001
# Optional: --id another-recording-id; --force replaces only an imported case.
```

This explicitly imports a read-only **Imported recording**, with its original case ID,
recorded date, source directory and import timestamp. The dashboard initially selects
an all-five-gates-passing case, then the furthest progressed state, then the latest
recorded update. MD-001 retains `AWAITING_HUMAN`: five stages are finished and the sixth
contains the recorded handoff-review state, not an invented human approval.

Identical re-imports are a no-op; changed packages require `--force`. Local cases are
never replaced. Artifact IDs are global in this store: if another case already owns a
recorded artifact ID, use a separate `REPRO_DATA_DIR`. Event streams are merged in
recorded sequence order; API `seq` is the local cursor and `recorded_seq` preserves the
original sequence. Missing artifact references remain in raw events but are not shown
as downloadable activity links.

Integrity coverage follows the export: every entry in either `artifacts.json` is checked
before any import writes. This checkout has only the network-validation manifest; the
patch is additionally checked against `patch_unchanged_sha256` in its result. These yield
10 unique artifacts and 738 events. The root JSON metadata and event streams have no
published checksums, so their authenticity cannot be independently verified. No prose
is parsed and no missing artifacts or metrics are reconstructed. Usage and elapsed time
retain the explicit original totals; rerun-only counters are not relabeled as lifetime
totals. Missing usage/timing snapshots remain null. Importing does not rerun the recorded
276 upstream tests or any validation gate.

An **investigation** is one bug case, from the player report through reproduction, diagnosis, and review. Small info buttons explain the stats, stages, and actions on hover, keyboard focus, or click; Escape dismisses the explanation. **Proposed patch** shows the saved justification and risks above the exact source diff, with green additions, red deletions, and old/new line numbers. Validation evidence is shown separately from the proposed explanation.

Click **Triage**, **Reproduce**, **Reduce**, **Localize**, **Validate**, or **Review** to open that stage's activity. Stage headers show the first and latest saved event times in your local time zone. The full history is searchable, including early stages and repeated attempts; model calls and observations can be included, and older entries load in batches of 40. Each entry has its own timestamp, record details, and relevant screenshot/log links. Validation exposes the latest build and test logs directly. First/latest intervals include pauses and are not active work durations.

On macOS, Docker may not have file-sharing access to a Documents folder. Set `REPRO_SANDBOX_DIR=/tmp/repro-workspaces` in `.env` in that situation. Case records and evidence stay under `REPRO_DATA_DIR`; only disposable build workspaces use the alternate directory. Temporary builds may need preparation again after a reboot.

Mindustry's pinned SDL desktop dependency does not ship a Linux ARM64 native library. Use the AMD64 image even on Apple Silicon (Docker emulates it); do not count an architecture-related launch failure as a reproduced game bug.

For manual play on macOS, see the [verified Mindustry desktop setup](docs/macos-setup.md).

```bash
uv run repro ingest report.txt --commit FULL_40_CHARACTER_SHA --title 'Player report'
uv run repro prepare CASE_ID
uv run repro investigate CASE_ID
uv run repro replay CASE_ID
uv run repro replay CASE_ID --regression  # exit 1 when the known bug is observed
uv run repro reduce CASE_ID  # refine the baseline replay; revalidate a candidate if it changes
uv run repro validate CASE_ID
uv run repro report CASE_ID --output output/pdf/repro-report.pdf
```

**Export PDF** downloads a **REPRO Report** with the workspace's lavender/charcoal branding, the current saved report, reproduction steps, diagnosis, patch explanation and diff, validation results, screenshots, and a stage timeline with selected milestones in UTC. Export makes no model calls. `GET /api/cases/CASE_ID/report` also returns PDF by default. For Markdown, add `?format=markdown`, use a `.md` CLI output path, or omit `--output` to print it to the terminal.

`replay` uses the retained pre-patch Mindustry build. `--candidate` uses the candidate build. A visual replay needs API access for its independent verifier. An explicit `validate` rerun repeats both baseline and candidate gates, retaining the previous result as an artifact. The validation workflow additionally checks that the expected game/UI state was reached; simply failing to observe the bug is insufficient to approve a patch.

## What is implemented

- Typed report intake, SQLite case snapshots, ordered events and reconnectable SSE.
- Responses API triage, hypothesis recording, screenshot-guided computer actions, source search and candidate diffs. Default: **`gpt-5.6-luna`**; `REPRO_MODEL=gpt-5.6-terra` is the requested alternative.
- A 1280 × 720 Xvfb desktop with recorded inputs, screenshots, logs and process state.
- Exact historical source snapshots, no future Git objects/remotes, and network-disabled investigation containers. The model controller keeps its API key outside the game sandbox.
- Independent visual/log/crash oracles, clean-profile replay, bounded action reduction, source localization, replay regressions, candidate builds/tests, post-patch replay, and a narrow launch smoke check.
- Artifact downloads, PDF and Markdown reports, saved patch justifications, and local review decisions. Review approval **does not push or merge changes to target-game repositories**.

## Recorded Mindustry run

The [MD-001 evidence package](docs/evidence/MD-001/README.md) contains a real historical run using Terra: the duplicate Weather-button bug reproduced in **5/5 clean runs**, the replay was reduced from **23 to 8 actions**, and **5/5 candidate replays** reached the correct menu with one Weather button. The first-ranked source file matched the later human-fix file. Screenshots, the generated patch, replay, raw logs and unsuccessful attempts are included.

The [latest validation rerun](docs/evidence/MD-001/network-validation/README.md) passed **all five gates**, including **276/276 upstream tests with zero skips**, and enabled local handoff review. The initial offline run passed 275/276 tests; a mod test could not download its GitHub fixture. That failure and the later network-enabled result are preserved separately. This selected development session includes runner improvements and refinement passes; it is not representative benchmark accuracy or one uninterrupted autonomous resolution.

A [controlled worker comparison](docs/evidence/MD-001/network-validation/worker-timing/README.md) measured the eight-action desktop replay at a median **47.3 → 30.9 seconds**, about **35% faster**, excluding model calls. Both workers used the same loading guard and recorded waits, and all six timing runs reached the target view. Dashboard updates now avoid repeatedly fetching event history and rendering the entire artifact list.

## Current limits

Mindustry is the primary implementation target. The Luanti adapter is experimental and has not established cross-game performance. Build dependencies and startup behavior vary by historical revision. Visual judgments are model-based, even though verification calls are separate from the investigator; they are not a ground-truth oracle.

Uploads are retained and hashed, but automatic video normalization, save installation and attachment-driven investigation are not implemented. Network/multiplayer experiments, distributed workers, automatic upstream PR publication and reliable ownership inference without CODEOWNERS remain future work. Smoke testing currently checks a clean desktop launch, not broad gameplay coverage. Bounded action reduction is not a proof of global minimality.

Some upstream tests perform network requests at runtime even with Gradle's `--offline` flag. Candidate build/test validation now has network access by default (`REPRO_VALIDATION_NETWORK=true`) so those dependencies can load. Set it to `false` for an offline validation run. The selected policy is recorded in the event audit. Game investigation and replay still use fresh containers with networking disabled; credentials stay in the controller. No tests are skipped.

No benchmark success rate is implied by unit tests or mock observations. See [benchmark protocol](docs/benchmark.md) for the evidence boundaries and [development notes](docs/architecture.md) for extension points.

## Development

```bash
uv run ruff check repro tests scripts infra/docker/worker.py
uv run pytest -q
cd apps/web
npm test
npm run build
```

PRs are the collaboration unit. Keep changes scoped, include validation and limitations, and preserve team members' work. Never commit `.env`, runtime data, API keys, downloaded target-game source, or evaluator-only material inside a model-visible workspace.
