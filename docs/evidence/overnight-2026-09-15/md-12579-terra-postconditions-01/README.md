# Target Dummy — unfinished MAX postcondition plan

This is a later cumulative snapshot of `md-12579-terra-overnight-01`, after a new validation attempt on the same AI candidate. The original result remains in the sibling `md-12579-terra-overnight-01` package.

The retry freshly reproduced the crash **5/5** and built the candidate. Existing upstream tests still failed because `ModTestAllure.begin()` downloads an unavailable archive (HTTP 404). Network was enabled; no failure was waived.

The candidate postcondition planner ran at `gpt-5.6-terra`, **max reasoning**, and exhausted its then-current **24-turn** limit. It reopened the map and reached a Target Dummy inspection, but did not finish and freeze a verification plan. Those exploratory actions are not five candidate replays or an independently verified save/load result. Startup smoke was not reached in this attempt.

The snapshot is `FAILED` and includes **641 events, 395 artifacts**, and cumulative usage of **88 calls, 825,981 input tokens and 13,250 output tokens**. That includes earlier medium-reasoning work on the same case. PR23 subsequently increases the planner allowance within the existing job budgets and handles exhausted planning as an unavailable check; that later implementation does not change this recording.

Import into a separate store, or replace an earlier imported snapshot of this same case with `--force`:

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12579-terra-postconditions-01 --manifest benchmarks/candidates/MD-candidate-12579.yaml --id recorded-md-12579
```

Cumulative snapshots share artifact IDs and cannot coexist under different aliases in one store. Importing preserves the failure and makes no model calls.
