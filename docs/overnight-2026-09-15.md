# REPRO overnight work — September 15, 2026

Work in progress. The authorized window ends at **07:04 JST / 22:04 UTC**.
This note separates fresh REPRO investigations, operator-assisted attempts,
retained-image audits, and supplemental evaluator checks. It is not a claim of
complete benchmark coverage.

The strongest fresh result so far is **deleted data patches returning after a map
reopens**. An explicitly evidence-guided Terra investigation reproduced the bug,
traced the cause, generated a one-line patch and passed **all five validation
gates**, including 276/276 upstream tests and five fresh correct candidate replays.
The original report-only attempt and its incomplete evidence remain separate.

| Candidate | Recorded result so far | Presentation value and limit |
| --- | --- | --- |
| [Target Dummy save crash](evidence/overnight-2026-09-15/md-12579-terra-overnight-01/result.json) | 15 actions reproduced 5/5; reduced 12-action trigger reproduced 5/5, then reconfirmed 5/5 on the upgraded worker. Fresh Terra source diagnosis and patch retained. | Clear creation → save → crash story. Three gates pass. The original candidate replay avoided the crash 5/5, but only 1/5 visual judgments established the full expected state; reopening was not recorded. One upstream fixture download also returns 404. |
| [Deleted data patch returns](evidence/overnight-2026-09-15/md-12620-terra-overnight-02/README.md) | Fresh evidence-guided run: 31 actions reproduced 5/5; reduced 30 actions reproduced 5/5. AI patch passed all five gates, 276/276 tests with no skips, and 5/5 correct candidate replays. | Recommended current demo: delete → save → reopen → unwanted content returns. The first report-only attempt remains at 3/5; assistance selected the necessary save evidence and supplied no fix. |
| [Unit loss on payload conveyor](evidence/overnight-2026-09-15/md-12565-terra-overnight-01/result.json) | Initial probe and fresh retry could not obtain the required unit. A later setup-guided attempt also stopped before entry/transport was tested. | Potentially stronger gameplay demo, currently inconclusive. Normal transformation into a payload is not evidence of loss. |
| [Ghost generator after explosion](evidence/overnight-2026-09-15/md-12603-terra-overnight-01/result.json) | The fueled-generator/explosion setup was not reached. | Visually interesting report, but no runtime qualification from these attempts. |
| [Derelict conveyor loses cargo on reload](../benchmarks/candidates/MD-candidate-12354.yaml) | First preparation failed because JitPack lacked the pinned Arc dependency. The exact required Arc revision has now been prepared from source for a retry. | A clear cargo-loss story if reproduced. No runtime result yet. |
| [Data Patches & Assets lifecycle crash](../benchmarks/candidates/MD-candidate-12652-fixture.yaml) | The original reporter map is retained, hashed and registered for identical restoration on each fresh run. MAX investigation queued. | A more involved original-map scenario. File inspection is not runtime qualification. |

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
- [#19](https://github.com/j-cunanan/oai-gaming-hackathon/pull/19): retain the first crash candidate, incomplete data-patch run, setup-guided unit attempt and supplemental controls. All referenced logs are committed; imports were checked from a fresh Git archive.
- [#20](https://github.com/j-cunanan/oai-gaming-hackathon/pull/20): configurable bounded model outputs and early skips for reduction proposals that drop or reorder required checkpoints.
- [#21](https://github.com/j-cunanan/oai-gaming-hackathon/pull/21): original `.msav` fixtures restored before each fresh run, with UI/PDF input provenance and the unchanged reporter attachment for #12652.

Current checks: **167 Python tests, 8 frontend tests, and a production build pass**.
The new postcondition workflow is loaded. A Target Dummy validation rerun started
through the dashboard; the original blocked result is frozen separately.

## Local handoff

REPRO is at [127.0.0.1:8001](http://127.0.0.1:8001/). Port 8000 belongs to another
local project and was left alone. Existing case data and credentials are retained
locally; no credentials are in the committed evidence.

Completed API investigations so far used `gpt-5.6-terra` at medium reasoning.
After the data-patch run finished, the server switched to **max reasoning** and a
16,000-token response allowance. Jobs remain bounded by 120 model calls, 200
actions and 3,600 seconds. Counts accumulate across continuations on the same
case. Target Dummy revalidation, the original-map investigation and the cargo
retry are queued in that order. Final outcomes will be recorded when they finish.
No game patch has been published upstream and no teammate was messaged.
