# MD-001: duplicate Weather controls

This is a selected historical Mindustry case, evaluated on September 14, 2026 (Japan time). It is one case with a Luna investigation and a Terra investigation plus refinement passes, not a representative benchmark.

The player [reported two Weather buttons in map rules](https://github.com/Anuken/Mindustry/issues/12647). The investigation received the short report and exact pre-fix revision `a5c178ae5abcc630613c233e0afbb361021d3828`. It did not receive the later human patch, changed-file list, GitHub comments or internet access.

## Recorded evidence

- [Original confirming screenshot](before.png): both Weather buttons are visible.
- [Source findings](source-findings.json): the investigator ranked `CustomRulesDialog.java` first and identified two explicit constructions of the same control.
- [Generated candidate](candidate.patch) and [rationale](patch-rationale.json): four lines removed from the duplicate construction in Lighting.
- [Candidate build log](candidate-build.txt): successful offline desktop build.
- [Candidate tests](candidate-tests.txt): 275 of 276 tests passed. `ModTestAllure.begin` failed while downloading a mod from GitHub in the network-disabled worker.
- [Untouched baseline network test](baseline-offline-mod-test.txt): the same `UnknownHostException` occurs without the candidate patch. It remains a failed candidate gate.
- [Container audit](isolation.json): no network, dropped capabilities, no secrets or Docker socket in the worker.
- [Luna attempt](luna-attempt.json): not reproduced; retained alongside the successful Terra reproduction.
- [Initial Terra attempt](initial-terra-attempt.json): 5/5 baseline replays with 23 actions. Its candidate replay left the required target state, so expected-state verification rejected it and the run was stopped for replay refinement.

Replay refinement and repeated post-patch checks are still being evaluated in the accompanying draft PR. Final results will replace this sentence when those checks complete.

## Evidence boundaries

The report's platform was Windows; this run used the Linux AMD64 desktop under Docker on Apple Silicon. Mindustry is the external game being tested, not an original REPRO game. Visual judgments use separate calls to the same model family; they are not calibrated ground truth. The source was a depth-one snapshot, so ownership history is intentionally unavailable. Preparation had temporary network access for dependencies; investigation and candidate validation did not. Startup smoke coverage is limited to a clean launch. No target-game repository was changed upstream.

The unsuccessful attempts, cancellations, refinement passes and test failures are part of the result. Do not present this development session as one uninterrupted autonomous resolution or use it to claim an accuracy percentage.
