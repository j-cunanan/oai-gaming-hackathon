# Desktop replay timing

For MD-001's eight-action baseline replay, the new worker reduced median elapsed time from **47.3 to 30.9 seconds**, about **35%**. All six final screenshots were visually checked: each reached Custom Rules with duplicate Weather controls. These measurements exclude model calls and recorder/database writes; they do not measure the speed of an entire AI investigation.

| Alternating pair | Old worker | Persistent worker |
| --- | --- | --- |
| 1 | 49.37 s | 30.67 s |
| 2 | 44.73 s | 30.93 s |
| 3 | 47.32 s | 32.24 s |
| Median | 47.32 s | 30.93 s |

The measurement used the same retained pre-fix Mindustry binary, eight recorded actions and waits, 1280 × 720 desktop, fresh container/profile, offline networking, and 3-CPU/5-GB worker limits on the same Apple Silicon host under AMD64 emulation. Runs alternated old/new without another REPRO job running. Elapsed time includes reset, launch, and every action/screenshot response; final container cleanup follows the measurement. Both variants used the same load-complete guard and one-second settling period after the existing eight-second startup minimum. The old transport received that guard in the comparison wrapper so missed startup clicks would not distort the result.

The new worker saves time by keeping Python and the screenshot driver alive, combining action and screenshot replies, reducing lossless PNG compression work, and removing a redundant container-stop command. Recorded input timing and fresh-state checks were retained. Three samples per worker are a local timing check, not a general performance benchmark.

- [Raw timings, actions, binary hash and image hashes](result.json).
- [Exact measurement script](measure.py): a local development probe requiring the retained case workspace and both image tags; it makes no model calls or case-record writes.
- [Worker image identities](images.json): both are Linux AMD64 and share the first seven image layers.
- Final screenshots: `old-1.png` through `old-3.png` and `new-1.png` through `new-3.png`.
- [Initial probe](initial-probe.json): with only the fixed eight-second startup delay, both variants reached the target in 2/3 trials. Those timings are excluded from the final comparison. The [old](initial-old-missed-startup.png) and [new](initial-new-missed-startup.png) missed-startup screenshots are retained. This finding led to the readiness check before the full validation rerun.
