# REPRO — Autonomous BugOps for Games

## Authoritative Build Context / Engineering Specification

**Hackathon:** Tokyo AI × OpenAI 100-Hour Game Builder Challenge  
**Track:** Track 2 — Build a better way to make games  
**Working project title:** **REPRO — Autonomous BugOps for Games**  
**Tagline:** **From vague player report to verified reproduction, localized root cause, regression test, and reviewable patch.**

This document is intended to be pasted directly into Codex, Claude Code, or another engineering agent.

Treat this document as the product specification.

Do **not** silently simplify the project into:
- a bug-report summarizer,
- a generic coding agent,
- a chatbot over a codebase,
- a normal CI/CD workflow,
- an autonomous gameplay QA bot,
- a GitHub issue classifier,
- or an LLM-generated “how to fix this” answer.

The intended system is substantially more ambitious.

---

# 1. Hackathon context

Track 2 asks teams to build an AI-powered tool that meaningfully improves the way games are developed, tested, localized, operated, or distributed. The organizers specifically state that they want meaningful workflow changes rather than merely adding an AI feature to an existing tool.

Judging weights:

- **Meaningful use of OpenAI technologies — 30%**
- **Originality — 25%**
- **Playability / Utility — 25%**
- **Execution and craft — 20%**

The organizers also explicitly say that using more OpenAI products is not inherently better; the technologies should be appropriate and meaningfully used.

Teams began from a blank repository and have 100 build hours.

Do not use proprietary game characters, assets, trademarks, music, etc. without permission.

For that reason, the final evaluation/demo should use properly licensed open-source games rather than Valorant, Ghost of Tsushima, etc.

---

# 2. Submission requirements

Final submission requires:

- Team name
- Representative email
- All team members
- Challenge track
- Project title
- **Required 1-minute demo video**
- Optional working demo URL
- Optional code repository URL
- Up to 200 words: project description
- Up to 200 words: meaningful use of OpenAI tools
- Up to 200 words: originality
- Up to 200 words: playability / utility
- Up to 200 words: execution and craft
- Up to 200 words: pre-existing code, open-source components, datasets and third-party tools + licenses

Latest valid submission before deadline replaces previous submission.

Placeholders:

**Team name:** `<TEAM_NAME>`  
**Representative:** `<REPRESENTATIVE_EMAIL>`  
**Members:** Ujwal / Alice / Kushal / NoS — replace with required submission names.

---

# 3. The problem

Game debugging has a highly measurable bottleneck before an engineer can even begin fixing a bug.

A 2026 peer-reviewed study, **“Identifying Video Game Debugging Bottlenecks: An Industry Perspective”** by Carlos Pinto Gomez and Fabio Petrillo, observed debugging sessions from 20 experienced professional game developers.

It found:

- **35.1% of observed debugging time was spent reproducing bugs locally**
- **36.6% was spent inspecting game artifacts**

These were the two dominant measured debugging activities.

Source: GAS 2026 / ACM-IEEE Games and Software Engineering, DOI `10.1145/3786171.3788375`.

That means REPRO targets the activities representing **71.7% of the observed debugging process in that study**.

Important wording:

Do **not** claim:

> “REPRO eliminates 71.7% of debugging.”

That has not been proven.

Correct claim:

> “REPRO targets the two activities that accounted for 71.7% of observed debugging time in a recent industry study.”

The primary wedge is even cleaner:

> **Game developers spent 35.1% of observed debugging time simply reproducing bugs locally. We automate that phase and continue through localization, regression testing and candidate remediation.**

---

# 4. Real-world reporting problem

Actual bug reports are often bad.

Players submit things like:

> “game crashes when I go to Overgrowth”

or:

> “background suddenly black”

or:

> “save doesn't import”

with incomplete reproduction steps, uncertain platform conditions, missing logs, ambiguous state, or no understanding of which subsystem caused the problem.

Mindustry's public tracker contains exactly this style of report. For example, issue #9913 reports a crash entering Overgrowth with essentially no useful setup information beyond what the player remembers.

Luanti's tracker even contains a 2026 feature request specifically describing how ordinary players may encounter bugs but not know where/how to report them and how it is difficult to get actionable information to the relevant creators.

This is the gap REPRO fills.

---

# 5. Product thesis

## Current workflow

A player reports:

> “Sometimes my quest item disappears when I die.”

A developer must manually:

1. understand what the player means,
2. collect missing context,
3. determine whether this is really a bug,
4. discover the relevant state/setup,
5. reproduce it,
6. reproduce it consistently,
7. reduce irrelevant actions,
8. inspect screenshots/logs/save data,
9. search the codebase,
10. determine the responsible subsystem,
11. determine which developer/team owns it,
12. reason about root cause,
13. create a regression test,
14. design a fix,
15. implement it,
16. rerun reproduction,
17. ensure nothing else broke,
18. write up the engineering ticket/PR.

## REPRO workflow

The developer provides the player report and repository.

REPRO performs:

**raw report / video / logs / save**  
→ normalize evidence  
→ classify + deduplicate  
→ prepare historical/current build  
→ autonomously operate game  
→ generate hypotheses  
→ run experiments  
→ verify the symptom  
→ reproduce consistently  
→ minimize reproduction  
→ inspect logs/state/code  
→ rank responsible files/functions  
→ infer subsystem/owners  
→ generate regression test  
→ propose candidate patch  
→ rebuild  
→ replay reproduction  
→ run regression test  
→ produce reviewable engineering report  
→ **human approves the code change**

The human remains in the loop before a patch becomes a real repository change.

---

# 6. Core value proposition

The product is:

> **An autonomous bug-operations engineer for game studios.**

Input:

> messy evidence from a player/tester.

Output:

> an engineering-ready incident with empirical proof.

The final artifact should answer:

### Is it real?

**Verified / Not reproduced / Insufficient evidence**

### How do I reproduce it?

Provide a deterministic minimal sequence and replay.

### How reliably?

Example:

**10 / 10 reproductions**

### Where is it?

Example:

1. `InventoryPersistence.java::serializeState()` — 0.91
2. `PlayerDeathHandler.java::onDeath()` — 0.78
3. `InventoryFragment.java::close()` — 0.44

### Why does it happen?

Evidence-backed causal explanation.

### Who owns it?

CODEOWNERS if available; otherwise historical ownership/contributor evidence.

### How do we prevent regression?

Executable regression test or replay test.

### How might we fix it?

Reviewable candidate diff.

### Did the proposed fix work?

Rebuild + replay + regression tests.

---

# 7. The key distinction from CI/CD

This question will absolutely come up.

## CI/CD

CI/CD starts from existing machine-readable engineering knowledge:

> “Here are tests humans already wrote. Execute them after this commit.”

## REPRO

REPRO starts from ambiguous human evidence:

> “A player says the game sometimes crashes after entering Overgrowth.”

The system must discover:

- what state matters,
- whether the issue exists,
- how to reproduce it,
- which actions are irrelevant,
- which part of the code is responsible,
- what regression test was missing,
- and what change could fix it.

GitHub Actions may be a deployment mechanism for REPRO.

It is **not** the product.

---

# 8. The key distinction from generic autonomous game QA

Do not pitch:

> “AI plays games and discovers bugs.”

That category is broader and less differentiated.

REPRO's wedge is:

> **A bug has already surfaced in the real world. Convert noisy player evidence into a deterministic, engineering-ready resolution path.**

The starting point is not:

> “Explore the game and find anything unusual.”

It is:

> “Something strange happened. Investigate it like an engineer.”

This dramatically constrains the search space while solving a painful workflow.

---

# 9. The key distinction from generic coding agents

A normal coding agent receives:

> “Fix this bug.”

It may inspect code and edit files.

REPRO has to establish empirical grounding first.

The code agent must not be trusted to simply assume that the natural-language report corresponds to a particular implementation defect.

REPRO establishes a chain:

**claim → experiment → observation → reproducible behavior → source localization → test → patch → behavioral verification**

The game itself is part of the reasoning loop.

---

# 10. Non-negotiable demo principle

The main proof must NOT be:

> “We created our own toy game and inserted 20 artificial bugs.”

Toy bugs may be used internally for harness development.

They are not the main evaluation.

Primary evaluation should use:

> **historical real bugs from real open-source games with real human fixes.**

---

# 11. Primary evaluation game — Mindustry

Use:

**Repository:** `Anuken/Mindustry`

Reasons:

- Real production-quality open-source game.
- Highly active public repository.
- GPL-3.0 licensed.
- Predominantly Java.
- Desktop build available.
- Existing structured bug-report template.
- Reports commonly contain saves, crash logs, platform/build information and reproduction notes.
- Large historical issue tracker.
- Appropriate graphical environment for computer use.

Current documented desktop development setup:

- JDK 17
- run: `./gradlew desktop:run`
- build: `./gradlew desktop:dist`
- resulting desktop JAR under `desktop/build/libs/`

Mindustry documents those commands directly.

Do not package or modify upstream Mindustry into our project unless necessary.

Prefer:

- cloning it during benchmark preparation,
- checking out historical commits,
- storing case metadata,
- and running it as an external evaluation target.

---

# 12. Secondary generalization game — Luanti

Use:

**Repository:** `luanti-org/luanti`

Luanti is a free/open-source voxel game engine.

Relevant properties:

- C++17
- Linux build supported
- GUI client
- public bug tracker
- unit test mode
- many bug categories
- mods/content create interesting state interactions
- issue tracker explicitly labels unconfirmed bugs

Typical Linux build:

```bash
cmake . -DRUN_IN_PLACE=TRUE
make -j$(nproc)
./bin/luanti
```

Unit tests:

```bash
./bin/luanti --run-unittests
```

These commands are documented upstream.

Core source files identify the project under `LGPL-2.1-or-later`; verify all bundled content licenses separately before redistributing anything.

The purpose of the second game is NOT merely extra demo content.

It proves:

> **the architecture is game-adapter-based rather than hardcoded to Mindustry.**

---

# 13. Why not OpenRCT2 as primary?

OpenRCT2 is technically attractive and GPL-3.0-or-later.

However, normal gameplay requires original RollerCoaster Tycoon 2 data files, which creates unnecessary licensing/setup complexity for a hackathon demo.

Therefore:

- possible later benchmark target,
- not preferred for primary demo.

---

# 14. Historical-bug benchmark design

This is central to the project.

For each benchmark case:

1. Find a real closed issue that resulted in a real source-code fix.
2. Identify the fix commit / merged PR.
3. Determine the parent/pre-fix commit.
4. Construct an isolated repository containing history only up to that point.
5. Provide REPRO only evidence available when the bug was reported.
6. Hide the future patch.
7. Disable web access during investigation.
8. Let REPRO investigate autonomously.
9. Record its output.
10. After it finishes, compare against the actual historical fix.

This gives us a ground-truth retrospective experiment.

---

# 15. Anti-cheating / anti-leakage protocol

This is extremely important.

Otherwise judges can reasonably argue the model simply found the answer on GitHub or memorized it.

## Network

During benchmark execution:

**NO INTERNET ACCESS.**

Network is allowed during benchmark dataset preparation.

Once a benchmark case begins, the environment should contain only:

- issue evidence,
- pre-fix repository,
- build dependencies/artifacts already downloaded,
- game runtime,
- required local tools.

## Repository history

Do NOT simply checkout an old commit while leaving all future branches/tags available.

The agent could inspect them.

Build an isolated Git history containing only:

> pre-fix commit + ancestors.

Recommended approach:

- create a Git bundle containing the pre-fix commit and its ancestors,
- clone the bundle into the benchmark workspace,
- ensure there are no future refs/remotes,
- disconnect network.

Alternative:

- snapshot source plus a sanitized historical `.git` directory.

## Issue evidence

Strict benchmark input:

- original issue title/body,
- attachments available at submission,
- save file,
- screenshot/video,
- original logs,
- platform/build metadata.

Do NOT expose:

- closing PR,
- fix commit,
- later comments revealing root cause,
- maintainers' diagnosis,
- release notes announcing fix.

Store those separately as evaluator-only ground truth.

## Model memorization

GPT-6 Astra's published knowledge cutoff is **April 30, 2026**.

Therefore prioritize Mindustry/Luanti bugs:

> **reported and fixed after April 30, 2026.**

This is much stronger evidence that Astra is reasoning from the supplied repository/game rather than recalling the historical answer.

Where a pre-cutoff issue is used:

- remove issue URL and issue number from model-visible input,
- rename benchmark case,
- strip obvious fix references,
- disclose this limitation.

---

# 16. Benchmark dataset structure

Example:

```text
benchmarks/
  mindustry/
    MD-001/
      manifest.yaml
      input/
        report.md
        metadata.json
        attachments/
      ground_truth/
        fix_commit.txt
        changed_files.json
        changed_symbols.json
        human_patch.diff
      expected/
        bug_oracle.yaml
      README.md
```

During a real benchmark run:

`ground_truth/` MUST NOT be mounted into the investigation workspace.

---

# 17. Case manifest

Example:

```yaml
id: MD-001
game: mindustry

repository:
  upstream: Anuken/Mindustry
  pre_fix_commit: abc123
  fix_commit: def456

build:
  command: "./gradlew desktop:dist"
  run_command: "java -jar desktop/build/libs/Mindustry.jar"

environment:
  os: linux
  resolution: [1280, 720]
  network: disabled

input:
  issue_title: "..."
  issue_body: "input/report.md"
  attachments: []

evaluation:
  bug_class: persistence
  positive_case: true
```

Never put hidden ground-truth root-cause information in model-visible manifest fields.

---

# 18. Include negative cases

Do not benchmark only known positive bugs.

Also include reports ultimately determined to be:

- user error,
- unsupported configuration,
- mod-related rather than base game,
- duplicate,
- upstream driver/system problem,
- insufficient evidence,
- not reproducible,
- expected behavior.

Otherwise a model that always says “confirmed bug” can look artificially good.

This allows measurement of:

**bug verification precision / recall.**

---

# 19. Case-selection criteria

Prefer bugs that:

- have a linked source fix,
- are reproducible on desktop Linux or a controlled environment,
- are behavior/state/UI/persistence/crash issues,
- do not depend on discontinued online services,
- can be reproduced in minutes rather than hours,
- have enough original evidence to start an investigation,
- were fixed after Astra's knowledge cutoff where possible.

Avoid initially:

- Android/iOS-specific bugs unless emulator infrastructure exists,
- GPU-vendor-specific bugs that cannot be recreated,
- network-service outages,
- performance regressions requiring hours of soak testing,
- bugs that depend on proprietary external content.

These are evaluation practicality constraints, not product limitations.

---

# 20. Target benchmark size

Goal:

**20–50 historical issues**, with a mixture of positive and negative cases.

Prefer:

- 15+ reproducible fixed bugs,
- several negative/non-bug reports,
- multiple bug categories,
- multiple versions,
- at least two open-source games if possible.

Do not fabricate results.

All submission numbers must come from stored benchmark run artifacts.

---

# 21. Metrics

## 21.1 Verification accuracy

Can REPRO correctly determine whether a report represents a reproducible bug?

Metrics:

- precision
- recall
- F1
- false confirmation rate

---

## 21.2 Reproduction success

For positive bugs:

```text
successfully reproduced / total reproducible cases
```

---

## 21.3 Time to first reproduction

Measure:

```text
investigation start → first verified reproduction
```

Store wall-clock seconds.

---

## 21.4 Reproduction stability

After discovering a reproduction sequence, replay it N times.

Example:

```text
9 / 10 successful
```

A reproduction is not considered deterministic solely because it happened once.

---

## 21.5 Action minimization

Record:

```text
actions in first successful reproduction
actions in minimal reproduction
```

Metric:

```text
1 - minimal_actions / original_actions
```

Example:

```text
17 → 4 actions
76.5% reduction
```

---

## 21.6 File localization

Ground truth:

files touched by the real historical fix.

Measure:

- Top-1 recall
- Top-3 recall
- Top-5 recall
- Mean Reciprocal Rank

Do not require candidate fix to be identical to human fix.

---

## 21.7 Symbol localization

Where ground truth can be extracted:

- class
- function
- method
- subsystem

Measure predicted causal symbols against symbols modified by historical patch.

---

## 21.8 Regression-test success

A generated regression test should ideally:

1. fail on the pre-fix commit,
2. pass on the actual human-fixed commit,
3. pass on REPRO's candidate patch if the patch is valid.

For bugs that are not easily unit-testable, the reproducible gameplay replay itself is a valid executable regression test.

---

## 21.9 Candidate patch validation

A patch succeeds only if:

- source compiles,
- existing tests remain green,
- generated regression test passes,
- original bug replay no longer triggers,
- basic smoke tests still succeed.

Patch similarity to the historical human diff is **secondary**.

An alternative correct fix is acceptable.

---

## 21.10 End-to-end resolution rate

Strongest overall metric:

> Percentage of historical bugs where REPRO went from raw report to verified reproduction + localization + regression test + validated candidate patch.

---

## 21.11 Cost

Record:

- input tokens,
- output tokens,
- model calls,
- computer actions,
- wall-clock time,
- approximate API cost.

Do not optimize primarily for cost during the hackathon.

But reporting cost makes the benchmark more complete.

---

# 22. Optional human baseline

If possible, select approximately five benchmark cases and have a developer manually investigate them without seeing the future fix.

Record:

- time to first repro,
- time to localization,
- confidence,
- actions taken.

Do NOT have the same person investigate manually after already seeing REPRO's answer.

If a proper human baseline is not possible, do not fake one.

The published 35.1% statistic can serve as problem evidence, but not as a direct measured speedup baseline.

---

# 23. System architecture

High-level architecture:

```text
                ┌────────────────────┐
                │ PLAYER / TESTER    │
                │ REPORT             │
                │ text/video/log/save│
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ INTAKE + NORMALIZER│
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ TRIAGE AGENT       │
                │ BugSpec            │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ ORCHESTRATOR       │
                │ GPT-6 ASTRA        │
                └───┬────────┬───────┘
                    │        │
          ┌─────────┘        └────────────┐
          ▼                               ▼
 ┌─────────────────┐            ┌─────────────────┐
 │ GAME INVESTIGATOR│           │ CODE INVESTIGATOR│
 │ computer use     │           │ shell/repo tools │
 └────────┬────────┘            └─────────┬───────┘
          │                               │
          ▼                               │
 ┌─────────────────┐                     │
 │ GAME BUILD      │                     │
 │ isolated desktop│                     │
 │ logs/state      │                     │
 └────────┬────────┘                     │
          │                               │
          └──────────────┬────────────────┘
                         ▼
                ┌────────────────────┐
                │ REPRO VERIFIER     │
                └─────────┬──────────┘
                          ▼
                ┌────────────────────┐
                │ REPRO MINIMIZER    │
                └─────────┬──────────┘
                          ▼
                ┌────────────────────┐
                │ TEST GENERATOR     │
                └─────────┬──────────┘
                          ▼
                ┌────────────────────┐
                │ PATCH AGENT        │
                └─────────┬──────────┘
                          ▼
                ┌────────────────────┐
                │ VALIDATOR          │
                │ build/test/replay  │
                └─────────┬──────────┘
                          ▼
                ┌────────────────────┐
                │ HUMAN REVIEW       │
                └────────────────────┘
```

---

# 24. OpenAI architecture

Use **GPT-6 Astra** as the primary investigator/orchestrator.

Current official model ID:

```text
gpt-6-astra
```

Astra officially supports complex reasoning, coding and computer use.

Recommended orchestration library:

**OpenAI Agents SDK**

It provides agents, tools, handoffs/agents-as-tools, sessions, human-in-the-loop functionality and tracing.

For this architecture, prefer:

> **manager/orchestrator + specialist agents exposed as tools**

rather than completely handing control between agents.

The Agents SDK documentation specifically recommends agents-as-tools when one manager should retain control and combine specialist outputs.

---

# 25. OpenAI tools

## ComputerTool

The game investigator needs actual GUI control.

OpenAI's Agents SDK `ComputerTool` can be backed by our own local computer environment and supports operations including:

- screenshots,
- clicks,
- double clicks,
- scrolling,
- typing,
- key presses,
- mouse movement,
- dragging.



Implement our game machine as an `AsyncComputer`.

---

## ShellTool

Use shell access for:

- repository search,
- builds,
- tests,
- logs,
- Git history,
- static analysis,
- runtime process inspection.

---

## ApplyPatchTool

Use for candidate code edits in an **ephemeral worktree only**.

The current Agents SDK supports local `ShellTool`, `ComputerTool`, and `ApplyPatchTool` execution surfaces.

---

## Tracing

Enable OpenAI Agents SDK tracing.

It captures:

- model generations,
- tool calls,
- agent spans,
- handoffs,
- custom spans.



Also persist our own investigation event log because the demo UI should not depend solely on the OpenAI dashboard.

---

# 26. Model allocation

Default:

### GPT-6 Astra

Use for:

- report understanding,
- hypothesis generation,
- computer use,
- code investigation,
- root-cause reasoning,
- test generation,
- candidate patching,
- final reporting.

Reasoning effort:

- medium for routine triage,
- high for reproduction/search,
- high/xhigh for difficult code localization or patches.

Smaller models may later handle:

- deduplication,
- cheap classifications,
- repetitive log extraction.

But do not prematurely optimize model cost.

The hackathon judges meaningful use of OpenAI technology.

---

# 27. Runtime environment

Recommended primary development environment:

**Linux machine / VM**

Components:

- Python 3.12+
- JDK 17 for Mindustry
- Docker where useful
- Xvfb or real X11 desktop
- lightweight window manager
- Mesa/software OpenGL if hardware acceleration unavailable
- FFmpeg
- Git
- ripgrep
- tree-sitter/ctags if useful
- `psutil`
- screen capture library such as `mss`
- keyboard/mouse automation layer

Use a **fixed screen size**, e.g.:

```text
1280 × 720
```

This makes recorded replay coordinates more deterministic.

---

# 28. Local ComputerTool implementation

Implement roughly:

```python
class GameComputer(AsyncComputer):
    environment = "computer"
    dimensions = (1280, 720)

    async def screenshot(self) -> str:
        ...

    async def click(self, x, y, button):
        ...

    async def double_click(self, x, y):
        ...

    async def scroll(self, x, y, scroll_x, scroll_y):
        ...

    async def type(self, text):
        ...

    async def keypress(self, keys):
        ...

    async def move(self, x, y):
        ...

    async def drag(self, path):
        ...

    async def wait(self):
        ...
```

Every action must be intercepted by an event recorder.

Persist:

```text
timestamp
action
arguments
screenshot_before
screenshot_after
log_delta
process_state
```

This recorded sequence later becomes a candidate reproducible test.

---

# 29. GameAdapter abstraction

Do not hardcode all orchestration logic to Mindustry.

Define something equivalent to:

```python
class GameAdapter(Protocol):
    async def prepare(case): ...
    async def build(case): ...
    async def launch(case): ...
    async def reset(session): ...
    async def install_save(session, path): ...
    async def screenshot(session): ...
    async def read_logs(session, since): ...
    async def process_state(session): ...
    async def terminate(session): ...
    async def smoke_test(case): ...
```

Game-specific adapter should contain:

- build command,
- launch command,
- log locations,
- save-data locations,
- window configuration,
- startup procedure,
- optional debug hooks.

It should NOT contain:

> bug-specific reproduction logic.

Otherwise the cross-game claim is meaningless.

Implement:

```text
MindustryAdapter
LuantiAdapter
```

---

# 30. Structured data models

Use Pydantic.

## BugReport

```python
class BugReport(BaseModel):
    id: str
    source: str
    title: str
    body: str

    platform: str | None
    build_version: str | None

    attachments: list[Artifact]
    logs: list[Artifact]
    save_files: list[Artifact]

    repository: str
    target_commit: str
```

---

## BugSpec

```python
class BugSpec(BaseModel):
    summary: str
    bug_class: str

    observed_behavior: str
    expected_behavior: str | None

    known_preconditions: list[str]
    uncertain_conditions: list[str]

    reproduction_hints: list[str]

    required_artifacts: list[str]

    candidate_oracles: list["OracleSpec"]

    severity_estimate: str
    confidence: float
```

---

## Hypothesis

```python
class Hypothesis(BaseModel):
    id: str
    statement: str

    preconditions: list[str]
    predicted_observation: str

    experiment_plan: list[str]

    probability: float
    status: Literal[
        "untried",
        "supported",
        "rejected",
        "inconclusive"
    ]
```

---

## RecordedAction

```python
class RecordedAction(BaseModel):
    index: int
    type: str
    args: dict

    semantic_description: str | None

    timestamp: float

    screenshot_before: str | None
    screenshot_after: str | None
```

---

## Reproduction

```python
class Reproduction(BaseModel):
    setup: list[str]
    actions: list[RecordedAction]

    oracle: OracleSpec

    successful_runs: int
    total_runs: int

    evidence: list[Artifact]

    deterministic: bool
```

---

## Localization

```python
class LocalizationCandidate(BaseModel):
    path: str
    symbol: str | None
    score: float
    evidence: list[str]
    reasoning: str
```

---

## CandidatePatch

```python
class CandidatePatch(BaseModel):
    diff_path: str

    tests_added: list[str]

    build_success: bool
    regression_test_success: bool
    replay_fixed: bool
    baseline_tests_success: bool

    risks: list[str]
```

---

# 31. Investigation state machine

Cases should move through explicit states:

```text
RECEIVED
↓
NORMALIZED
↓
TRIAGED
↓
ENVIRONMENT_PREPARING
↓
READY
↓
INVESTIGATING
↓
REPRODUCED
↓
MINIMIZING
↓
REPRO_CONFIRMED
↓
LOCALIZING
↓
TEST_GENERATING
↓
PATCH_PROPOSING
↓
VALIDATING
↓
AWAITING_HUMAN
↓
COMPLETE
```

Possible terminal alternatives:

```text
NOT_REPRODUCED
INSUFFICIENT_EVIDENCE
ENVIRONMENT_UNSUPPORTED
NOT_A_BUG
```

---

# 32. Triage agent

Responsibilities:

1. read report,
2. inspect attachments,
3. parse logs,
4. identify bug class,
5. separate facts from assumptions,
6. identify expected vs observed behavior,
7. list known and unknown preconditions,
8. generate possible detection oracles,
9. decide whether investigation is possible.

Categories should include:

- crash,
- object behavior,
- persistence/save,
- UI,
- rendering,
- input,
- network/multiplayer,
- economy/game state,
- performance,
- mod/plugin,
- platform compatibility,
- uncertain.

Never convert uncertain player statements into facts.

---

# 33. Artifact normalization

Before agent investigation:

### Video

Use FFmpeg to:

- extract metadata,
- sample keyframes,
- optionally create scene-change frames,
- retain original video.

Provide keyframes + report to Astra.

### Logs

Normalize:

- timestamps,
- severity,
- stack traces,
- repeated lines.

Retain raw logs.

### Save files

Never modify originals.

Copy to a per-run workspace.

Hash artifacts.

### Screenshots

Retain originals.

---

# 34. Duplicate/pattern detection

The team explicitly discussed studios being flooded with reports.

Implement report clustering as a supporting capability.

Given multiple reports:

```text
"shop took my gold"
"currency disappeared buying skin"
"bought item but balance reduced twice"
```

REPRO may group them into a canonical incident if evidence suggests the same underlying defect.

Output:

```text
INCIDENT #82

Probable duplicates: 14
Affected builds: 159.4–159.7
Platforms: Windows, Linux
Common trigger: interrupted purchase transaction

Confidence: 0.86
```

This is not the primary hackathon benchmark.

It strengthens the production story.

Never merge reports solely because their text is semantically similar; behavior/evidence should matter.

---

# 35. Hypothesis-driven investigation

Do not have the computer agent wander randomly.

Maintain an explicit hypothesis table.

Example:

```text
H1: save import fails for every save
H2: save import fails only for large archives
H3: imported archive contains malformed metadata
H4: path handling fails on a specific platform
H5: crash occurs during decompression
```

For every experiment record:

```text
hypothesis tested
setup
actions
prediction
observation
result
new evidence
```

After each failed attempt:

- update probabilities,
- generate new hypotheses,
- avoid repeating equivalent experiments.

---

# 36. Parallel exploration

Where environments permit:

Run several isolated investigators concurrently.

Example:

### Explorer A

Follow the player's reported path exactly.

### Explorer B

Search nearby state variations.

### Explorer C

Inspect logs/code and derive likely trigger conditions.

### Explorer D

Test environment/version/configuration assumptions.

Do not allow parallel agents to mutate the same game session.

Each receives its own session/workspace or serialized access.

---

# 37. Bug oracle system

The system needs evidence that the bug occurred.

Do not depend only on the same agent saying:

> “Looks broken.”

Implement multiple oracle types.

## Crash oracle

Signals:

- process exit,
- non-zero status,
- exception,
- crash log,
- known crash dialog.

## Log oracle

Example:

```text
ERROR InventorySerializer
NullPointerException
```

## Visual oracle

Astra evaluates whether screenshot/video exhibits the reported symptom.

Store:

- image evidence,
- model decision,
- confidence,
- description.

## State oracle

Where generic instrumentation is available:

- inventory value,
- player health,
- save state,
- object count,
- file contents.

## Composite oracle

Example:

```text
visual symptom AND specific error log
```

To reduce hallucinated confirmations:

- require evidence,
- replay,
- use an independent verifier pass.

---

# 38. Reproduction confirmation

One successful attempt is not enough.

After first reproduction:

1. reset environment,
2. execute exact same action sequence,
3. repeat N times,
4. measure success probability.

Suggested N:

```text
5 minimum
10 ideal
```

Output:

```text
Reproduction confidence: HIGH
9 / 10 successful
```

---

# 39. Reproduction minimization

This is a core differentiator.

Given:

```text
Launch game
Load save
Open map
Close map
Kill enemy
Pick item
Walk north
Open inventory
Close inventory
Fast travel
Open map
Take damage
Open inventory
Die
Respawn
```

Determine whether actions can be removed.

Goal:

```text
Pick item
Open inventory
Die during transition
Respawn
```

Use delta-debugging principles.

---

# 40. Minimization algorithm

Start with first successful action sequence `S`.

Pseudo:

```python
async def minimize(S):
    assert await reproduces(S)

    granularity = 2

    while len(S) >= 2:
        chunks = partition(S, granularity)

        reduced = False

        for chunk in chunks:
            candidate = S - chunk

            if await reproduces(candidate):
                S = candidate
                granularity = max(granularity - 1, 2)
                reduced = True
                break

        if not reduced:
            if granularity >= len(S):
                break

            granularity = min(
                len(S),
                granularity * 2
            )

    return S
```

But game actions have dependencies.

Therefore add semantic awareness:

- cannot remove “load save” if downstream state depends on it,
- cannot remove entering a menu if clicking an item requires it,
- may replace several navigation actions with a saved starting snapshot.

After structural minimization:

also reduce:

- waits,
- repeated actions,
- counts,
- state setup,
- configuration options.

---

# 41. ReproScript format

Every confirmed bug should become a machine-readable artifact.

Example:

```yaml
version: 1

game: mindustry
resolution: [1280, 720]

setup:
  save: artifacts/save.zip

steps:
  - action: launch

  - action: wait
    seconds: 2

  - action: click
    x: 612
    y: 411
    semantic: "Campaign"

  - action: keypress
    keys: ["escape"]

oracle:
  type: crash

repetitions: 10
```

Also generate a human-readable version.

---

# 42. Code investigation agent

The Code Investigator gets:

- BugSpec,
- successful reproduction,
- minimized sequence,
- screenshots,
- logs,
- stack traces,
- pre-fix repository.

Available operations:

```text
rg
git grep
git log
git blame
find
ctags/tree-sitter
build/test commands
read files
```

It must produce:

1. likely subsystem,
2. ranked files,
3. ranked symbols,
4. causal explanation,
5. evidence for each ranking.

---

# 43. Localization strategy

Use multiple evidence sources.

### Dynamic evidence

- stack traces,
- logs,
- errors,
- runtime behavior.

### Semantic evidence

Report vocabulary → code concepts.

### Structural evidence

- callers,
- callees,
- relevant state models,
- serialization handlers,
- UI callbacks.

### Historical evidence

Only history **before** the target commit:

- related earlier fixes,
- file ownership,
- subsystem evolution.

### Experiment evidence

Example:

> Bug only occurs if player dies during inventory opening.

Search for:

```text
death
inventory transition
serialization
event ordering
```

The model should explain why each file is suspected.

---

# 44. Ownership routing

The user wants:

> “who in the organization should handle this?”

Algorithm:

1. If `CODEOWNERS` exists, use it.
2. Otherwise inspect contributors to localized files.
3. Inspect repository labels/subsystems if available.
4. Rank likely maintainers.

Output:

```text
Likely ownership

Subsystem: Save / Persistence

Primary:
@developerA
Reason: CODEOWNERS entry

Secondary:
@developerB
Reason: 42% of recent commits touching affected files
```

Do not present heuristic ownership as certainty.

---

# 45. Severity estimation

Generate evidence-based triage:

```text
BLOCKER
CRITICAL
HIGH
MEDIUM
LOW
```

Useful signals:

- crash,
- data loss,
- corrupted save,
- progression blocker,
- multiplayer exploit,
- economy exploit,
- common core mechanic,
- cosmetic-only issue.

Do not hallucinate prevalence/frequency from a single report.

---

# 46. Regression-test generation

A patch should not be written first.

Preferred sequence:

```text
reproduce
→ minimize
→ localize
→ create regression test
→ confirm test fails
→ patch
→ confirm test passes
```

Two valid test classes:

## Code-level test

Unit/integration test inside upstream testing framework.

## Gameplay replay regression

If the behavior is difficult to express as a unit test:

- launch preconfigured build,
- execute ReproScript,
- evaluate oracle.

The latter is itself a legitimate regression test.

---

# 47. Candidate patch generation

Patch agent receives:

- BugSpec,
- reproduction,
- localization,
- regression test,
- relevant source.

It may:

- inspect files,
- edit an ephemeral branch/worktree,
- rebuild,
- run tests.

It should produce a **small, causal patch**, not broad refactoring.

Require explanation:

```text
Root cause:
...

Change:
...

Why this fixes it:
...

Potential side effects:
...
```

---

# 48. Human-in-the-loop boundary

Distinguish:

### Ephemeral benchmark workspace

The agent may automatically apply candidate changes so they can be tested.

### Actual production/upstream repository

The agent must NOT autonomously merge.

Final state:

```text
AWAITING HUMAN REVIEW
```

Buttons:

```text
[View Diff]
[Replay Bug]
[Run Validation Again]
[Approve PR]
[Reject]
```

This addresses concerns about autonomous changes to large codebases.

---

# 49. Validation

After patch:

### Build

Must compile.

### Existing test suite

Must remain green where practical.

### Generated regression

Must pass.

### Original reproduction

Replay exact minimized sequence.

Bug oracle must no longer trigger.

### Smoke testing

Game should still:

- launch,
- enter basic gameplay,
- perform minimal representative interactions.

Then output:

```text
PATCH VALIDATED

Build: PASS
Existing tests: PASS
Regression: PASS
Original bug replay: 0/10
Smoke test: PASS
```

---

# 50. Orchestrator

Use one top-level manager.

Pseudo:

```python
async def investigate(case):

    bug_spec = await triage(case)

    environment = await prepare_environment(case)

    hypotheses = await planner.create_hypotheses(
        bug_spec
    )

    reproduction = None

    while budget_remaining() and reproduction is None:

        experiment = await planner.next_experiment(
            bug_spec,
            hypotheses
        )

        result = await game_investigator.run(
            environment,
            experiment
        )

        verified = await oracle.verify(
            bug_spec,
            result
        )

        await planner.update(
            hypotheses,
            result,
            verified
        )

        if verified:
            reproduction = result

    if reproduction is None:
        return not_reproduced_report()

    minimal = await minimizer.minimize(
        reproduction
    )

    confirmed = await verifier.repeat(
        minimal
    )

    localization = await code_investigator.localize(
        bug_spec,
        minimal,
        confirmed
    )

    test = await test_writer.create(
        bug_spec,
        minimal,
        localization
    )

    patch = await patch_agent.propose(
        localization,
        test
    )

    validation = await validator.run(
        patch,
        minimal,
        test
    )

    return await reporter.generate(
        ...
    )
```

---

# 51. Failure handling

Never bury failures.

Possible outcome:

```text
Unable to reproduce after 37 experiments.

Most likely missing condition:
- platform-specific GPU state

Evidence:
- report is Windows/Intel only
- Linux reproduction failed
- behavior changed between renderer versions

Recommended human next step:
collect renderer/device logs.
```

A well-grounded “cannot reproduce” result is valuable.

---

# 52. Backend stack

Recommended:

### Python

- Python 3.12+
- FastAPI
- Pydantic
- OpenAI Agents SDK
- asyncio
- SQLAlchemy or lightweight SQLite wrapper
- Git subprocess/GitPython
- psutil

### Storage

Hackathon:

```text
SQLite
local artifact filesystem
```

No need to introduce a distributed database unless genuinely useful.

---

# 53. Frontend stack

Recommended:

- Next.js
- TypeScript
- React
- Tailwind
- Vercel

Screens:

### Dashboard

```text
Cases
Benchmark
Live investigations
```

### New Investigation

Inputs:

- GitHub issue / pasted report
- repository
- target commit
- attachments

### Investigation Page

Display live pipeline.

### Benchmark Page

Aggregate metrics.

---

# 54. Investigation UI

This is crucial to demo quality.

Suggested layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ CASE MD-017                    INVESTIGATING                 │
│ "item disappears after death"                               │
├──────────────────┬───────────────────────────────────────────┤
│ LIVE GAME        │ AGENT TIMELINE                            │
│                  │                                           │
│ [screenshot]     │ 00:12 H1 created                          │
│                  │ 00:21 Tested normal death                 │
│                  │       ❌ no bug                            │
│                  │ 00:39 Tested inventory-open death         │
│                  │       ✅ symptom observed                  │
│                  │ 00:44 replaying...                        │
├──────────────────┼───────────────────────────────────────────┤
│ HYPOTHESES       │ EVIDENCE                                  │
│ H1 ❌            │ screenshot                                │
│ H2 ✅            │ logs                                      │
│ H3 ...           │ crash event                               │
└──────────────────┴───────────────────────────────────────────┘
```

Do not hide the model reasoning behind a spinner.

Expose **safe high-level investigation state**, hypotheses, experiments, and evidence.

Do not expose private chain-of-thought.

---

# 55. Completed-case UI

Hero information:

```text
BUG VERIFIED

Reproduction:
10 / 10

First reproduced:
01:42

Original successful path:
14 actions

Minimal reproduction:
4 actions
```

Then:

### Minimal reproduction

1. Pick up key
2. Open inventory
3. Die during transition
4. Respawn

### Code localization

Top files/functions.

### Root cause

Short causal explanation.

### Ownership

Suggested subsystem/team.

### Regression

Fail-before / pass-after.

### Candidate patch

Diff viewer.

### Validation

Build/tests/replay status.

---

# 56. Benchmark UI

This page sells the product.

Show:

```text
HISTORICAL GAME BUG BENCHMARK

Cases: 24

Verified correctly: 21/24
Positive repro: 14/17
Top-5 localization: 13/17
Validated patches: 9/17

Median time to first repro: ...
Median action reduction: ...
```

Only populate with real measurements.

Add per-case rows:

```text
Case    Verify   Repro   Top-5   Test   Patch
MD-01     ✓        ✓       ✓      ✓      ✓
MD-02     ✓        ✓       ✓      ✓      -
...
```

---

# 57. Repository structure

Recommended monorepo:

```text
/
├── apps/
│   ├── web/
│   └── api/
│
├── repro/
│   ├── agents/
│   │   ├── triage.py
│   │   ├── planner.py
│   │   ├── game_investigator.py
│   │   ├── oracle.py
│   │   ├── code_investigator.py
│   │   ├── test_writer.py
│   │   ├── patch_agent.py
│   │   ├── validator.py
│   │   └── reporter.py
│   │
│   ├── orchestration/
│   │   ├── manager.py
│   │   └── state_machine.py
│   │
│   ├── adapters/
│   │   ├── base.py
│   │   ├── mindustry.py
│   │   └── luanti.py
│   │
│   ├── computer/
│   │   ├── desktop.py
│   │   ├── recorder.py
│   │   └── replay.py
│   │
│   ├── minimization/
│   │   └── ddmin.py
│   │
│   ├── schemas/
│   │
│   ├── storage/
│   │
│   ├── github/
│   │
│   └── utils/
│
├── benchmarks/
│   ├── manifests/
│   └── results/
│
├── scripts/
│   ├── harvest_github_cases.py
│   ├── prepare_case.py
│   ├── benchmark.py
│   └── license_report.py
│
├── infra/
│   ├── docker/
│   └── xvfb/
│
├── tests/
│
├── docs/
│   ├── architecture.md
│   ├── benchmark.md
│   └── third_party.md
│
├── README.md
└── pyproject.toml
```

---

# 58. CLI

Build a CLI even if frontend exists.

Useful commands:

```bash
repro ingest \
  --issue ISSUE_SOURCE \
  --repo REPO \
  --commit SHA
```

```bash
repro investigate CASE_ID
```

```bash
repro replay CASE_ID
```

```bash
repro validate CASE_ID
```

```bash
repro benchmark benchmarks/mindustry
```

```bash
repro report CASE_ID
```

This gives us a reliable fallback if the web UI breaks.

---

# 59. API

Suggested endpoints:

```text
POST /cases
GET  /cases
GET  /cases/{id}

POST /cases/{id}/prepare
POST /cases/{id}/investigate
POST /cases/{id}/replay
POST /cases/{id}/validate

GET /cases/{id}/events
GET /cases/{id}/artifacts

GET /benchmarks
GET /benchmarks/{id}

POST /cases/{id}/approve
POST /cases/{id}/reject
```

Use Server-Sent Events or WebSockets for live investigation events.

---

# 60. Database

Tables roughly:

```text
cases
bug_reports
artifacts
events
hypotheses
experiments
reproductions
actions
localizations
tests
patches
validations
benchmark_runs
```

Persist every experiment.

Reproducibility of our own evaluation matters.

---

# 61. GitHub benchmark harvester

Create script to identify candidate issues.

Desired pipeline:

```text
closed issues
↓
bug label
↓
linked PR/commit
↓
merged source change
↓
post-April-30-2026 if possible
↓
desktop-reproducible candidate
↓
create manifest
```

Use GitHub API during dataset preparation.

Then store:

```text
issue metadata
pre-fix SHA
fix SHA
changed files
timestamps
```

Do NOT store future fix inside model-visible workspace.

---

# 62. Historical repository builder

For each case:

1. clone upstream,
2. locate fix,
3. compute pre-fix SHA,
4. build a Git history containing only pre-fix SHA + ancestors,
5. prefetch dependencies,
6. confirm source builds,
7. remove upstream remote from benchmark copy,
8. disable network,
9. verify no fix references remain.

Produce:

```text
case.bundle
```

or isolated repo.

---

# 63. Build caching

Historical game builds can be expensive.

Cache by:

```text
game + commit + environment hash
```

Example:

```text
.cache/builds/mindustry/<sha>/
```

Likewise cache dependencies.

This lets agents repeatedly reset/replay without rebuilding.

---

# 64. Environment snapshots

Reproducing game bugs often needs initial state.

Support:

- clean profile,
- supplied save,
- copied config,
- artifact snapshot,
- restored working directory.

Before each experiment:

```text
restore known baseline
→ launch
→ run actions
```

Otherwise experiments contaminate each other.

---

# 65. Determinism

Control where possible:

- resolution,
- game version,
- commit,
- config,
- save,
- random seed if accessible,
- screen layout,
- locale,
- time scale,
- network state.

Record all environment metadata in the report.

---

# 66. Evidence discipline

Every conclusion should point to evidence.

Bad:

> “Inventory serializer is probably broken.”

Good:

> “Bug occurs only when PlayerDeath fires during InventoryOpening; runtime log shows persistence flush is skipped; `InventoryPersistence.java::save` contains an early return when transition state is active. Therefore this file is ranked #1.”

The UI should allow the user to inspect evidence behind findings.

---

# 67. Safety and isolation

Treat cloned repositories/builds as untrusted software.

Run game/build processes:

- outside developer secrets,
- isolated filesystem,
- minimal permissions,
- no production tokens,
- network disabled during benchmark,
- disposable workspace.

Never expose:

```text
OPENAI_API_KEY
GITHUB_TOKEN
deployment credentials
SSH keys
```

inside the game sandbox.

The orchestrator process may hold required model credentials outside that sandbox.

---

# 68. Definition of done for one case

A fully solved positive case has:

- [ ] report parsed
- [ ] environment built
- [ ] game launched
- [ ] bug reproduced
- [ ] evidence captured
- [ ] reproduction repeated
- [ ] sequence minimized
- [ ] replay artifact generated
- [ ] code localized
- [ ] root cause proposed with evidence
- [ ] owner/subsystem identified
- [ ] regression test generated
- [ ] test fails on pre-fix build
- [ ] candidate patch generated
- [ ] project builds
- [ ] regression passes
- [ ] original bug no longer reproduces
- [ ] existing tests/smoke test pass
- [ ] engineering report generated

---

# 69. Definition of done for negative case

- [ ] report parsed
- [ ] relevant environment prepared
- [ ] plausible hypotheses tested
- [ ] repeated attempts recorded
- [ ] no unsupported claim that bug exists
- [ ] conclusion classified
- [ ] missing evidence stated
- [ ] recommended next information requested

---

# 70. Engineering report output

Example:

```text
REPRO INVESTIGATION — MD-017

STATUS
Confirmed

SEVERITY
High

SYMPTOM
Quest item disappears after death.

MINIMAL REPRODUCTION
1. Load attached save.
2. Acquire red key.
3. Open inventory.
4. Trigger death while opening animation is active.
5. Respawn.

REPRODUCTION RATE
10 / 10

ROOT CAUSE
Inventory persistence is skipped when the death event interrupts
the opening transition.

LOCALIZATION
1. InventoryPersistence.java::serializeState   0.92
2. PlayerDeathHandler.java::onDeath            0.81
3. InventoryFragment.java::open                0.54

OWNER
Persistence subsystem
@...

REGRESSION
Generated: InventoryDeathTransitionTest

PRE-PATCH
FAIL

CANDIDATE PATCH
...

POST-PATCH
Build       PASS
Regression  PASS
Replay      0 / 10 failures
Smoke       PASS

STATUS
Awaiting human review.
```

---

# 71. Product name / branding

Working title:

# REPRO

Subtitle:

**Autonomous BugOps for Games**

Strong positioning sentences:

> **Turn “it crashed somehow” into a reproducible engineering task.**

> **From player report to verified patch.**

> **Your players find the bug. REPRO finds the cause.**

Do not spend engineering time on naming until product works.

---

# 72. 1-minute demo strategy

The required video is only 60 seconds.

The demo must establish:

1. real problem,
2. real game,
3. real historical bug,
4. autonomous interaction,
5. measurable result,
6. code-level output,
7. ground-truth validation.

---

# 73. Recommended 60-second video

## 0–6 sec

Text:

> **Game developers spend 35.1% of observed debugging time reproducing bugs.**

Show citation in tiny footer.

Then:

> **What if the bug report could investigate itself?**

---

## 6–13 sec

Show an actual historical Mindustry issue.

Something messy.

Overlay:

```text
REAL PLAYER REPORT
REAL OPEN-SOURCE GAME
REPO REWOUND TO BEFORE THE FIX
```

Then press:

**Investigate**

---

## 13–27 sec

Split screen:

left:

**Mindustry being autonomously controlled**

right:

agent timeline:

```text
H1 tested        ❌
H2 tested        ❌
H3 tested        ✅ BUG OBSERVED
Replaying...
```

---

## 27–35 sec

Huge result:

```text
BUG VERIFIED

10 / 10 reproductions
```

Then:

```text
Original sequence: 14 actions
Minimal repro: 4 actions
```

Press:

**Replay Bug**

Show it happen again.

---

## 35–44 sec

Code localization appears:

```text
LIKELY ROOT CAUSE

1. fileA.java::function       91%
2. fileB.java::function       73%
3. fileC.java::function       42%
```

Then:

```text
Regression test generated
Pre-fix: FAIL
```

---

## 44–52 sec

Candidate patch appears.

Run validation.

```text
Build      PASS
Regression PASS
Replay     0/10
```

Show fixed gameplay.

---

## 52–57 sec

This is the killer reveal:

```text
REPRO predicted:
fileA.java

ACTUAL HISTORICAL HUMAN FIX:
fileA.java
```

If candidate patch differs but behavior is correct, show:

> Independent valid fix

rather than implying identical patch.

---

## 57–60 sec

Benchmark dashboard:

```text
24 REAL HISTORICAL BUG REPORTS
...
```

with actual measured results.

Final:

# REPRO
### From player report to verified patch.

---

# 74. Demo authenticity

Do not fake a 60-second live investigation if an actual full run takes several minutes.

It is fine for the video to be an edited recording of a real autonomous run.

Make this obvious through UI timestamps/action history.

Do not fabricate model actions.

Store trace artifacts so judges can inspect the real execution.

---

# 75. Best live showcase flow

At the physical showcase:

1. explain historical benchmark,
2. choose one known case,
3. show report,
4. replay previously completed investigation,
5. optionally initiate a fresh run,
6. show exact trace/evidence,
7. show ground truth,
8. show aggregate benchmark.

This reduces reliance on a multi-minute live model call while retaining authenticity.

---

# 76. Team parallelization

Do not interpret the 100-hour limit as a reason to make the product concept smaller.

Instead parallelize.

Suggested workstreams:

## A — Game automation/runtime

- Xvfb/game window
- ComputerTool
- MindustryAdapter
- action recording/replay

## B — Agent backend

- schemas
- orchestrator
- triage/planner/oracle
- code investigator
- patch/validation

## C — Benchmark

- GitHub issue harvester
- historical commit isolation
- benchmark manifests
- metrics

## D — Product/UI

- dashboard
- case page
- live event stream
- diff/evidence panels
- benchmark visualization

Merge continuously.

---

# 77. Build dependency order

Critical dependency graph:

```text
Game boots deterministically
        ↓
Computer actions work
        ↓
Actions record/replay
        ↓
Oracle can detect one bug
        ↓
Agent can reproduce one real bug
        ↓
Minimization
        ↓
Code localization
        ↓
Regression generation
        ↓
Patch + validation
        ↓
Historical benchmark scale
        ↓
Second game
```

UI can develop independently using mocked event data, then connect to real backend.

Benchmark harvesting can run in parallel immediately.

---

# 78. First engineering milestone

Before adding clever multi-agent logic, prove:

```text
Python
→ launches historical Mindustry build
→ Astra sees screen
→ Astra controls game
→ actions are recorded
→ exact actions replay
→ screenshots/logs stored
```

Everything else sits on top of that.

---

# 79. Second engineering milestone

One real historical bug:

```text
raw report
→ autonomous reproduction
→ repeated reproduction
→ minimized replay
```

This validates the central product thesis.

---

# 80. Third engineering milestone

For same historical bug:

```text
reproduction
→ top-5 code localization
→ compare against historical fix
```

This creates first quantitative result.

---

# 81. Fourth engineering milestone

Complete the loop:

```text
regression
→ candidate patch
→ build
→ replay no longer triggers
```

Then scale benchmark.

---

# 82. What NOT to waste time on

Avoid unnecessary infrastructure for its own sake:

- Kubernetes
- complicated microservices
- vector DB unless proven necessary
- enterprise auth
- billing
- elaborate permissions
- multi-region deployment

Ambition should go into:

> **reasoning quality + empirical proof + product experience**

not infrastructure theater.

---

# 83. What WOULD materially improve the project

High-value additional capabilities:

- parallel hypothesis exploration,
- automatic report deduplication,
- cross-game adapters,
- bug cluster visualization,
- ownership routing,
- issue severity estimation,
- human approval workflow,
- automatic PR generation,
- benchmark replay site,
- confidence calibration.

---

# 84. Why OpenAI is fundamental

The system cannot realistically be implemented as ordinary deterministic automation because the input and environment are semantically open-ended.

Astra is responsible for:

- interpreting vague player language,
- understanding screenshots/video,
- generating hypotheses,
- adapting computer actions to a changing UI,
- connecting observed behavior to code,
- reasoning across runtime evidence,
- designing tests,
- generating candidate source changes.

Remove the model and the core workflow disappears.

This is not:

```text
logs → LLM → summary
```

The model exists inside the **closed-loop experimental process**:

```text
OBSERVE
↓
HYPOTHESIZE
↓
ACT
↓
MEASURE
↓
UPDATE BELIEF
↓
REPEAT
```

---

# 85. What makes the project original

The individual capabilities are not the novelty:

- computer use exists,
- coding agents exist,
- automated tests exist,
- bug trackers exist.

The novelty is the connection:

> **unstructured player evidence → autonomous empirical investigation inside the game → minimal reproducible case → evidence-grounded code localization → executable regression → reviewable remediation**

The game runtime and code repository become part of one reasoning environment.

---

# 86. Utility story

Game studios do not need another tool that merely generates Jira text.

They need the ticket to arrive with:

- proof,
- exact reproduction,
- evidence,
- responsible subsystem,
- regression,
- candidate remediation.

The unit of value is:

> **time from player report to actionable engineering work.**

That should be the product's north-star metric.

---

# 87. Benchmark integrity rules

Never:

- manually modify a benchmark case to make REPRO succeed and then count it normally,
- let REPRO see the fix,
- let REPRO search the internet,
- count unreproduced issues as solved,
- count a compilation-only patch as fixed,
- count localization as correct merely because it names the same general subsystem,
- report only handpicked successes without disclosure.

Maintain:

```text
all_cases.json
```

with every attempted benchmark case and outcome.

Judges may care more about honest numbers than perfect ones.

---

# 88. Third-party/licensing strategy

Our repository should contain mostly our code.

For open-source target games:

- reference upstream,
- clone/build during preparation,
- keep license notices,
- do not claim game source/assets as ours.

Mindustry:

**GPL-3.0**.

Luanti core:

**LGPL-2.1-or-later**.

OpenAI Agents SDK:

**MIT**.

Public GitHub bug reports and attachments should be treated as externally authored material.

Prefer storing:

- issue ID,
- metadata necessary for evaluation,
- retrieval script,

rather than redistributing all external attachments in our repository.

Generate a final:

```text
THIRD_PARTY.md
```

from actual dependencies.

Do not guess licenses at submission time.

---

# 89. README opening

Suggested:

```text
# REPRO

Autonomous BugOps for games.

REPRO turns messy player bug reports into verified engineering work.

Given a report, video, logs or save file, REPRO can investigate a game
build using computer use, reproduce the failure, minimize the sequence,
localize the likely source code, generate a regression test and propose
a validated patch for human review.

Rather than evaluating against toy bugs, REPRO is benchmarked by rewinding
real open-source games to historical pre-fix commits and asking the system
to independently rediscover bugs using only the information originally
available to developers.
```

---

# 90. Submission draft — project description

**Keep final below 200 words. Replace benchmark placeholders with real results.**

REPRO is an autonomous bug-operations engineer for game studios. Player bug reports are often vague: a crash video, a save file, or “my item disappeared after I died.” Before fixing anything, developers must reproduce the behavior, isolate the triggering state, inspect game artifacts and find the responsible code.

REPRO takes that workflow end-to-end. Given a report and game repository, it autonomously operates the game, generates and tests hypotheses, verifies the bug, reduces the interaction to a minimal reproducible sequence, inspects runtime evidence and localizes likely source files/functions. It then creates an executable regression test, proposes a candidate patch in an isolated workspace, rebuilds the game and replays the original bug before presenting the result for human review.

We evaluate REPRO retrospectively on real historical bugs from open-source games: we rewind each repository to the commit before the human fix, hide the future patch, disable internet access and ask REPRO to independently rediscover the issue.

---

# 91. Submission draft — meaningful use of OpenAI tools

REPRO uses GPT-6 Astra inside the actual debugging control loop rather than as a text-generation layer. Astra interprets noisy player reports, screenshots, videos and logs; generates competing causal hypotheses; and uses computer control to execute experiments directly inside real game builds. Observations from each experiment update the next investigation step.

Once behavior is reproduced, Astra reasons jointly over the minimal action sequence, runtime evidence and source repository to rank likely files/functions and explain the causal path. It then generates a regression test and candidate patch, which are executed rather than merely described.

The OpenAI Agents SDK coordinates specialized investigation, code and validation agents, while ComputerTool provides interaction with the running game and shell/patch tools connect reasoning to the source/build environment. Tracing records the investigation process.

Removing the OpenAI model would fundamentally remove the system's ability to transform ambiguous human evidence into adaptive experiments and engineering artifacts.

---

# 92. Submission draft — originality

Most automated testing begins with a test that somebody already knows how to write, while coding agents typically begin with a developer telling them what to fix. REPRO begins earlier: with the incomplete evidence that arrives from an actual player.

Its central contribution is connecting runtime investigation and software engineering into one closed loop:

**player report → hypothesis → autonomous gameplay experiment → verified reproduction → minimal repro → code localization → regression test → validated candidate patch.**

The system does not merely explore for arbitrary defects or summarize an issue tracker. It asks whether a reported behavior really exists, experimentally discovers the conditions under which it occurs and grounds subsequent code changes in that observed behavior.

We also evaluate the system differently from a typical hackathon prototype. Historical open-source repositories are rewound to their state before a real bug was fixed; future code and internet access are hidden; and REPRO's localization and remediation are compared against the actual later outcome.

---

# 93. Submission draft — playability / utility

A recent industry study observing 20 experienced game developers found that 35.1% of debugging time was spent reproducing bugs locally and 36.6% inspecting game artifacts. REPRO directly targets these two bottlenecks.

For a developer, the useful output is not another AI-generated explanation. It is an actionable incident containing a reproducible replay, reproduction rate, evidence, minimal trigger sequence, ranked source locations, likely subsystem owner, executable regression and reviewable candidate patch.

Our historical benchmark measures this utility rather than relying on subjective demos. On `<N>` real reports, REPRO reproduced `<X%>`, achieved Top-5 source localization of `<Y%>`, reduced reproduction sequences by `<Z%>` and produced `<P>` validated candidate fixes. **Replace these placeholders only with final measured values.**

The same architecture uses game adapters rather than bug-specific scripts, allowing the system to investigate different game engines while preserving the core workflow.

---

# 94. Submission draft — execution and craft

REPRO is built as an observable, reproducible engineering system rather than a scripted demo. Each investigation runs against an isolated game/build environment with deterministic configuration, records every computer action, screenshot and log delta, maintains explicit hypotheses and stores artifacts required to replay the result.

Successful reproductions are automatically repeated and minimized before code investigation begins. Candidate patches must build, pass the generated regression test and survive replay of the original failure before being marked validated. The final code change remains human-reviewed.

The product UI exposes the workflow in real time: game screen, experiments, evidence, reproduction confidence, minimal replay, source localization, diff and validation status. A CLI provides the same investigation/replay functionality independently of the frontend.

For evaluation, historical repositories are truncated before their real fix and run without internet access. Benchmark metrics and traces are persisted per case so results can be inspected rather than asserted.

---

# 95. Submission draft — pre-existing/open-source/third-party components

REPRO's application and orchestration code was created during the challenge. We use the OpenAI Agents SDK (MIT) and OpenAI API models/tools for agent orchestration, computer interaction and reasoning. Our primary external evaluation target is Mindustry (`Anuken/Mindustry`, GPL-3.0), and a secondary target is the Luanti game engine (`luanti-org/luanti`, LGPL-2.1-or-later). These projects are used as independently developed open-source systems on which REPRO investigates historical bugs; their source/assets are not presented as our work.

We additionally use standard development/runtime dependencies for the Python backend, web frontend, Git operations, screen capture, process isolation and media processing. Their exact package names, versions and licenses should be generated from the final lockfiles and recorded in `THIRD_PARTY.md` before submission.

Historical GitHub issue text/attachments remain externally authored material; benchmark manifests should reference public source issues rather than unnecessarily redistributing third-party attachments.

---

# 96. Results template

Create:

```markdown
# Evaluation Results

## Dataset

Games:
- Mindustry
- Luanti

Cases attempted:
Positive:
Negative:

## Verification

Precision:
Recall:
F1:

## Reproduction

Successful:
Median time:
Median repetitions:

## Minimization

Median initial actions:
Median final actions:
Median reduction:

## Localization

Top-1:
Top-3:
Top-5:
MRR:

## Regression

Fail-before/pass-after:
...

## Candidate patch

Built:
Validated:
End-to-end:
...

## Cost

Median tokens:
Median API cost:
Median wall time:
```

Automatically generate from benchmark DB.

---

# 97. Critical product claims checklist

Allowed once proven:

> “REPRO reproduced X/Y historical bugs.”

> “REPRO localized Y% of real fixes within its Top-5 predictions.”

> “REPRO reduced successful reproductions from median X actions to Y.”

> “REPRO generated Z validated patches.”

Allowed immediately with citation:

> “In one 2026 study, game developers spent 35.1% of observed debugging time reproducing bugs locally.”

Do not claim:

> “REPRO saves 35% of all game development time.”

Do not claim:

> “REPRO replaces QA engineers.”

Do not claim:

> “REPRO fixes every game automatically.”

---

# 98. Core narrative for judges

Everything should reinforce this story:

### Problem

> The expensive part often starts before fixing: turning a player's experience into a reproducible engineering problem.

### Insight

> Modern multimodal computer-use models can participate in the empirical debugging loop itself.

### Product

> REPRO investigates the game first and the code second.

### Proof

> We rewind real games to before real historical fixes and ask REPRO to independently rediscover them.

### Output

> Reproduction, localization, regression and validated candidate remediation.

---

# 99. One-sentence explanation to another engineer

> **REPRO is an agentic debugging system that starts from a raw player report, autonomously reproduces and minimizes the failure in the actual game, traces it into the source code, writes the missing regression test and produces a behaviorally validated patch for human review.**

---

# 100. One-sentence explanation to a game executive

> **REPRO turns player bug reports into engineering-ready fixes instead of making developers spend hours proving the problem exists first.**

---

# 101. One-sentence explanation to a judge asking “why does this need AI?”

> **Because neither the player's language, the game's UI, nor the path from observed behavior to source code is predefined—the model must continuously understand the situation, form hypotheses, run experiments and change strategy based on what actually happens.**

---

# 102. One-sentence explanation to “isn't this just Claude Code?”

> **A coding agent starts with a software task; REPRO autonomously discovers the software task by investigating the reported behavior in the running game first.**

---

# 103. One-sentence explanation to “isn't this just automated QA?”

> **Automated QA asks the game to reveal unknown bugs; REPRO asks a known but poorly understood player complaint to reveal its exact cause.**

---

# 104. Final engineering directive

Build toward the complete pipeline:

```text
REPORT
↓
VERIFY
↓
REPRODUCE
↓
MINIMIZE
↓
LOCALIZE
↓
ROUTE
↓
REGRESSION TEST
↓
PATCH
↓
VALIDATE
↓
HUMAN REVIEW
```

Do not stop after generating text.

Every major claim should produce an executable or inspectable artifact:

```text
“bug exists”
→ replay + evidence

“this triggers it”
→ minimal action sequence

“this code is responsible”
→ ranked source references + evidence

“this fixes it”
→ diff

“it is fixed”
→ regression + replay result
```

The central design principle is:

# **The agent must prove its conclusions against the game.**

That is the product.