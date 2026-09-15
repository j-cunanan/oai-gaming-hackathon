# Architecture and handoff

The application is a Python package plus a web dashboard. `repro/api.py` exposes the same manager used by `repro/cli.py`. `Store` persists JSON case snapshots and ordered events in SQLite, and stores content-hashed evidence outside the game sandbox.

The [reproduction-method figure](figures/reproduction-method/README.md) explains adaptive exploration, fresh replay verification and the retained regression, with PNG, SVG and editable slide versions.

## Trust and execution boundaries

1. Preparation downloads an exact game revision into a disposable directory. The default is a depth-one snapshot retaining the genuine upstream SHA; there are no future objects, refs or remotes. `isolate_history` also supports an ancestor-only bundle when full historical ownership analysis is needed. Tests check that an actual future commit cannot be read.
2. A container with temporary network access downloads dependencies and compiles the game. No user credentials, host home directory or Docker socket are mounted. Preparation is a distinct, non-benchmark phase.
3. The container is replaced with one using `--network none`, dropped capabilities, no privilege escalation and CPU/memory/PID limits. The model controller runs outside it. The model has only explicitly implemented tools; it has no web search, GitHub connector or access to the evaluator.
4. Every input produces screenshot/log/process evidence. Resets recreate the worker and profile. The API key and database never enter the game workspace.
5. Reproduction is verified independently and repeated before source localization and patching. `repro.yaml` is the executable replay regression. Candidate edits occur only in the disposable repository.
6. Baseline assertions run offline; candidate build/tests use a fresh offline container by default. Mindustry preparation compiles test dependencies while networking is available; the actual baseline suite runs afterward on verified untouched source. Offline candidate failures are compared against matching baseline evidence. An explicit `REPRO_VALIDATION_NETWORK=true` enables only candidate build/test networking; these runs must pass outright and cannot waive failures using an offline baseline. Gameplay investigation and replay containers remain offline. Local approval is a handoff decision; it cannot publish to an upstream game.

Treat these containers as a practical local hackathon isolation boundary, not a hardened multi-tenant execution service. Run the API on loopback. Do not expose a Docker-controlling backend directly on the public internet. A production service needs authentication, separate workers and durable job leases.

## API and model implementation

The implementation uses the Responses API directly to keep the first control loop small. It does not currently use Agents SDK handoffs/tracing or the native ComputerTool class. Screenshot-aware function tools provide real computer actions through our own driver. Pydantic schemas constrain model output, and the application checks it before execution.

Official documentation checked during implementation:

- [GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna): the default choice from the requested models, supporting Responses, structured output, image input and function calling.
- [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra): the requested alternative, used for the successful historical visual reproduction.
- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs): Python `responses.parse` with `text_format`.
- [Function calling](https://developers.openai.com/api/docs/guides/function-calling): preserve response output items, return matching `call_id` outputs, and pass images with tool results.
- [Computer use](https://developers.openai.com/api/docs/guides/tools-computer-use): retain the execution environment and return fresh screenshots at native coordinates.

`store=False` is set on model calls. Model reasoning items remain only in the active API conversation; the UI receives concise hypotheses, observations and tool events, not private reasoning. Call/time budgets apply to each dispatched job; a case's displayed usage accumulates across investigation, manual replay, reduction and validation jobs. Token usage is measured, but dollar estimates are omitted until a dated price table is configured.

The investigator cannot redefine the success condition: verification uses the triaged player symptom. A rejected visual confirmation is returned to the investigator as an observation, allowing another experiment within the same budget. The reducer reserves calls for localization and validation. A budget-exhausted validation can be rerun from the saved candidate without regenerating the patch.

Reduction starts with a model-proposed subsequence of recorded actions. Indices must be unique, ordered and in range; no action can be invented or changed. A clean baseline replay decides whether to accept the proposal, then bounded delta debugging tries trailing chunks first. Any shorter result needs five fresh confirmations by default. `reduce` can refine an existing case using the retained baseline binary, invalidates checks tied to an older replay, and revalidates a candidate when the sequence changes. The proposal receives only the recorded actions and symptom, never the candidate patch or evaluator metadata.

Temporal replays use a version-2 `sequence` oracle with 2–8 distinct checkpoint labels. Labels attach to actual recorded actions, so a reduced replay preserves their identity without relying on shifted numeric indices. The recorder rejects duplicate labels within an attempt and clears them on every reset/replay. A separate model call receives the ordered checkpoint screenshots, the actual input trace through the final checkpoint, and the report-defined symptom. Inputs establish action order and navigation attempts; their effects must be visible in the images. It must positively establish the target sequence and either the defect or the correct behavior; a missing frame, wrong order, low confidence, or contradictory judgment is inconclusive. Candidate validation uses the same chronological evidence rather than a final-frame absence check. These remain model-based judgments, not deterministic ground truth. The [retained-image audit](evidence/R07-sequence-audit/README.md) records initial inconclusive judgments and the effect of adding the input trace; it does not count as new game executions.

Validation requires all five named gates, so an intermediate passing build or regression cannot be counted as an approved candidate. The existing-tests gate may earn `baseline_failed` only from a matching recorded offline failure set; it remains visibly distinct from `pass`. No upstream assertions are skipped. Network-enabled operational runs remain separate from the offline benchmark protocol and cannot reuse its failure exceptions. Offline failures and network-enabled reruns remain separate artifacts. The benchmark records attempts and distinct cases separately; cancelled refinement passes and failed replays remain in the event audit. See the [benchmark protocol](benchmark.md) for cache identity, parser limits and refresh instructions.

An explicit validation rerun snapshots the prior case and repeats the baseline gameplay gate as well as the candidate gates. The separate baseline test-suite record is cached by commit and checked for matching command, worker image digest, platform, parser and intact log evidence; it is never reconstructed from a candidate log. The previous evidence remains downloadable.

The desktop driver stays alive on one ordered JSON-lines pipe per container. Each action returns its screenshot and process state in the same response; it no longer starts two Python interpreters per input. PNG compression is reduced without changing pixels, and recorded settling times remain unchanged. A timed-out or malformed response closes the pipe to prevent a late reply from being used for another action. Every replay still recreates the container and profile.

Mindustry startup retains the eight-second minimum and additionally waits for its existing load-complete log marker, with a 45-second bound and one second for the final resize/interactive frames. This prevents the first recorded click from arriving while assets still load on an emulated CPU. First-run dialogs are never dismissed automatically. Other adapters retain their existing startup wait until they define a readiness marker.

The dashboard starts its event stream after the latest loaded event and uses new events to coalesce case snapshot and incremental activity refreshes. Artifact metadata is fetched only while the Evidence tab is open, and its list renders 50 rows at a time. Filtering still searches the complete fetched index.

Stage activity is derived from the complete durable audit by `repro/activity.py`, including records older than the 500-event SSE page. State transitions, recorded action phases, and named model purposes assign entries to the six UI stages; failures and cancellations stay with the stage that encountered them. Historical first/latest timestamps are event boundaries, not inferred active durations. New investigations explicitly record triage starting. `/api/cases/{id}/activity?after=SEQ` returns compact new entries plus stage summaries, and the dashboard merges deltas without duplicating earlier entries. Raw records are fetched only when expanded through the case-scoped `/events/{seq}` endpoint. The PDF uses the same stage mapping and UTC timestamps; the UI displays the browser's local time zone.

Patch proposals persist a concise explanation and risks alongside the selected patch artifact. Older cases recover that data from the patch event matching the exact artifact ID, so a different proposal cannot supply its justification. The dashboard presents this saved explanation, the validation evidence, and the colored source diff as separate parts of review. Info buttons explain the terminology without additional API requests.

`repro/reporting.py` builds a plain, paginated PDF from saved case data and case-scoped artifacts using ReportLab. `/api/cases/{id}/report` returns it by default; `?format=markdown` preserves the text report, and the CLI selects PDF for a `.pdf` output path. PDF rendering runs in FastAPI's thread pool so it does not block the event loop. Report generation makes no model calls, escapes user/model text, preserves failed or missing checks, and labels unavailable evidence without inventing replacements.

## Next engineering work

- Add reproducible offline fixture preparation for environments that cannot permit network access during tests.
- Expand the benchmark only after the first historical run has inspectable artifacts.
- Add save/profile installation and video extraction without modifying original uploads.
- Validate the Luanti adapter against a pinned engine revision and separately licensed content pack.
- Improve visual-oracle calibration with negative controls and deterministic instrumentation where available.
- Extend smoke tests beyond startup and add worker resumption/leases before multiple API processes.
- Add optional reviewed GitHub PR publication for target-game patches; do not confuse that with this repository's development PRs.
