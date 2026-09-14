# REPRO overnight work — September 15, 2026

Work in progress. The authorized window ends at **07:04 JST / 22:04 UTC**.
This note separates fresh REPRO investigations, operator-assisted attempts,
retained-image audits, and supplemental evaluator checks. It is not a claim of
complete benchmark coverage.

The strongest fresh result so far is the **Target Dummy save crash**: REPRO
reproduced it, reduced the replay, located the cause, and generated a one-line
candidate patch. The saved result is still blocked at validation. This is a good
report-to-reproduction story, with an honest remaining fix-verification problem.

| Candidate | Recorded result so far | Presentation value and limit |
| --- | --- | --- |
| [Target Dummy save crash](evidence/overnight-2026-09-15/md-12579-terra-overnight-01/result.json) | 15 actions reproduced 5/5; reduced 12-action trigger reproduced 5/5, then reconfirmed 5/5 on the upgraded worker. Fresh Terra source diagnosis and patch retained. | Clear creation → save → crash story. Three gates pass. The original candidate replay avoided the crash 5/5, but only 1/5 visual judgments established the full expected state; reopening was not recorded. One upstream fixture download also returns 404. |
| [Deleted data patch returns](evidence/overnight-2026-09-15/md-12620-terra-overnight-01/result.json) | Fresh report-only attempt: 3/5 confirmations, no patch. Reverification with an omitted recorded save checkpoint included matched all five retained recordings. | Strong persistence story. The audit is not five new executions. A separately labeled evidence-guided investigation is in progress. |
| [Unit loss on payload conveyor](evidence/overnight-2026-09-15/md-12565-terra-overnight-01/result.json) | Initial probe and fresh retry could not obtain the required unit. A later setup-guided attempt also stopped before entry/transport was tested. | Potentially stronger gameplay demo, currently inconclusive. Normal transformation into a payload is not evidence of loss. |
| [Ghost generator after explosion](evidence/overnight-2026-09-15/md-12603-terra-overnight-01/result.json) | The fueled-generator/explosion setup was not reached. | Visually interesting report, but no runtime qualification from these attempts. |
| [Derelict conveyor loses cargo on reload](../benchmarks/candidates/MD-candidate-12354.yaml) | First preparation failed because JitPack lacked the pinned Arc dependency. The exact required Arc revision has now been prepared from source for a retry. | A clear cargo-loss story if reproduced. No runtime result yet. |

The earlier Weather case remains available as a simpler reference with all five
recorded gates passing. It predates this overnight run and is not counted as a
new discovery or fresh overnight fix.

## Alignment with Jayson

Main was fetched before work and checked again during the run. Jayson's evidence
import/provenance work (#9) and baseline-differential validation (#5) are retained.
His three human-fixed qualification controls establish the selected historical
bugs and environment, not a fresh AI-generated fix. No later code-mining records
were located in the fetched branches beyond the existing qualification and
MD-001 records. That describes the inspected repository, not unpushed work.

## Target Dummy candidate and independent checks

The [AI candidate](evidence/overnight-2026-09-15/md-12579-terra-overnight-01/candidate.patch)
writes the building's team when the dummy's team has not yet been initialized.
The [saved rationale](evidence/overnight-2026-09-15/md-12579-terra-overnight-01/patch-rationale.json)
connects the crash to saving before the first update and describes compatibility
and remaining risks. The patch was produced from the pre-fix source and recorded
crash, without the historical developer patch in the model input.

[Supplemental evaluator checks](evidence/overnight-2026-09-15/target-dummy-controls/result.json),
authored after that AI proposal, show:

- The untouched historical source also fails `ModTestAllure.begin()` with network
  enabled. Its pinned mod URL returns HTTP 404. The candidate's failure is not
  explained by disabled networking.
- A new save/read serialization regression fails for all three tested default
  teams before the first update on baseline, and all three pass with the AI patch.
- An explicitly configured team survives serialization on both versions; the
  serialized layout and other dummy fields remain intact in these checks.

These checks do not alter the live case's gates or replace the missing map-reopen
UI evidence. They test serialization, not an entire saved-map load. Logs, test
source, exact patch hash, environment and the original execution driver are retained.

## Runner and usability work

Each change has a PR and passing repository CI:

- [#10](https://github.com/j-cunanan/oai-gaming-hackathon/pull/10): explicit network-enabled validation; an offline baseline cannot waive online candidate failures.
- [#11](https://github.com/j-cunanan/oai-gaming-hackathon/pull/11): chronological checkpoint verification and complete input traces.
- [#12](https://github.com/j-cunanan/oai-gaming-hackathon/pull/12): dashboard actions work on custom local ports.
- [#13](https://github.com/j-cunanan/oai-gaming-hackathon/pull/13): preserve checkpoint images and allow extra exploration checkpoints.
- [#14](https://github.com/j-cunanan/oai-gaming-hackathon/pull/14): actual modifier clicks and held input; verified with real X11 events.
- [#15](https://github.com/j-cunanan/oai-gaming-hackathon/pull/15): retain unsuccessful gameplay runs and import candidate recordings with provenance.
- [#16](https://github.com/j-cunanan/oai-gaming-hackathon/pull/16): continue diagnosis from a freshly reconfirmed trigger, with inspectable source-tool logs.
- [#17](https://github.com/j-cunanan/oai-gaming-hackathon/pull/17): readable Cyrillic PDFs with bundled fonts. All six bilingual-report pages and five Weather-report pages were visually checked.
- [#18](https://github.com/j-cunanan/oai-gaming-hackathon/pull/18): freeze additional candidate checks after the unchanged trigger, such as reopening a saved map. Planning success does not count as repeated validation. Also retain the original report alongside triage and record reasoning effort. Live verification is pending.

Current checks: **150 Python tests, 8 frontend tests, and a production build pass**.
The new postcondition workflow is merged but has not yet been loaded into the
running server; active investigations are allowed to finish first.

## Local handoff

REPRO is at [127.0.0.1:8001](http://127.0.0.1:8001/). Port 8000 belongs to another
local project and was left alone. Existing case data and credentials are retained
locally; no credentials are in the committed evidence.

All live API investigations so far used `gpt-5.6-terra` at medium reasoning, bounded
by 120 model calls, 200 actions and 3,600 seconds per job. Counts accumulate across
continuations on the same case. New configurations and final totals will be
recorded here when the remaining runs finish. No game patch has been published
upstream and no teammate was messaged.
