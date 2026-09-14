# Mindustry candidate shortlist — 2026-09-14

Evaluator-only research. Do not provide this document, candidate evaluator fields, human diffs, or this research conversation to an investigator. Dispatch fresh investigations with only manifest `input` fields and isolated pre-fix source. Public historical fixes can have appeared in model training; hiding the fix at runtime does not prove lack of memorization.

Reviewed 200 recent commit entries and 19 linked issue/PR records; inspected 12 fix commits. This is a curated recent-history sample, not an exhaustive survey. Eight new candidates are retained below. All are **runtime-unverified**. The existing MD-001 Weather-button case remains the only recorded reproduction in this repository. Docker was unavailable in the current shell, so no builds, games, or model investigations were run.

## Recommended order

Start with #12579 (editor save crash), #12620 (deleted patch returns), and #12623 (hex color precision). Together with existing MD-001 these cover crash, persistence, numeric UI behavior, and a simple visual defect. Add #12565 for deeper gameplay reasoning after setup qualification. Priority is an engineering estimate, not measured model performance.

| Issue | Priority | Suggested tags | Proposed reproduction | Prerequisites and limitations |
|---|---|---|---|---|
| [12579](https://github.com/Anuken/Mindustry/issues/12579) | P1 | Crash / editor / initialization | Place a Target Dummy in a fresh editor map, then save. | No imported save should be necessary; reported on Windows, Linux reproduction unverified. Verify save and reload succeed on the candidate, not just absence of a crash. |
| [12620](https://github.com/Anuken/Mindustry/issues/12620) | P1 | Persistence / editor / data patches | Create a map, add and save a data patch, delete it, save, leave and reopen the map. | Reported on Android; confirm Linux behavior. Needs a valid harmless data patch created through the UI. No process restart is required by the reported steps. |
| [12623](https://github.com/Anuken/Mindustry/issues/12623) | P1 | UI / numeric precision / color picker | In the editor, enter adjacent hex values such as ff0200 and ff0300 for colored tiles and inspect the retained values. | Reported on Windows; Linux unverified. Tiny color differences are weak screenshot evidence: verify displayed hex values and persistence. ItemBridge.java in the human commit is incidental formatting, excluded from causal-file scoring. |
| [12565](https://github.com/Anuken/Mindustry/issues/12565) | P2 | Gameplay / payloads / unit state | Drive or command a unit into a payload conveyor in a fresh sandbox map. | Needs unit and conveyor setup. A unit becoming a payload is normal; verify unexpected loss by observing transport/output, not disappearance alone. Reported on Windows. |
| [12598](https://github.com/Anuken/Mindustry/issues/12598) | P2 | UI / logic editor / layout | Open a processor, add a jump with a destination, and switch its condition to always. | Reported on Android; Linux 1280x720 layout may not exhibit the same offset. Establish visible geometry before admitting the case. |
| [12640](https://github.com/Anuken/Mindustry/issues/12640) | P2 - runner extension | Persistence / controls / settings | Open Controls, rebind an action, choose Unbind, restart the game, and inspect that action. | Reported on Linux. Current reset deletes the profile; replay needs a restart action that preserves the profile within each run, while runs still start clean. |
| [12652](https://github.com/Anuken/Mindustry/issues/12652) | P3 - fixture required | Crash / data patches / content lifecycle | Open the supplied patched-content map, edit in game, quit to editor, open Data Patches & Assets, switch tabs, and press Escape. | Reported on Mac with an unmodded crash log. Requires inspecting and installing supplied map assets; automatic fixture installation is not implemented. Timing and Linux reproduction unverified. |
| [12603](https://github.com/Anuken/Mindustry/issues/12603) | P3 - complex setup | Gameplay / payload lifecycle / destruction | Fuel a generator with Blast Compound, pick it up damaged, put it on a payload conveyor, let it explode, then try to retrieve and place it. | Requires reactor explosions enabled, controlled damage, resources and payload handling. Strong multi-file reasoning case but a long, timing-sensitive demo. Reported on Windows. |

## Qualification before scoring

1. Build the exact parent revision listed in each manifest and record baseline test failures.
2. Reproduce on Linux AMD64 from a clean profile five times. Verify that the human-fixed revision resolves the selected symptom; a linked fix alone does not establish this.
3. Freeze the report symptom and expected target state before attempting a patch. Preserve original attachments; review fixtures before installation.
4. Run a fresh investigator without evaluator data. Record model identity, budgets, attempts, failures, reproduction rate, localization rank, and all five existing validation gates.
5. Add matched negative controls using a verified fixed build. Absence of a symptom outside its required target state is inconclusive. Controls from the same bug are paired checks, not independent bug cases.

## Deferred or excluded

- #12644 (UI-scale category selection): Linux report is promising, but the fix also updates Arc in gradle.properties. Current patch prompts prohibit dependency/build-script changes; inspect the Arc changes before treating it as a source-only candidate.
- #12566 (sector-list clipping): similarly bundles an Arc revision update and may need campaign progress/long sector names.
- #12613 (Target Dummy hitbox/text): inspected fix addresses hitbox geometry, not both reported symptoms. Do not count the entire report as verified fixed.
- #12626 (ghost dummy payload): human fix intentionally disallows dummy payloads. That conflicts with current generic patch guidance against disabling behavior and with unchanged replay assumptions; needs an explicitly justified behavioral contract.
- #12600: report explicitly calls the crash unstable and relies on a save/video.
- #12611: campaign progression, a timer, and inconsistent pathfinding; poor first demo.
- #12632: campaign completion, mods and saved state complicate isolation.
- #12636: Android layout report with unverified desktop behavior; weaker than the selected alternatives.
- #12650: Steam multiplayer and mods exceed current runner scope.
- #12615: texture-asset defect, outside the strongest source-patching demonstration.
- #12624: a pull request with proposed implementation, not a clean player-report input.

## Usage

Candidate files use the existing manifest schema and remain outside the admitted manifests directory. For a selected candidate:

```bash
uv run repro import-case benchmarks/candidates/MD-candidate-12579.yaml
uv run repro prepare CASE_ID
uv run repro investigate CASE_ID
```

Do not promote a candidate or claim success until its evidence exists. Importing a candidate does not establish reproduction. Existing upstream offline-network test failures must remain visible.
