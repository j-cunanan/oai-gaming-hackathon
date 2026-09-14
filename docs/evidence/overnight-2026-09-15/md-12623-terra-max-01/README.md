# Report-only color investigation — incomplete final response

This fresh Terra MAX investigation received the original color-input report without the human-fixed qualification records or historical developer patch. It observed entered color values changing on readback, including `ff0300` becoming `ff0200ff` for Colored Floor and Colored Wall. It also explored other values and placement. Those are investigator observations, not independent repeated confirmations.

After a clean-profile reset, the investigator executed a separate final **29-action sequence**: create a map, enter and confirm `ff0300` for Colored Wall, place and pick it for readback, then enter/confirm/reopen the Colored Floor picker. All 29 actions and their existing checkpoint labels are retained as global action indices **55–83**. Earlier exploratory actions remain in the same event history.

The final model response was incomplete after using its full **16,000 output-token allowance**. No partial actions from that response were executed. The original final proposed oracle was not returned and is not reconstructed here. The case is **FAILED**, with no saved reproduction, independent verdict, five-run confirmation or proposed patch.

This package preserves **209 events and 109 artifacts**. Returned-response usage, including the incomplete response's reported usage, is **52 model calls, 1,313,193 input tokens and 42,109 output tokens**. A prior queue cancellation happened before any model call and is not an additional investigation.

The final trace was subsequently supplied to `md-12623-terra-replay-02`, with cached triage and six existing checkpoints explicitly selected by an operator. That is a separate assisted qualification job. Only its own fresh outcomes can establish whether the supplied trigger qualifies for AI diagnosis and patching; this package's observations do not count as those confirmations.

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12623-terra-max-01 --manifest benchmarks/candidates/MD-candidate-12623.yaml --id recorded-md-12623-max
```
