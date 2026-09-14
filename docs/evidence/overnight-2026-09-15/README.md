# Overnight investigation records — September 15, 2026

The [overnight progress report](../../overnight-2026-09-15.md) tracks the current
shortlist. Each package below is a frozen snapshot, including unsuccessful attempts.

New records retained after the initial gameplay attempts:

- `md-12579-terra-overnight-01`: verified 12-action crash trigger and a fresh AI patch.
  Three gates pass; the existing-test fixture returns 404, and the full candidate
  visual check passed only 1/5 because reopening was not recorded. The patch avoids
  the save crash in all five candidate executions. No fully validated fix is claimed.
- `md-12620-terra-overnight-01`: original report-only data-patch investigation,
  3/5 confirmed replays and no patch. `datapatch-selection-audit` separately shows
  5/5 retained-image judgments after including the omitted initial-save checkpoint.
  It does not change the original case or count as new game executions.
- `md-12565-terra-overnight-02`: a separate setup-guided attempt (37 Terra calls)
  still stopped before the required unit-entry transition. Use the corresponding
  `MD-candidate-12565-guided.yaml` input manifest when importing it.
- `target-dummy-controls`: supplemental evaluator tests authored after the AI
  proposal. Full online baseline repeats the fixture 404. Default-team serialization
  fails 3/3 on baseline and passes 3/3 with the exact AI patch; the explicit-team
  control passes on both. These do not replace full-map reload verification.

For the initial two gameplay records below, both attempts ended **inconclusive
before the report's trigger was executed**. No reproduction rate, negative-case
success or game fix is claimed for either.

| Report | Model attempts | Outcome | Total model usage |
| --- | --- | --- | --- |
| [#12565 unit disappears on entry](md-12565-terra-overnight-01/result.json) | One cancelled probe (34 calls), then one fresh model context (45 calls) | Conveyor setup was reached, but a ground unit was not obtained and entry never happened. | 79 calls; 904,716 input / 9,672 output tokens |
| [#12603 ghost generator](md-12603-terra-overnight-01/result.json) | One model run; a preceding queue cancellation made zero calls | Editor/playtest setup did not produce a fueled generator; explosion/transport was never tested. | 80 calls; 1,032,495 input / 8,793 output tokens |

Both used `gpt-5.6-terra`, medium reasoning, 120 calls/3,600 seconds per job, and a
1280×720 Linux AMD64 Docker desktop. Build preparation used network access; the
game ran without it. The reports were imported from only the candidate `input`
fields, with isolated pre-fix source and no evaluator/human-fix input. The shared
case ID for #12565 retains both attempts in chronological events; its counters
are cumulative, not just the second run.

The first unit probe exposed recorder image aliasing and an overrestrictive
checkpoint limit; it was cancelled and retained, then restarted after PR #13.
Later inspection found requested Ctrl-clicks were ignored by the worker. PR #14
adds modifier clicks and held inputs, independently qualified using real X11
events. The game setup failures have additional causes; fixing the input driver
does not establish that either bug reproduces.

Each directory contains the complete case snapshot, event trace, artifact bytes
and SHA-256 manifest. Recorded explanations are agent observations, not independent
qualification. No original save attachments were installed. These exports are
read-only recordings and do not create new investigations when imported.

For example, after pulling the repo:

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12565-terra-overnight-01 --manifest benchmarks/candidates/MD-candidate-12565.yaml --id recorded-md-12565
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12603-terra-overnight-01 --manifest benchmarks/candidates/MD-candidate-12603.yaml --id recorded-md-12603
```

Both imports were verified in an isolated local store. The optional manifest flag
lets candidate recordings use the existing provenance/hash-checked importer without
promoting them into the admitted benchmark set.

A supplementary [#12354 manifest](../../../benchmarks/candidates/MD-candidate-12354.yaml)
records a potentially clearer cargo-loss-on-reload story. Its issue and historical
fix were reviewed, but it has **not been run or qualified**. #12626 remains deferred
for the behavioral-contract reason in the original shortlist; it was not silently
reintroduced as a fresh positive candidate.

The new crash and persistence packages use the same importer:

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12579-terra-overnight-01 --manifest benchmarks/candidates/MD-candidate-12579.yaml --id recorded-md-12579
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12620-terra-overnight-01 --manifest benchmarks/candidates/MD-candidate-12620.yaml --id recorded-md-12620
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12565-terra-overnight-02 --manifest benchmarks/candidates/MD-candidate-12565-guided.yaml --id recorded-md-12565-guided
```

The supplied-input variants are explicitly labeled assistance and remain separate
from the report-only cases. They are not additional distinct bug reports.
