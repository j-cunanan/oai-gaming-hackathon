# Target Dummy — full save and reopen passes 5/5

The later MAX validation now establishes the full reported behavior after the unchanged AI patch: **five fresh candidate runs save the map, leave it, reopen it and identify the retained Target Dummy with the editor's non-modifying picker**. The baseline still crashes **5/5** on the unchanged 12-action trigger.

Each candidate run executes that same 12-action trigger, followed by a separately planned and frozen **12-action save/reopen check**. The planner's exploratory success was not counted as a repetition. The final sequence oracle uses five chronological checkpoints. `result.json` retains the verification plan, its trigger fingerprint and the bound patch artifact; `repro.yaml` retains the original baseline trigger.

| Gate | Result |
| --- | --- |
| Regression before patch | Pass — crash reproduced 5/5 |
| Candidate build | Pass |
| Existing upstream tests | **Fail — `ModTestAllure.begin()` requests an unavailable archive (HTTP 404)** |
| Original replay after patch | Pass — all 5 runs reach the saved/reopened state without the symptom |
| Startup smoke | Pass |

**This is four passing gates, not an approved or fully validated handoff.** Networking was enabled for the candidate suite; the failure was not waived. The earlier supplemental network-enabled baseline also has the same unavailable-fixture failure, but those evaluator checks do not change this case's gates. No upstream game patch or handoff approval was submitted.

The patch itself remains the original medium-reasoning Terra proposal, generated from the pre-fix source and recorded crash. This later MAX work validates it; it is not a second independently generated patch. The first incomplete candidate replay and the subsequent 24-turn planner failure remain in their own sibling packages.

The [seven-page REPRO PDF](repro-report.pdf) was generated from this saved case without new model calls and visually reviewed. Its final page pairs the crashed baseline with the retained-object inspection after candidate reopen. `report-provenance.json` binds the PDF and renderer to the frozen case sources.

This cumulative snapshot contains **889 events and 503 artifacts**. Totals are **107 model calls, 962,177 input tokens and 42,432 output tokens** across the case's jobs. Relative to the previous frozen snapshot, this validation adds **19 MAX calls, 136,196 input tokens and 29,182 output tokens**.

Import into a separate store, or replace the same earlier imported case ID with `--force`:

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12579-terra-postconditions-02 --manifest benchmarks/candidates/MD-candidate-12579.yaml --id recorded-md-12579
```

Cumulative snapshots share artifact IDs and cannot coexist under different aliases in one store. Importing is read-only and makes no model calls. For a fresh local execution, use the app's **Rerun validation** or `repro validate CASE_ID`; a single manual candidate replay does not include this separate repeated save/reopen validation workflow.
