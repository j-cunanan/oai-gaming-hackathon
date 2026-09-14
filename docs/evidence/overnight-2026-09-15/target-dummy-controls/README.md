# Target Dummy supplemental controls

These checks were authored by the Codex evaluator **after** REPRO generated its
candidate. They are additional evaluation, not a model-generated regression test
or a replacement for the app's failed full save/reopen gate.

`result.json` records the exact game commit, worker image, network mode, commands,
elapsed time and SHA-256 of each log. The original driver copied the prepared local
workspace using macOS copy-on-write, restored its source to the untouched commit,
and checked it was clean before running the full online baseline suite. It did not
modify the live case or its candidate. The dependency cache was copied, and the
Gradle commands forced assertion execution and recompilation without build cache.

- Full untouched baseline: 213 tests completed, one failed. `ModTestAllure.begin()`
  fails because its original, version-pinned GitHub mod archive returns 404. The
  same failure appears in the candidate's full online test log.
- Added serialization regression on baseline: three default-team cases fail with
  the null-team save exception; the explicit-team case passes.
- The exact AI patch plus the same regression: all four cases pass. The assertions
  also check the unchanged 21-byte field layout and retained non-team values.

The test exercises `write`/`read`, not a complete game-map save and reload.
`driver.py` preserves the original execution code and its local paths; rerunning it
requires that prepared local case and a new output/control directory. The recorded
source and logs can be inspected without running anything or using an API key.
