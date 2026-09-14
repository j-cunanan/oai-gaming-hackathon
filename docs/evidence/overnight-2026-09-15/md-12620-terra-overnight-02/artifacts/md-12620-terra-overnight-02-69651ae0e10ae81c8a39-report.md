# REPRO — [Evidence guided] Persistent Datapatch bug


Status: **AWAITING_HUMAN**


Candidate ready for review. Validation gates satisfied; inspect any pre-existing test failures.


Game: mindustry · revision `63b2069e9685063c74abc41fae84a66f73e9e09b`


## Player report

### Platforms

Android

### Build

BE 27790

### Issue

When you save a datapatch in a map, suddenly, attempting to remove it does not work.
When you remove it, it gets temporarily removed, but gets added back when you open the map.
I tested this with or without mods and it still happened by the way.

### Steps to reproduce

Make map
Add data-patch
Save map
Delete data-patch
Save map
Leave editor
Come back to map editor
See that the data-patch is back.

### Mods used

I tested it in vanilla but here are the mods I usually use.

Auto Research (gone from in-game mod browser?)
Patch Editor (I think this mod doesn't cause the issue)
Patch Viewer
CLaJ

### Save file

I zipped the msav here

[persistent datapatch bug.zip](https://github.com/user-attachments/files/32028828/persistent.datapatch.bug.zip)

### (Crash) logs

_No response_

### REPRO recording guidance (not part of the upstream report)

A previous local attempt reached the reported sequence, but the final oracle omitted its recorded initial-save screenshot. Two of five independent replay judgments were inconclusive because that prerequisite was not visible in the selected evidence. This is a fresh attempt; those prior judgments do not establish the current result.

Capture and select the important checkpoints in chronological order: the map identity and existing patch, visible successful initial save, confirmed deletion with an empty list, visible successful save after deletion, exit/reopen of the same map, and the patch list after reopening. Include both successful-save screenshots in the final sequence oracle, within its eight-checkpoint limit. Use neutral labels for the resulting state; inspect what is actually visible rather than assuming disappearance or reappearance. If prerequisites cannot be demonstrated, report that limitation.



## Reproduction

5/5 successful clean replays. 31 → 30 actions (bounded reduction, not a proof of global minimality).

1. Open map editor from main menu — `{"action":"click","x":253,"y":335,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open map editor from main menu","checkpoint":"open_editor"}`

2. Create a new editable map — `{"action":"click","x":635,"y":678,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Create a new editable map","checkpoint":"new_map_dialog"}`

3. Focus map-name text field — `{"action":"click","x":700,"y":357,"keys":[],"text":"","seconds":0.5,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Focus map-name text field","checkpoint":""}`

4. Enter unique map name — `{"action":"type","x":630,"y":357,"keys":[],"text":"DatapatchPersistenceTest","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Enter unique map name","checkpoint":"map_name_attempt"}`

5. Create named test map — `{"action":"click","x":701,"y":429,"keys":[],"text":"","seconds":4.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Create named test map","checkpoint":"created_test_map"}`

6. Open editor menu — `{"action":"click","x":35,"y":51,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open editor menu","checkpoint":"editor_menu"}`

7. Open map information — `{"action":"click","x":736,"y":188,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open map information","checkpoint":"map_info"}`

8. Open Data Patches and Assets — `{"action":"click","x":631,"y":607,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open Data Patches and Assets","checkpoint":"assets_dialog_empty"}`

9. Add a datapatch — `{"action":"click","x":748,"y":680,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Add a datapatch","checkpoint":"datapatch_add_options"}`

10. Load datapatch from current clipboard — `{"action":"click","x":646,"y":319,"keys":[],"text":"","seconds":3.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Load datapatch from current clipboard","checkpoint":"load_patch_clipboard"}`

11. Return to map information with datapatch added — `{"action":"click","x":540,"y":680,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Return to map information with datapatch added","checkpoint":"patch_present_before_initial_save"}`

12. Open menu to save map containing datapatch — `{"action":"click","x":36,"y":50,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open menu to save map containing datapatch","checkpoint":""}`

13. Save map with added datapatch — `{"action":"click","x":541,"y":187,"keys":[],"text":"","seconds":3.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Save map with added datapatch","checkpoint":"initial_map_save"}`

14. Open editor menu to remove datapatch — `{"action":"click","x":35,"y":52,"keys":[],"text":"","seconds":0.5,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open editor menu to remove datapatch","checkpoint":""}`

15. Open map information — `{"action":"click","x":740,"y":187,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open map information","checkpoint":""}`

16. Inspect persisted datapatch before deletion — `{"action":"click","x":630,"y":608,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Inspect persisted datapatch before deletion","checkpoint":"persisted_patch_before_delete"}`

17. Request deletion of saved datapatch — `{"action":"click","x":955,"y":176,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Request deletion of saved datapatch","checkpoint":"delete_confirmation"}`

18. Confirm datapatch deletion — `{"action":"click","x":741,"y":404,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Confirm datapatch deletion","checkpoint":"patch_deleted_ui"}`

19. Leave empty datapatch list after deletion — `{"action":"click","x":536,"y":681,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Leave empty datapatch list after deletion","checkpoint":""}`

20. Open editor menu after deletion — `{"action":"click","x":33,"y":51,"keys":[],"text":"","seconds":0.5,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open editor menu after deletion","checkpoint":""}`

21. Save map after datapatch deletion — `{"action":"click","x":540,"y":187,"keys":[],"text":"","seconds":3.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Save map after datapatch deletion","checkpoint":"post_delete_map_save"}`

22. Open editor menu to leave saved map — `{"action":"click","x":35,"y":51,"keys":[],"text":"","seconds":0.5,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open editor menu to leave saved map","checkpoint":""}`

23. Quit editor and return to map list — `{"action":"click","x":641,"y":510,"keys":[],"text":"","seconds":3.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Quit editor and return to map list","checkpoint":"exit_editor_after_deletion"}`

24. Confirm leaving editor after saving deletion — `{"action":"click","x":742,"y":413,"keys":[],"text":"","seconds":5.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Confirm leaving editor after saving deletion","checkpoint":"confirmed_editor_exit"}`

25. Open map editor map list — `{"action":"click","x":257,"y":334,"keys":[],"text":"","seconds":3.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open map editor map list","checkpoint":"returned_map_list"}`

26. Reopen the same custom map after saved deletion — `{"action":"double_click","x":203,"y":261,"keys":[],"text":"","seconds":5.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Reopen the same custom map after saved deletion","checkpoint":"reopened_same_map"}`

27. Open named map in editor for post-reopen inspection — `{"action":"click","x":484,"y":502,"keys":[],"text":"","seconds":5.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open named map in editor for post-reopen inspection","checkpoint":"opened_map_editor_again"}`

28. Open reopened map editor menu — `{"action":"click","x":34,"y":49,"keys":[],"text":"","seconds":0.5,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open reopened map editor menu","checkpoint":""}`

29. Open reopened map information — `{"action":"click","x":736,"y":186,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open reopened map information","checkpoint":""}`

30. Inspect datapatches after reopening same saved map — `{"action":"click","x":627,"y":607,"keys":[],"text":"","seconds":3.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Inspect datapatches after reopening same saved map","checkpoint":"post_reopen_patch_state"}`


## Source findings

The confirmed deletion path removes the PatchAsset only from DataManager's per-type patch Seq and rebuilds the UI. It does not call DataManager.reloadPatches (or otherwise rebuild orderedAssets). Map saving serializes orderedAssets via getAllAssets(), so it can write the stale pre-deletion asset list. On reopen, readDataPatches loads that serialized patch again.

- `core/src/mindustry/editor/data/MapPatchesView.java` / MapPatchesView.build(MapAssetsDialog, Table) trash-button confirmation handler (0.99): This is the most direct source of the reported UI-versus-persisted-state split: the visual list is rebuilt from the now-empty per-type collection, but DataManager's save-facing aggregate can remain stale.

- `core/src/mindustry/mod/DataManager.java` / DataManager.reloadPatches(Seq<PatchAsset>), rebuildOrderedAssets(), and getAllAssets() (0.96): This establishes the stale-cache mechanism connecting the missing reload in the deletion handler to persistence. It also explains why adding/replacing, which calls `reloadPatches`, would not have the same aggregate-list staleness.

- `core/src/mindustry/io/SaveVersion.java` / SaveVersion.writeDataPatches(DataOutput, boolean) / readDataPatches(DataInput, SaveReadState) (0.94): This is the persistence endpoint that makes the in-memory aggregate discrepancy observable after save, exit, and reopen. It is not itself shown to mutate incorrectly; it faithfully serializes its supplied aggregate.

- `core/src/mindustry/editor/data/MapBundlesView.java` / MapBundlesView.build(MapAssetsDialog, Table) trash-button confirmation handler (0.48): This is corroborating evidence of a broader editor asset-removal pattern and may imply an analogous persistence risk for bundles. It is lower ranked because the reported replay deletes a datapatch, not a bundle.


Limitations: Only source was inspected; no game client was run and no supplied screenshot, ZIP, map-save bytes, or runtime logs were available through the tools.; The report identifies Android/build BE 27790 while source provenance relative to the replay commit was not independently established. The control/data flow in the inspected source nevertheless directly matches the supplied deterministic replay.; This localizes a cause consistent with the report, but does not determine the future human fix or prove whether other asset types are intended to refresh their runtime loaders on deletion.


## Validation

- Regression before patch: **pass** — Bug oracle triggered in 5/5 clean runs; the regression therefore fails on the pre-fix build.

- Candidate build: **pass** — Build exit code 0

- Existing tests: **pass** — Test exit code 0.

- Original replay after patch: **pass** — 5/5 reached expected state without the symptom; bug seen 0 times.

- Smoke test: **pass** — Clean desktop launch and live process after startup; deeper gameplay smoke coverage is not implemented.


## Proposed patch


### Why this patch should work

Cause: the delete confirmation at MapPatchesView.java:84-89 removes the PatchAsset from the mutable per-type sequence returned by `state.data.getPatches()` but only rebuilds the dialog. `DataManager` maintains a separate `orderedAssets` aggregate: `reloadPatches()` rebuilds it (DataManager.java:169-176), while `getAllAssets()` returns that aggregate directly (DataManager.java:263-265). Saving serializes `getAllAssets()` (SaveVersion.java:595-601), so without a reload the save can still contain the deleted patch and loading restores it.

The added line calls the same patch reload path already used after add/replace in MapPatchesView.java:125-143. It unapplies the old patch effects, applies the remaining patches, and rebuilds `orderedAssets`. Thus the save-facing aggregate no longer includes the deleted PatchAsset before the UI is rebuilt, so a subsequent map save should persist the deletion.

This is a one-line, datapatch-only change in the confirmed deletion handler; it does not alter serialization, save format, the regression oracle, or unrelated asset behavior.


### Risks and tradeoffs

- Deleting a patch now immediately reapplies all remaining patches. This is consistent with add/replace behavior, but reviewers should verify that removing a patch is intended to revert its runtime content effects immediately, not only update persisted editor state.

- `reloadPatches` may have a perceptible cost or expose errors from remaining malformed patches at deletion time; this follows the established add/replace path and is preferable to retaining stale serialized state.

- Other asset editors may have analogous stale-aggregate deletion paths, but they are deliberately out of scope for this datapatch replay and are not changed.


## Usage

80 model calls; 926267 input and 15071 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
