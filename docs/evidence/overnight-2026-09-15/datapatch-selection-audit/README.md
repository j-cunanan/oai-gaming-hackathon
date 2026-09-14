# Data-patch checkpoint-selection audit

The fresh report-only case confirmed 3/5 replays. Two judgments lacked proof of the
initial save, because the investigator recorded `patch_initial_save` but omitted
it from the final seven-checkpoint oracle. Its screenshot visibly shows “Saved!”.

This audit adds that existing frame as an eighth checkpoint and reverifies the
same five recordings with the unchanged verifier and original input trace. All
five judgments then observe the persistence defect (confidence 0.94–0.96).

This is **five retained-image judgments, not five new game executions**. The
original case remains 3/5, and the assisted selection does not count as a fresh
independent discovery. `audit.json` retains both verdict sets, exact source image
hashes, revised oracle, model/effort and usage. Raw screenshots and actions are in
the adjacent `md-12620-terra-overnight-01` package. `driver.py` is the original local
execution driver; it requires that source case and a new output directory to rerun.
