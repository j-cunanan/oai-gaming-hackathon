# R05/R06: selected Mindustry cases qualified

Evaluator-only evidence, September 14, 2026. Do not give these human-fixed
revisions, evaluation notes or qualification traces to a fresh investigator.
These are qualification runs, not new autonomous patch-generation results.

| Case | Clean baseline confirmation | Historical human-fixed check |
| --- | --- | --- |
| [#12579 Target Dummy](12579/README.md) | 5/5 nonzero exits with the null `unitTeam` save signature; 13 actions | Saved and reopened DummyRepro, then eyedropper identified the retained Target Dummy |
| [#12620 data-patch persistence](12620/README.md) | 5/5 chronological sequences: sole patch present, deleted, saved, reopened, returned; 40 actions | Deleted patch remained absent after reopening |
| [#12623 hex precision](12623/README.md) | 5/5 sequences for both Colored Floor and Colored Wall: entered `ff0300`, reopened `ff0200ff`; 26 actions | Both reopened as `ff0300ff`, preserving RGB; trailing `ff` is alpha |

Each control was checked once successfully; these are paired controls, not
three additional independent bugs. The color check covers the reported `ff0300`
mismatch, not every hex value. Target Dummy reload was checked in the editor,
not in gameplay. No external save attachments were required or installed.

## Evidence and method

Each numbered directory contains baseline and human-fixed result JSON, exact
revisions, build/test logs, history audits, case snapshots, complete event
traces and the screenshots referenced by result JSON. Artifact IDs resolve to
files in that directory's `artifacts/` folder. [Summary](summary.json) includes
model usage across all attempts and the preparation test counts.

The runs used Linux AMD64 Docker, 1280 × 720 Xvfb, fresh profiles, networking
disabled during game actions, and Astra with low reasoning. Preparation builds
and upstream tests used networking. API keys remained outside worker mounts.
Baseline discovery used only public report input and game UI tools; source tools
were disabled. Human-fixed builds used separate evaluator workspaces.

R05's crash oracle requires both a nonzero game exit and the specific null
`unitTeam` log signature. R06 uses separate model calls over ordered screenshots
and actual recorded actions: before/input, deletion/confirmation, save/map
selection and reopened/readback state. The independent model reads literal
values and states; Python compares them with the frozen expectations for that
trial. These model judgments are inspectable evidence, not ground truth.

The standard REPRO visual verifier accepts a single final screenshot. It
correctly rejected the initial R06 attempts as insufficient to establish prior
input or deletion. R06 is therefore qualified with the separate chronological
verification drivers, **not yet with the standard replay verifier**. Integrating
and freezing those temporal oracles is required before R07/R09 showcase runs.
No R06 pipeline result has been relabeled as an autonomous successful run.

## Retained unsuccessful attempts and adjustments

- R05 initially reproduced 4/5. One worker opened an unmanaged, narrower window
  and missed coordinate targets. The runner now waits for Xvfb before starting
  Openbox and for Openbox readiness before launching the game. A fresh set of
  five runs then passed. The original result and failed screenshot are retained.
- The first R05 fixed control did not actually place the dummy: fast search
  input lost characters and selected Metal Floor 3. It remains inconclusive.
  The successful control used extra UI settling time and explicitly verified
  the Target Dummy before save/reopen and with the eyedropper afterward.
- The first chronological data-patch oracle unnecessarily required the optional
  display name PersistenceProbe: it scored 4/5 baseline and 0/1 control when one
  patch appeared as `<unnamed>`. Those results are retained. The corrected oracle
  checks the sole one-field patch entry, empty list after deletion, same map and
  reopened list. It was rerun on five new baseline profiles and a fresh control;
  all passed. Optional naming is not the reported persistence defect.
- Initial single-frame color and persistence attempts are retained as
  insufficient evidence. No failed attempt is included in the final five-run
  denominator; the separate attempt records make that distinction explicit.

[Desktop-readiness change](desktop-readiness.patch) and
[wait helper](wait_desktop.py) record the environment fix. The change was verified
by the fresh R05 runs and all 27 repository tests. The upstream game source was
not patched during qualification; controls are the historical human-fixed commits.

Recorded session drivers are in `drivers/`. They reference this session's local
case IDs and stores; they are audit copies, not a portable public CLI. The result
JSON contains the full action sequences for reconstruction against the recorded
revisions. Baseline scripts are bounded by the configured 60 calls/1800 seconds;
chronological verification uses at most 10 calls (six for color), and fixed UI
verification at most 30 calls/600 seconds. Detailed usage includes failed runs.
