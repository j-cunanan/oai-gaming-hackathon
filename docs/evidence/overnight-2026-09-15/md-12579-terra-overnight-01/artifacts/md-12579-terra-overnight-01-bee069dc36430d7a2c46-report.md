# REPRO — Target Dummies crash the game when saved in editor


Status: **AWAITING_HUMAN**


Candidate ready for review. Validation is incomplete or failed; inspect the recorded checks before using the patch.


Game: mindustry · revision `f7ededb3a1950c396e5c113d96a19dd88e71da9a`


## Player report

### Platforms

Windows

### Build

bleeding-edge build 27733

### Issue

If a Target Dummy is placed in the editor and the map is saved, the game crashes. The map also causes an error if it is attempted to be loaded afterwards.

### Steps to reproduce

1. Place a target dummy in the editor
2. Save the map

### Mods used

None

### Save file

(As described above, this map is unloadable in-game.)
[dummy.zip](https://github.com/user-attachments/files/31756506/dummy.zip)

### (Crash) logs

[crash-report-09_02_2026_16_06_14.txt](https://github.com/user-attachments/files/31756477/crash-report-09_02_2026_16_06_14.txt)


## Reproduction

5/5 successful clean replays. 15 → 12 actions (bounded reduction, not a proof of global minimality).

1. Open Editor from main menu — `{"action":"click","x":253,"y":335,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open Editor from main menu","checkpoint":"open-editor"}`

2. Create a new editor map — `{"action":"click","x":640,"y":680,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Create a new editor map","checkpoint":"new-map-dialog"}`

3. Focus the modal map name input underline — `{"action":"click","x":640,"y":383,"keys":[],"text":"","seconds":0.2,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Focus the modal map name input underline","checkpoint":""}`

4. Input new blank map name — `{"action":"type","x":null,"y":null,"keys":[],"text":"DummySaveTest","seconds":0.3,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Input new blank map name","checkpoint":"map-name-entered"}`

5. Confirm creation of blank map — `{"action":"click","x":704,"y":429,"keys":[],"text":"","seconds":3.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Confirm creation of blank map","checkpoint":"blank-editor"}`

6. Switch editor palette to block placement — `{"action":"click","x":94,"y":225,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Switch editor palette to block placement","checkpoint":""}`

7. Focus editor block search — `{"action":"click","x":1112,"y":43,"keys":[],"text":"","seconds":0.2,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Focus editor block search","checkpoint":""}`

8. Search for Target Dummy block — `{"action":"type","x":null,"y":null,"keys":[],"text":"Target Dummy","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Search for Target Dummy block","checkpoint":"target-dummy-search"}`

9. Select Target Dummy block from results — `{"action":"click","x":1165,"y":133,"keys":[],"text":"","seconds":0.3,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Select Target Dummy block from results","checkpoint":""}`

10. Place selected Target Dummy on blank map — `{"action":"click","x":600,"y":370,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Place selected Target Dummy on blank map","checkpoint":"target-dummy-placed"}`

11. Open editor map menu to save — `{"action":"click","x":35,"y":52,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open editor map menu to save","checkpoint":""}`

12. Save map containing Target Dummy — `{"action":"click","x":548,"y":186,"keys":[],"text":"","seconds":5.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Save map containing Target Dummy","checkpoint":"save-target-dummy"}`


## Source findings

TargetDummy.TargetDummyBuild.write dereferences unitTeam without a null check (`write.i(unitTeam.id)`). `unitTeam` is declared without initialization and is only defaulted to the building's team in `updateTile`; consequently, a newly placed dummy whose update/defaulting has not occurred can throw NullPointerException while map serialization invokes its write method. This exactly matches the supplied oracle frame at TargetDummy.java:271. The failed write can leave the just-written map incomplete, which is a supported explanation for the reported later load error, but the exact load error was not supplied.

- `core/src/mindustry/world/blocks/defense/TargetDummy.java` / TargetDummy.TargetDummyBuild.write(Writes) (0.99): This is the direct crash site named by the empirical oracle and contains a concrete null dereference consistent with the newly placed editor building state. It is the primary localization; no future fix is inferred.

- `core/src/mindustry/io/SaveVersion.java` / SaveVersion.writeMap(DataOutput) block/entity serialization loop (lines 238-289) (0.85): This is the verified caller/path that turns the Target Dummy state defect into an editor save crash. It does not itself create the null value.

- `core/src/mindustry/io/SaveVersion.java` / SaveVersion.readMap(DataInput, SaveReadState) block/entity deserialization loop (lines 321-395) (0.58): This is the likely path for the reported post-crash load error, but without the produced map or exact load stack trace it cannot be established whether the file is partial, or what read failure occurs.

- `core/src/mindustry/io/MapIO.java` / MapIO.writeMap(Fi, Map, boolean) (0.42): Relevant error propagation boundary for editor map saving, but no evidence indicates it mishandles the exception or causes the invalid state.


Limitations: No crash report, full stack trace, generated map artifact, or exact load-error text was available to inspect.; The supplied source does establish the crash-site null dereference and serializer call chain, but does not by itself prove the exact editor scheduling condition that leaves `unitTeam` null in every reproduction.; The subsequent load failure is localized only as a probable consequence of interrupted/corrupt output; its specific parser failure remains unverified.; Build 27733-to-commit correspondence and Windows-specific runtime details were not independently verified.


## Validation

- Regression before patch: **pass** — Bug oracle triggered in 5/5 clean runs; the regression therefore fails on the pre-fix build.

- Candidate build: **pass** — Build exit code 0

- Existing tests: **fail** — Test exit code 1. Failing tests: :tests:test::ModTestAllure.begin(). Network-enabled candidate failures cannot be waived by an offline baseline.

- Original replay after patch: **fail** — 1/5 reached expected state without the symptom; bug seen 0 times.

- Smoke test: **pass** — Clean desktop launch and live process after startup; deeper gameplay smoke coverage is not implemented.


## Proposed patch


### Why this patch should work

Cause: `unitTeam` is declared without an initial value (line 91) and is normally defaulted from the building team only in `updateTile()` (line 107). `write()` can run before that update, but line 271 unconditionally reads `unitTeam.id`, causing the reported null-pointer crash while saving a newly placed Target Dummy.

The changed serialization line writes the building's `team.id` when `unitTeam` has not yet been initialized; otherwise it writes the explicitly selected dummy team exactly as before. The building team is the same default `updateTile()` would assign, so the saved value preserves the intended default and lets the map save complete rather than leaving a partial output.

This is a one-line, local serialization guard. It keeps the existing save format (one integer in the same position), so no map format/version change is required. Validation should run the existing replay and also verify both a newly placed default dummy and a dummy configured to another team save and reload with their expected teams.


### Risks and tradeoffs

- This relies on `team` being initialized for a building being serialized. That is the existing default source used in `updateTile()` and should hold for placed map buildings, but malformed manually constructed objects are not addressed.

- The patch prevents this specific write-time null dereference; it does not establish the exact cause of any already-corrupted map load failure. Previously interrupted/truncated map files may remain unreadable and should be regenerated.

- Other pre-update code paths that dereference `unitTeam` (for example configuration UI) are intentionally unchanged because the confirmed regression is the serialization crash.


## Usage

64 model calls; 528798 input and 7478 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
