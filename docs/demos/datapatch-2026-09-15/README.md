# Recorded data-patch walkthrough

Open `index.html` from a complete checkout, or serve the repository locally and visit `/docs/demos/datapatch-2026-09-15/`. This is a portable, static before/after walkthrough using actual saved screenshots. It makes no model calls and does not run Mindustry.

The eight checkpoints compare the final reduced-baseline confirmation (replay event 2741) with the first candidate replay (event 2815), selected from `md-12620-terra-overnight-02`. Both executed the same 30 action records. `recording.json` preserves capture times, event sequence numbers, screenshot hashes and the original verifier verdicts. The full case package retains all runs; this selection is a presentation excerpt, not a new experiment or real-time video.

The original report-only attempt remains at 3/5 confirmation. The shown fresh attempt received explicitly labeled guidance to include both save confirmations, but no source diagnosis or historical developer patch. Its all-five-gates result includes 5/5 baseline and candidate replay outcomes and 276/276 upstream tests with zero skips. The test concerns persistence of an editor-accepted patch entry; it does not establish changes to gameplay balance or other patch effects.

`repro-report.pdf` is the reviewed eight-page REPRO report generated from the saved case using the candidate-outcome-aware renderer identified by SHA-256 in `report-provenance.json`. Its final page now shows the recorded candidate result after reopen; startup smoke no longer replaces that evidence. Its source-review notes remain verbatim, under an explicit source-analysis scope. A static SHA-256 manifest covers the delivered files.

A [short demo script](demo-script.md) explains the persistence failure, the reproduction work and the limits of the evidence.

Rebuild the checkpoint data without new executions:

```bash
uv run python docs/demos/datapatch-2026-09-15/build.py
```

The builder checks equality with the frozen action sequence and verifies all 16 image hashes before emitting the data. The browser was checked for image loading, checkpoint navigation, playback controls, patch inspection and links.
