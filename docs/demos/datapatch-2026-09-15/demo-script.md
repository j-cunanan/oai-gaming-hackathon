# A short, evidence-backed REPRO demo

Open the [recorded walkthrough](index.html). It presents eight selected checkpoints from actual runs, not a live game or a newly executed investigation. The complete replay contains 30 actions. The original report-only attempt was incomplete; this fresh run received explicit guidance to record both save confirmations, without a source diagnosis or historical patch.

## The story

1. **The report:** “I delete a data patch, save my map, and it comes back when I reopen it.” This is a persistence bug: looking only at the deletion screen would miss it.
2. **Follow the paired screenshots:** Start from the saved entry, delete it, confirm the save, leave the map and reopen the same map. At the final checkpoint, the baseline has the unwanted entry again. The candidate says “No patches found.”
3. **Explain the hard part:** REPRO had to obtain and replay the full trigger, distinguish a save confirmation from navigation, and inspect the result after reopening. The confirmed sequence reproduced on five fresh baseline profiles; bounded reduction removed one of its original 31 actions.
4. **Show the proposed patch:** The UI removed the entry from its local collection, but the save-facing asset list was stale. The AI inserted `state.data.reloadPatches(patches);` after removal so saving uses the updated collection. The small diff follows from the recorded behavior and source diagnosis.
5. **Show the checks:** All five gates pass: baseline regression, candidate build, all 276 upstream tests with no skips, five candidate replays that reach the expected state, and startup smoke. The PDF includes the rationale, limitations, timeline and actual outcome images.

The engineering value is the reproducible evidence connecting the report to a tested change. Patch size alone does not describe the investigation effort.

## What this recording does and does not establish

- It verifies persistence of an editor-accepted data-patch entry. It does not measure gameplay balance changes or other effects of that entry.
- Five fresh replay outcomes are model-checked visual evidence; they do not establish every platform or every save scenario.
- Startup smoke confirms a launch and live process, not broad gameplay coverage.
- The case awaits human review. No Mindustry patch was published upstream.
- The original failed attempt, the explicit assistance and all underlying events remain available alongside this successful run.

Use the full report or [saved case package](../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/README.md) for questions about methods or exact counts. The walkthrough is a concise presentation of those records, not additional experimental evidence.
