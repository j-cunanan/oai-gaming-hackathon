# Historical benchmark protocol

Preparation and evaluation may access GitHub. The investigation cannot. Model-visible data is limited to the player report, supplied evidence, pre-fix source, prepared dependencies and game runtime.

The default checkout is **depth one at the exact pre-fix SHA**. This intentionally trades ownership/history analysis for small, auditable preparation. There is no future history, remote, shared object database or evaluator mount. A separate ancestor-only bundle exporter is available and tested.

Manifests live in `benchmarks/manifests/`. Only their `input` fields become `CaseInput`. Source URLs, fix commits and changed files belong to evaluator metadata. Never include the full manifest in a model prompt or game-container mount. Public report bodies may have been edited after submission; a fetched body is a snapshot, not proof that every word existed at initial reporting. Disclose that limitation until issue revision history is captured.

Each attempted case must retain its outcome, including failed preparation and unsuccessful investigation. UI run counts are descriptive. They are not precision/recall, localization accuracy or an end-to-end resolution rate without evaluator labels and an explicit denominator.

## First candidate

`MD-001` references [Mindustry issue 12647](https://github.com/Anuken/Mindustry/issues/12647), reported September 12, 2026. The report says that two Weather buttons appear in map rules and gives a short UI navigation hint. It requires no save or mods. The report's platform is Windows; the planned evaluation uses Linux, which must be disclosed.

The pre-fix source is `a5c178ae5abcc630613c233e0afbb361021d3828`. The evaluator knows the later human fix; the investigation receives neither that fix nor its changed-file list. This is a selected, simple visual case, not a representative sample of all game bugs.

## Scoring requirements

- Verification requires runtime evidence and independent repeated checks. A source-code match is not reproduction.
- Action reduction combines a deletion-only proposal and bounded delta debugging, followed by fresh confirmation. Do not call it globally minimal.
- Localization compares ranked exact file paths to evaluator ground truth only after investigation.
- A replay regression should observe the symptom on the retained pre-fix build and demonstrate its absence in the correct target state on the candidate build.
- A validated candidate requires all five required gates to exist and pass. Failed/not-run checks stay visible, including tests blocked by offline networking.
- A clean launch smoke check is narrower than representative gameplay smoke testing.
- Include negative/non-bug cases before reporting verification accuracy.

No evaluation results are populated by the unit tests.
