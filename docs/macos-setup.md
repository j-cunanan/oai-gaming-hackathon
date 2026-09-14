# Mindustry on macOS

## Verified local installation (2026-09-14)

Mindustry **v160.3** launches on this MacBook Pro: Apple M2 Max, 32 GB RAM,
macOS 26.6.2. The main menu was visually verified. Startup logs confirmed
OpenGL 4.1 on the Apple M2 Max, CoreAudio initialization, and Java 23.0.2.
This is a desktop launch smoke check; gameplay and automated replays were not tested.

The game is installed at `~/Applications/Mindustry.app`. Open it in Finder, or run:

```bash
open "$HOME/Applications/Mindustry.app"
```

This is a local app wrapper around the unmodified official desktop JAR, using
the existing ARM64 Java installation selected by `/usr/libexec/java_home` and
the macOS `-XstartOnFirstThread` flag. It does not bundle Java.

Source: [official v160.3 release](https://github.com/Anuken/Mindustry/releases/tag/v160.3).
The downloaded `Mindustry.jar` SHA-256 matched the release asset digest:

```text
0aacb97bbb15ec2467cf9affb1af053aa9deb9fbe1f4c94634bb2753a3db2577
```

A download copy is in `.repro/games/mindustry/v160.3/Mindustry.jar`, which is
already ignored by Git. No game binaries or upstream source are committed.

## Automated testing prerequisites

The installed desktop app is for manual exploration. REPRO builds the exact
historical revision for each case inside its Linux worker; it does not use this
app as the benchmark target.

Follow the [repository setup](../README.md#run-locally) for the full workflow.
Docker Desktop 29.4.1 is now running. The `repro-worker:local` image has been
built for `linux/amd64`. Python 3.12.10 dependencies were installed with
`uv sync --frozen`; Ruff and all 13 repository tests pass. The dashboard builds
successfully with project-local Node 22.23.2, leaving the system Node unchanged.

The API and built dashboard run at `http://127.0.0.1:8000`; `/api/health` returns
`status: ok`, and the browser shows the backend connected. The ignored local `.env` now contains the stored API key and selects
`gpt-6-astra` with low reasoning. R03 passed a three-call live screenshot and
tool round trip; see [model smoke evidence](evidence/R03/README.md). The API was
restarted to load this configuration. Investigation limits remain 60 calls and
1,800 seconds per job.

To restart the API from the repository root:

```bash
.venv/bin/repro serve
```

For future dashboard builds using the installed Node 22:

```bash
export PATH="$PWD/.repro/tooling/node_modules/node/bin:$PATH"
npm run build --prefix apps/web
```

Historical case `d4493cca50fb` (MD-001) is prepared locally. Its source is pinned
to `a5c178ae5abcc630613c233e0afbb361021d3828`. The desktop build passed, and
**276/276 upstream baseline tests passed with preparation networking enabled**.
This does not clear R08, which concerns offline tests.

A fresh worker launched the built game with `--network none`, a read-only root,
all capabilities dropped and `no-new-privileges`. The main menu was visually
verified at 1280 × 720, and the process remained alive after startup. The worker
was stopped after verification; its prepared build and evidence remain available.
The API and dashboard were left running.

Inspect the case in the dashboard for `runner-setup-smoke.png`,
`runner-setup-smoke.log`, `runner-setup-smoke.json`, `prepare-build.log`,
`baseline-tests.log` and `history-audit.json`. Local files live under
`.repro/cases/d4493cca50fb/artifacts/`; a compact summary is also saved in
`.repro/runner-setup-result.json`. These are setup evidence, not a new reproduced
bug, candidate patch or validation result. R02 is now complete on this evidence.

Keep `--platform linux/amd64` when building the worker on Apple Silicon, as
documented in the README. Successful native macOS startup does not establish
that a historical Linux build or replay will succeed.
