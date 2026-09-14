# Historical benchmark protocol

Preparation and evaluation may access GitHub. Investigation, baseline tests, candidate build/tests and gameplay replays cannot. Model-visible data is limited to the player report, supplied evidence, pre-fix source, prepared dependencies and game runtime. Record the validation network policy with each result; historical network-enabled reruns do not overwrite the original offline outcomes or qualify as offline baseline evidence.

The application also supports explicitly opted-in network-enabled candidate validation (`REPRO_VALIDATION_NETWORK=true`) for operational use. Those results are outside this offline protocol, must pass all candidate tests without a baseline-failure waiver, and must be labeled with their network mode. The default remains offline; baseline suites and game replays always remain offline.

The default checkout is **depth one at the exact pre-fix SHA**. This intentionally trades ownership/history analysis for small, auditable preparation. There is no future history, remote, shared object database or evaluator mount. A separate ancestor-only bundle exporter is available and tested.

Manifests live in `benchmarks/manifests/`. Only their `input` fields become `CaseInput`. Source URLs, fix commits and changed files belong to evaluator metadata. Never include the full manifest in a model prompt or game-container mount. Public report bodies may have been edited after submission; a fetched body is a snapshot, not proof that every word existed at initial reporting. Disclose that limitation until issue revision history is captured.

Each attempted case must retain its outcome, including failed preparation and unsuccessful investigation. UI run counts are descriptive. They are not precision/recall, localization accuracy or an end-to-end resolution rate without evaluator labels and an explicit denominator.

## First candidate

`MD-001` references [Mindustry issue 12647](https://github.com/Anuken/Mindustry/issues/12647), reported September 12, 2026. The report says that two Weather buttons appear in map rules and gives a short UI navigation hint. It requires no save or mods. The report's platform is Windows; the recorded evaluation used Linux under Docker on Apple Silicon. The [evidence package](evidence/MD-001/README.md) preserves the actual results and failed attempts.

The pre-fix source is `a5c178ae5abcc630613c233e0afbb361021d3828`. The evaluator knows the later human fix; the investigation receives neither that fix nor its changed-file list. This is a selected, simple visual case, not a representative sample of all game bugs.

## Scoring requirements

- Verification requires runtime evidence and independent repeated checks. A source-code match is not reproduction.
- Action reduction combines a deletion-only proposal and bounded delta debugging, followed by fresh confirmation. Do not call it globally minimal.
- Localization compares ranked exact file paths to evaluator ground truth only after investigation.
- A replay regression should observe the symptom on the retained pre-fix build and demonstrate its absence in the correct target state on the candidate build.
- A validated candidate requires a patch and all five required gates. Every recorded check must be `pass` or `baseline_failed`; `fail`, `not_run` and `error` block approval. `baseline_failed` is an accepted pre-existing failure, not a clean pass.
- The existing-tests baseline-differential gate requires an actual recorded offline suite run on untouched source. A nonzero candidate exit is accepted only when its confidently parsed, nonempty failing-test set equals or is a subset of the baseline failing-test set. Any candidate-only failure blocks approval, even if another baseline failure disappears. Matching identifiers do not establish identical exception causes or prove those tests are healthy.
- Baseline records are cached per case, keyed by commit SHA. The source revision, exact test command, running worker image digest, platform and parser version must match. Validation re-reads and hashes the stored baseline log and checks its parsed identifiers against the record. Missing, incomplete, stale, corrupt or unparseable evidence blocks differential acceptance. No exception-string heuristic, assertion skip or network exception grants acceptance. Both logs and the named failures remain inspectable.
- The parser currently supports a complete single-task Gradle/JUnit console report with consistent failure counts and a terminal build marker. Truncated, duplicate, interleaved or unsupported reports fail closed. Passing test commands still produce `pass`.
- A clean launch smoke check is narrower than representative gameplay smoke testing.
- Include negative/non-bug cases before reporting verification accuracy.

No evaluation results are populated by the unit tests.

`uv run repro prepare CASE_ID --refresh-baseline-tests` forces a new baseline suite run before patching; successful cached records otherwise retain their timestamp. Interrupted and unparseable attempts are explicitly recorded and are not reusable. Gradle baseline and candidate runs use `--rerun-tasks --no-build-cache --console=plain` with the adapter's full offline test command. Preparation compiles test dependencies without running Mindustry assertions online.

Existing patched cases without qualifying baseline records stay blocked on failing tests. Prepare and investigate a fresh case to obtain new evidence; the CLI deliberately cannot run baseline assertions on a patched checkout. Source/image/command identity does not capture every mutable dependency or flaky test condition, so refresh when those conditions change. No time-based cache expiry or cross-case cache is implemented.
