# Color bug reproduced 5/5; the AI candidate failed 5/5

This is the final snapshot of **md-12623-terra-replay-02**, the explicitly assisted qualification of the [report-only investigator's recording](../md-12623-terra-max-01/README.md). The separate [first snapshot](../md-12623-terra-replay-02-first/README.md) preserves an inconclusive 0/1 check whose selected images omitted wall placement and picking.

The continuation added those two **existing** checkpoint labels to the original six, in chronological order. All **29 actions**, the required outcome and the target revision remained unchanged. Five fresh profiles then independently confirmed the bug **5/5**: enter `ff0300`, confirm, place and pick the Colored Wall, reopen its picker and read `ff0200ff`; enter and confirm the same value for Colored Floor, then reopen that picker with the same wrong readback. This scope does not cover every reported input value or adjacent floor placement.

Terra MAX then inspected source and [proposed a patch](candidate.patch), removing `updateColor(false)` from the hex-input callback in `ColorPicker.java`. Its [rationale](patch-rationale.json) hypothesized that avoiding an RGB→HSV→RGB round trip would preserve the entered color. **That causal proposal was insufficient:** all five fresh candidate replays still read `ff0200ff` for both tile types. The rationale is a recorded model hypothesis, not a verified explanation of a working fix.

| Check | Result |
| --- | --- |
| Regression before patch | Pass: 5/5 clean bug confirmations |
| Candidate build | Pass |
| Existing upstream tests | Pass: 276/276, zero failures, errors or skips |
| Original replay after patch | **Fail: 0/5 correct outcomes; the bug remained in all five** |
| Startup smoke | Pass: clean launch and live process only |

The case is `AWAITING_HUMAN`, but validation failed and handoff is blocked. It is a useful **reproduction and rejected-candidate** example, not a completed game fix. No test was waived and no patch was published upstream. The [test/build audit](../color-candidate-audit/README.md) binds the existing JUnit outputs and distinguishes the baseline and compiled candidate JARs. The fresh offline baseline suite had its own ModTestAllure failure; candidate tests actually ran with network enabled and passed.

The final package contains **429 events and 178 artifacts**, including the earlier checkpoint-selection failure. Its cumulative **44 returned calls, 520,345 input tokens and 95,683 output tokens** include that first attempt; do not add the first snapshot's usage again. Recorded active time is **2,263.78 seconds** across both sessions, excluding the gap between them. First successful reproduction was recorded after 556.80 active seconds. No reduction was attempted: the supplied trace remains 29 actions.

The exact `continuation_driver.py` and its SHA-bound `checkpoint-selection-revision.json` artifact document the correction. It reused the remaining portion of the original 55-minute active-work budget with MAX reasoning, 24,000 output tokens, a 450-second request timeout and no automatic retry. The artifact's `same_cumulative_model_call_budget` field records the intended 120-call allowance; actual enforcement is per Model session. Total recorded calls remained below 120. The protocol-4 worker, clean source, retained baseline JAR and freshly executed baseline assertions are bound in the input artifacts. The worker's wheel change is irrelevant to this trace, which contains no scroll actions.

The [REPRO PDF](repro-report.pdf) is generated from this saved final case. The complete original report, source findings, rationale, action trace, selected screenshots, logs and per-replay verdicts are retained. Re-rendering the report does not run the AI or game again.

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12623-terra-replay-02-final --manifest benchmarks/candidates/MD-candidate-12623-replay-guided.yaml --id recorded-md-12623-final
```
