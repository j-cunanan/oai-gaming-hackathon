# REPRO overnight work — September 15, 2026

Morning handoff for the authorized **00:04–07:04 JST** work window
(September 14, **15:04–22:04 UTC**).
This note separates fresh REPRO investigations, operator-assisted attempts,
retained-image audits, and supplemental evaluator checks. It is not a claim of
complete benchmark coverage.

The strongest fresh result is **deleted data patches returning after a map
reopens**. An explicitly evidence-guided Terra investigation reproduced the bug,
traced the cause, generated a one-line patch and passed **all five validation
gates**, including 276/276 upstream tests and five fresh correct candidate replays.
The original report-only attempt and its incomplete evidence remain separate.

Open the [recorded before/after walkthrough](demos/datapatch-2026-09-15/index.html)
or the [eight-page REPRO PDF](demos/datapatch-2026-09-15/repro-report.pdf).
A [short demo script](demos/datapatch-2026-09-15/demo-script.md) explains what to show and which claims the evidence supports.
The walkthrough selects eight real checkpoints from one baseline and one
candidate replay; its playback is an excerpt, not live video or a new execution.

| Candidate | Recorded result | Presentation value and limit |
| --- | --- | --- |
| [Deleted data patch returns](evidence/overnight-2026-09-15/md-12620-terra-overnight-02/README.md) | Fresh evidence-guided run: 31 actions reproduced 5/5; reduced 30 actions reproduced 5/5. AI patch passed all five gates, 276/276 tests with no skips, and 5/5 correct candidate replays. | Recommended current demo: delete → save → reopen → unwanted content returns. The first report-only attempt remains at 3/5; assistance selected the necessary save evidence and supplied no fix. |
| [Target Dummy save crash](evidence/overnight-2026-09-15/md-12579-terra-postconditions-02/README.md) | Fresh baseline crash 5/5; the AI candidate now saves and reopens the map with the dummy retained in 5/5 fresh runs. Each uses the unchanged 12-action trigger plus 12 separately frozen verification actions. | Clear creation → save → crash story. Four gates pass; the only failing gate is an upstream test's unavailable archive (HTTP 404). The earlier incomplete replay and planner failure remain separate. |
| [Color input changes on readback](evidence/overnight-2026-09-15/md-12623-terra-replay-02-final/README.md) | Fresh supplied-trace qualification: 29 actions reproduced 5/5. The AI patch built and passed 276/276 existing tests, but still showed the defect in all five candidate replays. | Useful reproduction and rejected-fix demonstration: enter `ff0300`, confirm, reopen and see `ff0200ff`. The supplied trace and corrected checkpoint selection are explicitly operator-assisted. It tests both pickers and a placed-and-picked wall, not every reported value. |
| [Unit loss on payload conveyor](evidence/overnight-2026-09-15/md-12565-terra-paced-06/README.md) | A later retained-image review was positive, but the first supplied trace produced two inconclusive fresh verdicts and a third verifier timeout. The final calibrated trace recovered the intended zoom and unit selection, but still failed to show entry: 0/1 fresh confirmations. | Not qualified. A real scroll-delivery mismatch was identified and fixed, but that runner fix did not establish the gameplay bug. Retained-image review is not a fresh reproduction. |
| [Ghost generator after explosion](evidence/overnight-2026-09-15/md-12603-terra-prepared-03/README.md) | The prepared-scene run reached a Water/Blast-fueled Steam Generator producing 132.0 power and later nonfatal health loss. It did not establish the required pickup, conveyor transport, explosion and zero-health redeployment. | Visually interesting report, still inconclusive. Original report-only, video-guided and prepared-scene attempts are recorded separately. |
| [Derelict conveyor loses cargo on reload](evidence/overnight-2026-09-15/md-12354-terra-fixture-02/README.md) | The original-map attempt identified a Derelict conveyor and nearby World Processor, then saved and reopened. Both remained visible, but it did not establish that the object was carried payload. | Inconclusive. The test did not qualify the exact transport-persistence precondition; it does not disprove the reported bug. The earlier report-only setup failure remains separate. |
| [Data Patches & Assets lifecycle crash](evidence/overnight-2026-09-15/md-12652-terra-max-01/README.md) | MAX imported the unchanged reporter map, entered in-game editing, changed a tile, returned to the editor and visited the asset tabs before closing. No crash was observed. | Original-map input is runtime-qualified, but this tested flow did not reproduce the reported bug. This is not five negative confirmations or proof the bug is absent. |

The earlier Weather case remains available as a simpler reference with all five
recorded gates passing. It predates this overnight run and is not counted as a
new discovery or fresh overnight fix.

**Choose the data-patch case for the primary demo.** Keep Target Dummy as the
clearer crash example, explaining its remaining test-fixture blocker. Use color
as the example of verification rejecting a plausible patch. The payload reports
are follow-up research candidates, not ready-to-present confirmed results.

There are **17 new case IDs across seven distinct player reports**. Retries,
assisted variants and continued validation are not new bugs. Target Dummy's
multiple snapshots and the color case's checkpoint correction each share one
case ID; their cumulative usage must not be summed across snapshots. The
[attempt ledger](evidence/overnight-2026-09-15/attempts.json) records final local
states, usage and evidence links. This curated, adaptive run does not estimate
general bug-fixing accuracy. Native input probes, retained-image audits and
evaluator-authored controls are listed separately from fresh investigations.

## Alignment with Jayson

Main was fetched before work and checked again during the run. Jayson's evidence
import/provenance work (#9) and baseline-differential validation (#5) are retained.
His three human-fixed qualification controls establish the selected historical
bugs and environment, not a fresh AI-generated fix. No later code-mining records
were located in the fetched branches beyond the existing qualification and
MD-001 records. That describes the inspected repository, not unpushed work.
The final remote check found no open PRs or newer teammate commits. The supplied
build-context Markdown is already on main at `docs/REPRO_FULL_BUILD_CONTEXT.md`;
its bytes were checked against the original downloaded document.

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
- [#18](https://github.com/j-cunanan/oai-gaming-hackathon/pull/18): freeze additional candidate checks after the unchanged trigger, such as reopening a saved map. Planning success does not count as repeated validation. Also retain the original report alongside triage and record reasoning effort. The later Target Dummy run verifies the full save/reopen workflow.
- [#19](https://github.com/j-cunanan/oai-gaming-hackathon/pull/19): retain the first crash candidate, incomplete data-patch run, setup-guided unit attempt and supplemental controls. All referenced logs are committed; imports were checked from a fresh Git archive.
- [#20](https://github.com/j-cunanan/oai-gaming-hackathon/pull/20): configurable bounded model outputs and early skips for reduction proposals that drop or reorder required checkpoints.
- [#21](https://github.com/j-cunanan/oai-gaming-hackathon/pull/21): original `.msav` fixtures restored before each fresh run, with UI/PDF input provenance and the unchanged reporter attachment for #12652.
- [#22](https://github.com/j-cunanan/oai-gaming-hackathon/pull/22): freeze the fully validated fresh data-patch investigation and its 276-test suite evidence.
- [#23](https://github.com/j-cunanan/oai-gaming-hackathon/pull/23): identify source-review notes by their scope, allow a longer bounded postcondition planner and retain an unavailable check when planning exhausts its budget.
- [#24](https://github.com/j-cunanan/oai-gaming-hackathon/pull/24): package the recorded data-patch walkthrough and preserve later incomplete investigation results.
- [#25](https://github.com/j-cunanan/oai-gaming-hackathon/pull/25): supply unchanged original cargo test maps and explicit observations from the generator report's video.
- [#26](https://github.com/j-cunanan/oai-gaming-hackathon/pull/26): provide audited healthy setup saves for the unit and generator reports, with their origin labeled separately from original player attachments. Save/reload precondition checks are not bug reproductions.

- [#27](https://github.com/j-cunanan/oai-gaming-hackathon/pull/27): retain the complete Target Dummy save/reopen result and later inconclusive attempts; show current candidate outcomes in PDFs with reviewed, hash-bound report artifacts.

- [#28](https://github.com/j-cunanan/oai-gaming-hackathon/pull/28): bounded desktop action sequences preserve ordinary replay evidence and stop after process exit. A real X11 probe verifies matching inputs on fresh replay; no AI speedup ratio is claimed.
- [#29](https://github.com/j-cunanan/oai-gaming-hackathon/pull/29): preserve unverified trigger proposals before independent checks, allow longer bounded MAX requests, disable automatic retries and retain the prepared-unit timeout honestly.

- [#30](https://github.com/j-cunanan/oai-gaming-hackathon/pull/30): retain later prepared-scene attempts, a separate image audit and the unsuccessful fresh qualification without merging their claims.
- [#31](https://github.com/j-cunanan/oai-gaming-hackathon/pull/31): pace wheel detents to avoid collapsed camera updates. A real Arc SDL comparison and nine production-RPC samples verify delivery; old recordings retain their original provenance.

Current checks: **189 Python tests, 8 frontend tests, and a production build pass**.
The final four exports were restored into isolated stores from a fresh Git
archive, verifying **358 artifact files** and retaining all 25 referenced logs.
Driver, test-audit, PDF and walkthrough checksums match. All eight pages of the
final color PDF were visually reviewed. In the live dashboard, data-patch handoff
is enabled; the color candidate's failed replay disables its handoff button.
The original blocked Target Dummy result and later failed planner snapshot are
frozen separately. The longer planner completed five correct save/reopen candidate
runs. Cargo, generator and calibrated unit attempts finished without qualifying
their required gameplay transitions. The report-only color investigation
observed wrong readbacks but exhausted its final response allowance; its separate
supplied-trace qualification is recorded above. No incomplete response was
accepted as a finished replay or patch.

## Local handoff

REPRO is at [127.0.0.1:8001](http://127.0.0.1:8001/). Port 8000 belongs to another
local project and was left alone. Existing case data and credentials are retained
locally; no credentials are in the committed evidence.
The docs-only preview serves the [recorded demo](http://127.0.0.1:8766/demos/datapatch-2026-09-15/index.html).
The dashboard's proposed-patch view was checked against the real data-patch
record: the case identity, timed stages, logs, rationale, diff, five passing checks
and PDF link are visible. Its handoff button is enabled and awaits human review.

The fresh completed data-patch fix used `gpt-5.6-terra` at medium reasoning.
After the data-patch run finished, the server switched to **max reasoning** and a
16,000-token response allowance. API jobs allow up to 120 model calls, 200
**discovery actions** and 3,600 seconds. Replay/validation actions are recorded
separately and are not capped by that discovery-action number. Requests use a
300-second timeout with automatic retries disabled after PR29.

Standalone supplied-trace qualifications used explicit exceptions: up to 90
minutes for the first unit qualification, 65 minutes for its scroll-calibrated
variant, and a 450-second request timeout. The final color qualification allowed
55 minutes of active work and 24,000 output tokens per response; its continuation
retained the unused portion of that original time allowance. Every run stayed
inside the overall overnight deadline. Case usage accumulates across
continuations; the model-call cap is enforced per model session, not across the
lifetime of a continued case. Failed requests can have unavailable token usage,
so recorded tokens are not a billing reconciliation.

All paid investigations are finished and the overnight heartbeat is paused.
The local app and docs preview remain available.
No game patch has been published upstream and no teammate was messaged.
