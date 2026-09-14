# R07 ordered sequence audit

On September 15, 2026 (JST), the new generic sequence verifier was checked with
Jayson's retained qualification evidence for Mindustry #12620 and #12623: five
buggy recordings and one human-fixed control for each issue. No new game was
launched for this audit. These are 12 judgments on two distinct bugs, not 12 new
reproduction runs or a measure of general accuracy.

The first pass supplied the selected screenshots and their corresponding actions.
It agreed with 3/12 expected outcomes and left nine inconclusive, mainly because
intervening close/reopen navigation was missing. Those results are preserved in
[sequence-audit.json](sequence-audit.json).

The second pass also supplied the complete recorded input trace through the final
checkpoint. It agreed with 12/12 expected outcomes (10 buggy, 2 human-fixed), with
positive target-state checks, while retaining the same symptom descriptions and
images. Results are in [sequence-audit-with-trace.json](sequence-audit-with-trace.json).
This change was calibrated on this small retained set. Fresh gameplay qualification
and independent broader examples are still needed before calling R07 complete.

The verifier saw the report-defined symptom, neutral checkpoint labels, actual
screenshots, recorded input coordinates/keys and process state. It did not receive
baseline/fixed labels, expected outcomes, source diffs or evaluator metadata.
Input actions are navigation evidence, not proof that their effects occurred.
The driver matched recorded action events by screenshot artifact ID and evaluated
the outcome only after each model response. Opaque alpha `ff` was explicitly
excluded from the RGB color-change symptom.

Source images and event logs remain under [#12620](../qualification/12620/) and
[#12623](../qualification/12623/). Both passes used `gpt-5.6-terra` with low reasoning,
12 bounded model calls each. [usage.json](usage.json) retains aggregate token counts.
The application supports fresh reset-separated replay checkpoints and rejects
missing/reversed frames, conflicting judgments, absent prerequisites and weak
confidence. Unit tests cover those rejection paths; the saved examples alone do
not establish their frequency in real play.

To run a new audit with the current verifier (12 paid API calls at most):

```bash
REPRO_MODEL=gpt-5.6-terra uv run python scripts/audit_sequences.py --output .repro/new-sequence-audit
```

Use `--without-trace` for a comparison without intervening inputs. The driver
requires a new/empty output directory, records source hashes and usage, and leaves
prior results intact. New judgments may differ; the frozen original results above
are not overwritten. This driver audits retained evidence, not live recorder or
UI behavior. Live testing later found and fixed checkpoint snapshot aliasing and
premature recording limits in PR #13.
