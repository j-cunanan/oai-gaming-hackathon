# REPRO — [Recorded trigger + operator scroll calibration] Unit disappears on payload entry


Status: **INSUFFICIENT_EVIDENCE**


Calibrated supplied trigger confirmed in 0/1 completed fresh verdicts; 5/5 was required. Source analysis and patching did not start.


Game: mindustry · revision `7e80948b58138a569e119857e0add95762d7e0bb`


## Player report

### Platforms

Windows

### Build

27713

### Issue

Unit disappears when entering payload conveyor

### Steps to reproduce

Using RTS or manually control a unit entering a payload conveyor.

### Mods used

none

### Save file

Any save

### (Crash) logs

_No response_

### REPRO setup assistance (not part of the upstream report)

A prior local attempt did not obtain a ground unit, so the entry transition was never tested. These notes concern setup and controls only; the original reported symptom above is unchanged.

- In this pre-fix source, core/src/mindustry/world/blocks/payloads/PayloadSource.java supports both Block and UnitType configuration. The vanilla sandbox Payload Source can supply a test unit without building a factory supply chain. Verify its actual unit output before trying the reported trigger, and keep the test scene small.
- core/src/mindustry/game/Gamemode.java distinguishes sandbox (infinite resources) from editor (also instant construction). The editor menu's Edit in Game action is implemented by MapEditorDialog.editInGame. This can help create a setup, but record the mode/rules and perform the actual report test in normal play; setup shortcuts must not manufacture the symptom.
- core/src/mindustry/input/Binding.java defines Ctrl for direct unit control, Shift for command mode, and E for pausing/resuming construction. Inspect the source or Controls screen if unsure. A placement outline is not proof that construction completed.
- The updated input worker supports keys on pointer actions (for example Ctrl-click), plus hold_seconds on keypress for sustained movement. seconds alone is a wait after releasing the keys.
- A unit entering a payload can legitimately stop being drawn as a walking unit. Check the connected transport/output and the same unit's continued existence; do not count normal payload transport as disappearance.


### REPRO operator-prepared saved scene (explicit additional assistance)

This variant begins from a small prepared SAVE GAME supplied at /workspace/fixtures/operator-unit-setup.msav. It is not an original player attachment. Import it using Play > Load Game > Import Save (follow the actual UI labels), then load the saved game. Importing it only as an editor map may omit the saved unit entities, so verify that the units are present in gameplay.

The scene was constructed with the unchanged historical game's normal objects and native SaveIO serializer. It uses a flat 160x120 stone map, a friendly Sharded core and normal Sandbox rules (editor=false, infinite resources=true, reactor explosions=true, no automatic wave timer). The construction audit saved and reloaded the file and checked healthy initial objects and empty conveyors. This is a precondition audit, not a bug reproduction, candidate test or an AI result. There is no damaged, dead or ghost object embedded in the file.

The scene has three healthy Dagger ground units near tiles (84,56), (84,60) and (84,64), and three connected, empty, right-facing Payload Conveyors at (90,60), (93,60) and (96,60), with clear space beyond the output. Camera metadata is near tile (86,60), but choose coordinates from the actual screenshot. The three units allow the AI to inspect the setup and select one specific subject; they are not three independent bug trials.

First identify a ground unit and the empty transport route. Then use direct control or an actual unit command to test the report's entry transition. Preserve evidence of the same subject before entry, on the transport route, and after it should exit. Becoming a payload and temporarily disappearing from the walking-unit view is normal; determine whether the unit actually gets lost. No transport step or bug state is embedded in the initial file, and no root-cause diagnosis or future patch was supplied.


### Recorded-trigger input and explicit operator checkpoint selection

This variant starts with the first 33 actual desktop actions recorded by the earlier prepared-scene AI investigation md-12565-terra-prepared-03. That run reached an RTS Enter Payload Block transition, then its final verifier timed out. The operator selected five existing recorded checkpoint labels from that RTS segment for a separate visual audit. This selection is additional assistance; it is not the unavailable original final oracle and is not a new autonomous discovery. The later direct-control detour is outside this selected prefix.

The selected input sequence must now be replayed on five fresh profiles and independently verified before source diagnosis or a patch can begin. Retained-image review alone does not establish repeated reproduction. The prior failed case remains unchanged. No source diagnosis, historical fixed revision or developer patch is supplied. This run's time-to-proof excludes the earlier exploration that produced the supplied trace.


### Additional operator input calibration

A fresh replay of the supplied 33-action recording had a different zoom level and missed the selected unit. A separate infrastructure probe found that burst wheel inputs can collapse within the Arc backend update. Protocol 4 paces individual wheel detents. This variant changes only scroll_y at supplied action 10 from -8 to -2 and action 11 from -8 to -1, requesting three actual zoom detents to match the earlier recorded geometry. All other recorded action parameters and the five selected checkpoint labels are unchanged. This is operator calibration of a supplied trace, not a new autonomous discovery. Fresh images must independently establish the selected subject, actual entry and reported outcome before any source diagnosis or patching. No historical game fix is supplied.



## Reproduction

0/1 successful clean replays. 33 → 33 actions (bounded reduction, not a proof of global minimality).

1. Open Play menu to access Load Game and import the supplied prepared save. — `{"action":"click","x":252,"y":197,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open Play menu to access Load Game and import the supplied prepared save.","checkpoint":""}`

2. Open Load Game dialog. — `{"action":"click","x":475,"y":405,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open Load Game dialog.","checkpoint":""}`

3. Choose Import Save to load the operator-prepared fixture as saved gameplay state. — `{"action":"click","x":748,"y":680,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Choose Import Save to load the operator-prepared fixture as saved gameplay state.","checkpoint":""}`

4. Wait for save-file chooser after activating Import Save. — `{"action":"wait","x":null,"y":null,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Wait for save-file chooser after activating Import Save.","checkpoint":""}`

5. Focus the save chooser filename field. — `{"action":"click","x":611,"y":459,"keys":[],"text":"","seconds":0.5,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Focus the save chooser filename field.","checkpoint":""}`

6. Enter the supplied operator fixture path. — `{"action":"type","x":null,"y":null,"keys":[],"text":"/workspace/fixtures/operator-unit-setup.msav","seconds":0.5,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Enter the supplied operator fixture path.","checkpoint":""}`

7. Import the selected supplied save file. — `{"action":"click","x":802,"y":458,"keys":[],"text":"","seconds":4.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Import the selected supplied save file.","checkpoint":""}`

8. Load the imported operator-prepared sandbox save into gameplay. — `{"action":"click","x":614,"y":380,"keys":[],"text":"","seconds":8.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Load the imported operator-prepared sandbox save into gameplay.","checkpoint":""}`

9. Toggle menus off to inspect units and the transport route without the build panel obscuring the view. — `{"action":"keypress","x":null,"y":null,"keys":["c"],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Toggle menus off to inspect units and the transport route without the build panel obscuring the view.","checkpoint":""}`

10. Zoom out around the units to locate the connected conveyor route and verify initial scene geometry. — `{"action":"scroll","x":956,"y":369,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":-2,"button":"left","semantic":"Zoom out around the units to locate the connected conveyor route and verify initial scene geometry.","checkpoint":""}`

11. Further zoom out centered on the conveyor intake so the full connected route and clear output can be inspected. — `{"action":"scroll","x":1145,"y":369,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":-1,"button":"left","semantic":"Further zoom out centered on the conveyor intake so the full connected route and clear output can be inspected.","checkpoint":""}`

12. Enter RTS command mode and select the middle Dagger, keeping the other two units as visual controls. — `{"action":"click","x":855,"y":369,"keys":["shift"],"text":"","seconds":2.0,"hold_seconds":0.2,"scroll_y":0,"button":"left","semantic":"Enter RTS command mode and select the middle Dagger, keeping the other two units as visual controls.","checkpoint":""}`

13. Restore HUD to inspect RTS command controls and selection state. — `{"action":"keypress","x":null,"y":null,"keys":["c"],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Restore HUD to inspect RTS command controls and selection state.","checkpoint":""}`

14. Open pause menu to inspect command-mode control settings without altering the scene. — `{"action":"keypress","x":null,"y":null,"keys":["esc"],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open pause menu to inspect command-mode control settings without altering the scene.","checkpoint":""}`

15. Open settings to inspect the RTS command-mode behavior. — `{"action":"click","x":754,"y":292,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open settings to inspect the RTS command-mode behavior.","checkpoint":""}`

16. Open control settings to locate command mode configuration. — `{"action":"click","x":648,"y":414,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open control settings to locate command mode configuration.","checkpoint":""}`

17. Return to settings categories. — `{"action":"click","x":633,"y":680,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Return to settings categories.","checkpoint":""}`

18. Open game settings to locate command-mode hold/toggle setting. — `{"action":"click","x":640,"y":175,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Open game settings to locate command-mode hold/toggle setting.","checkpoint":""}`

19. Toggle the Hold For Command Mode option to expose its current state and enable a persistent command-mode test workflow if needed. — `{"action":"click","x":400,"y":625,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Toggle the Hold For Command Mode option to expose its current state and enable a persistent command-mode test workflow if needed.","checkpoint":""}`

20. Set command mode back to toggle behavior so its UI can remain visible after activating it. — `{"action":"click","x":400,"y":625,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Set command mode back to toggle behavior so its UI can remain visible after activating it.","checkpoint":""}`

21. Toggle Hold For Command Mode off using its row to retain a persistent RTS mode for inspection. — `{"action":"click","x":555,"y":625,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Toggle Hold For Command Mode off using its row to retain a persistent RTS mode for inspection.","checkpoint":""}`

22. Move pointer away from the setting to distinguish hover highlighting from its actual toggle state. — `{"action":"move","x":1000,"y":100,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Move pointer away from the setting to distinguish hover highlighting from its actual toggle state.","checkpoint":""}`

23. Exit game settings after enabling toggle-style RTS command mode. — `{"action":"click","x":642,"y":679,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Exit game settings after enabling toggle-style RTS command mode.","checkpoint":""}`

24. Return to paused gameplay. — `{"action":"click","x":640,"y":680,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Return to paused gameplay.","checkpoint":""}`

25. Resume the loaded sandbox scene for the RTS transport test. — `{"action":"click","x":526,"y":291,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Resume the loaded sandbox scene for the RTS transport test.","checkpoint":""}`

26. Activate persistent RTS command mode using the configured Shift binding. — `{"action":"keypress","x":null,"y":null,"keys":["shift"],"text":"","seconds":2.0,"hold_seconds":0.1,"scroll_y":0,"button":"left","semantic":"Activate persistent RTS command mode using the configured Shift binding.","checkpoint":""}`

27. Capture the pre-entry state: one outlined middle Dagger is selected in Command Mode and the right-facing payload conveyor route is visibly empty. — `{"action":"wait","x":null,"y":null,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Capture the pre-entry state: one outlined middle Dagger is selected in Command Mode and the right-facing payload conveyor route is visibly empty.","checkpoint":"rts_pre_entry_subject_selected"}`

28. Choose the selected Dagger's Enter Payload Block command in Command Mode. — `{"action":"click","x":1028,"y":612,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Choose the selected Dagger's Enter Payload Block command in Command Mode.","checkpoint":"rts_enter_payload_command_selected"}`

29. Assign the selected Dagger's Enter Payload Block target to the leftmost intake of the connected right-facing conveyor route. — `{"action":"click","x":938,"y":369,"keys":[],"text":"","seconds":0.5,"hold_seconds":0.0,"scroll_y":0,"button":"right","semantic":"Assign the selected Dagger's Enter Payload Block target to the leftmost intake of the connected right-facing conveyor route.","checkpoint":"rts_payload_intake_target_assigned"}`

30. Observe the selected Dagger as it reaches the commanded payload-conveyor intake. — `{"action":"wait","x":null,"y":null,"keys":[],"text":"","seconds":1.2,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Observe the selected Dagger as it reaches the commanded payload-conveyor intake.","checkpoint":"rts_unit_reaches_payload_intake"}`

31. Observe the route during expected payload transport after the walking Dagger has entered. — `{"action":"wait","x":null,"y":null,"keys":[],"text":"","seconds":1.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Observe the route during expected payload transport after the walking Dagger has entered.","checkpoint":"rts_payload_transporting"}`

32. Allow sufficient time for a unit payload to traverse all three connected conveyors and emerge at the clear output. — `{"action":"wait","x":null,"y":null,"keys":[],"text":"","seconds":2.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Allow sufficient time for a unit payload to traverse all three connected conveyors and emerge at the clear output.","checkpoint":"rts_payload_expected_output"}`

33. Continue observing well beyond the normal conveyor traversal interval to distinguish a delayed output from a stuck or lost unit. — `{"action":"wait","x":null,"y":null,"keys":[],"text":"","seconds":8.0,"hold_seconds":0.0,"scroll_y":0,"button":"left","semantic":"Continue observing well beyond the normal conveyor traversal interval to distinguish a delayed output from a stuck or lost unit.","checkpoint":"rts_no_visible_output_after_extended_wait"}`


## Usage

1 model calls; 7685 input and 3449 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
