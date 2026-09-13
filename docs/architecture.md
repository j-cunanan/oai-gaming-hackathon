# Architecture and handoff

The application is a Python package plus a web dashboard. `repro/api.py` exposes the same manager used by `repro/cli.py`. `Store` persists JSON case snapshots and ordered events in SQLite, and stores content-hashed evidence outside the game sandbox.

## Trust and execution boundaries

1. Preparation downloads an exact game revision into a disposable directory. The default is a depth-one snapshot retaining the genuine upstream SHA; there are no future objects, refs or remotes. `isolate_history` also supports an ancestor-only bundle when full historical ownership analysis is needed. Tests check that an actual future commit cannot be read.
2. A container with temporary network access downloads dependencies and compiles the game. No user credentials, host home directory or Docker socket are mounted. Preparation is a distinct, non-benchmark phase.
3. The container is replaced with one using `--network none`, dropped capabilities, no privilege escalation and CPU/memory/PID limits. The model controller runs outside it. The model has only explicitly implemented tools; it has no web search, GitHub connector or access to the evaluator.
4. Every input produces screenshot/log/process evidence. Resets recreate the worker and profile. The API key and database never enter the game workspace.
5. Reproduction is verified independently and repeated before source localization and patching. `repro.yaml` is the executable replay regression. Candidate edits occur only in the disposable repository.
6. Validation separately records compilation, existing tests, expected-state replay and startup smoke results. Local approval is a handoff decision; it cannot publish to an upstream game.

Treat these containers as a practical local hackathon isolation boundary, not a hardened multi-tenant execution service. Run the API on loopback. Do not expose a Docker-controlling backend directly on the public internet. A production service needs authentication, separate workers and durable job leases.

## API and model implementation

The implementation uses the Responses API directly to keep the first control loop small. It does not currently use Agents SDK handoffs/tracing or the native ComputerTool class. Screenshot-aware function tools provide real computer actions through our own driver. Pydantic schemas constrain model output, and the application checks it before execution.

Official documentation checked during implementation:

- [GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna): the explicitly requested default, supporting Responses, structured output, image input and function calling.
- [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra): the requested alternative, used for the successful historical visual reproduction.
- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs): Python `responses.parse` with `text_format`.
- [Function calling](https://developers.openai.com/api/docs/guides/function-calling): preserve response output items, return matching `call_id` outputs, and pass images with tool results.
- [Computer use](https://developers.openai.com/api/docs/guides/tools-computer-use): retain the execution environment and return fresh screenshots at native coordinates.

`store=False` is set on model calls. Model reasoning items remain only in the active API conversation; the UI receives concise hypotheses, observations and tool events, not private reasoning. Token usage is measured, but dollar estimates are omitted until a dated price table is configured.

The investigator cannot redefine the success condition: verification uses the triaged player symptom. A rejected visual confirmation is returned to the investigator as an observation, allowing another experiment within the same budget. The reducer reserves calls for localization and validation. A budget-exhausted validation can be rerun from the saved candidate without regenerating the patch.

Reduction starts with a model-proposed subsequence of recorded actions. Indices must be unique, ordered and in range; no action can be invented or changed. A clean baseline replay decides whether to accept the proposal, then bounded delta debugging tries trailing chunks first. Any shorter result needs five fresh confirmations by default. `reduce` can refine an existing case using the retained baseline binary, invalidates checks tied to an older replay, and revalidates a candidate when the sequence changes. The proposal receives only the recorded actions and symptom, never the candidate patch or evaluator metadata.

Validation requires all five named gates, so an intermediate passing build or regression cannot be counted as an approved candidate. Upstream tests that require internet access remain failed in the offline worker. The benchmark records attempts and distinct cases separately; cancelled refinement passes and failed replays remain in the event audit.

## Next engineering work

- Expand the benchmark only after the first historical run has inspectable artifacts.
- Add save/profile installation and video extraction without modifying original uploads.
- Validate the Luanti adapter against a pinned engine revision and separately licensed content pack.
- Improve visual-oracle calibration with negative controls and deterministic instrumentation where available.
- Extend smoke tests beyond startup and add worker resumption/leases before multiple API processes.
- Add optional reviewed GitHub PR publication for target-game patches; do not confuse that with this repository's development PRs.
