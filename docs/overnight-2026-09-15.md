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

Open the [recorded before/after walkthrough](demos/datapatch-2026-09-15/index.html)
or the [eight-page REPRO PDF](demos/datapatch-2026-09-15/repro-report.pdf).
The walkthrough selects eight real checkpoints from one baseline and one
candidate replay; its playback is an excerpt, not live video or a new execution.

| Candidate | Recorded result so far | Presentation value and limit |
| --- | --- | --- |
| [Target Dummy save crash](evidence/overnight-2026-09-15/md-12579-terra-postconditions-02/README.md) | Fresh baseline crash 5/5; the AI candidate now saves and reopens the map with the dummy retained in 5/5 fresh runs. Each uses the unchanged 12-action trigger plus 12 separately frozen verification actions. | Clear creation → save → crash story. Four gates pass; the only failing gate is an upstream test's unavailable archive (HTTP 404). The earlier incomplete replay and planner failure remain separate. |
| [Deleted data patch returns](evidence/overnight-2026-09-15/md-12620-terra-overnight-02/README.md) | Fresh evidence-guided run: 31 actions reproduced 5/5; reduced 30 actions reproduced 5/5. AI patch passed all five gates, 276/276 tests with no skips, and 5/5 correct candidate replays. | Recommended current demo: delete → save → reopen → unwanted content returns. The first report-only attempt remains at 3/5; assistance selected the necessary save evidence and supplied no fix. |
| [Unit loss on payload conveyor](evidence/overnight-2026-09-15/md-12565-terra-overnight-01/result.json) | Initial probe and fresh retry could not obtain the required unit. A later setup-guided attempt also stopped before entry/transport was tested. | Potentially stronger gameplay demo, currently inconclusive. Normal transformation into a payload is not evidence of loss. |
| [Ghost generator after explosion](evidence/overnight-2026-09-15/md-12603-terra-video-02/README.md) | Neither the original attempt nor the later video-guided MAX attempt completed the required fueled-generator/explosion setup. | Visually interesting report, but no runtime qualification. A separate operator-prepared healthy scene is available for a fresh assisted attempt. |
| [Derelict conveyor loses cargo on reload](evidence/overnight-2026-09-15/md-12354-terra-overnight-01/README.md) | Preparing the exact missing Arc source enabled the build. MAX created an editor scene but did not load a payload, establish Derelict ownership, or save/reload. | A clear cargo-loss story if reproduced, currently insufficient evidence. The reporter's original data-export attachment was retrieved afterward for separate analysis. |
| [Data Patches & Assets lifecycle crash](evidence/overnight-2026-09-15/md-12652-terra-max-01/README.md) | MAX imported the unchanged reporter map, entered in-game editing, changed a tile, returned to the editor and visited the asset tabs before closing. No crash was observed. | Original-map input is runtime-qualified, but this tested flow did not reproduce the reported bug. This is not five negative confirmations or proof the bug is absent. |

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

These supplemental checks do not alter the live case's gates. Their scope is
serialization; the separate UI validation below supplies the full save/reopen
evidence. Logs, test source, exact patch hash, environment and the original
execution driver are retained.

The [first MAX postcondition attempt](evidence/overnight-2026-09-15/md-12579-terra-postconditions-01/README.md)
freshly reconfirmed the crash 5/5 and built the candidate. Its separate planner
reopened a map and inspected the dummy, but reached its 24-turn limit before
returning a complete, frozen verification plan. No five candidate repetitions or
independent postcondition verdict were produced. The failed snapshot is retained;
PR23 raises the planner limit within the existing job budgets and reports an
unfinished plan as an unavailable check.

The [subsequent MAX validation](evidence/overnight-2026-09-15/md-12579-terra-postconditions-02/README.md)
completed that missing evidence: all five fresh candidate runs saved and reopened
the map and identified the retained Target Dummy with the picker. This resolves
the save/load evidence gap. The unavailable upstream test fixture still blocks
an all-five-gates result and handoff approval.

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
- [#22](https://github.com/j-cunanan/oai-gaming-hackathon/pull/22): freeze the fully validated fresh data-patch investigation and its 276-test suite evidence.
- [#23](https://github.com/j-cunanan/oai-gaming-hackathon/pull/23): identify source-review notes by their scope, allow a longer bounded postcondition planner and retain an unavailable check when planning exhausts its budget.
- [#24](https://github.com/j-cunanan/oai-gaming-hackathon/pull/24): package the recorded data-patch walkthrough and preserve later incomplete investigation results.
- [#25](https://github.com/j-cunanan/oai-gaming-hackathon/pull/25): supply unchanged original cargo test maps and explicit observations from the generator report's video.
- [#26](https://github.com/j-cunanan/oai-gaming-hackathon/pull/26): provide audited healthy setup saves for the unit and generator reports, with their origin labeled separately from original player attachments. Save/reload precondition checks are not bug reproductions.

Current checks: **170 Python tests, 8 frontend tests, and a production build pass**.
The original blocked Target Dummy result and later failed planner snapshot are
frozen separately. The longer planner completed five correct save/reopen candidate
runs. The original-map cargo variant ended inconclusively because carried-payload identity remained unverified. Fresh prepared-scene unit and generator investigations are now queued, with the unit run first.

## Local handoff

REPRO is at [127.0.0.1:8001](http://127.0.0.1:8001/). Port 8000 belongs to another
local project and was left alone. Existing case data and credentials are retained
locally; no credentials are in the committed evidence.

The fresh completed data-patch fix used `gpt-5.6-terra` at medium reasoning.
After the data-patch run finished, the server switched to **max reasoning** and a
16,000-token response allowance. Jobs remain bounded by 120 model calls, 200
actions and 3,600 seconds. Counts accumulate across continuations on the same
case. The first Target Dummy MAX revalidation and original-map investigation have
finished; the original cargo attempt also ended without reaching the necessary
setup. Target Dummy's second MAX validation now passes the full save/reopen check
5/5. The generator video-guided attempt ended before its required damage/transport
sequence. The original-map cargo variant ended inconclusively: its observed object remained after reopen, but it was not established as carried payload. Fresh investigations using the separately labeled healthy scenes are now queued, with the unit run first.
Final outcomes will be recorded when they finish.
No game patch has been published upstream and no teammate was messaged.
