# REPRO — [Prepared setup] Unit disappears when entering payload conveyor


Status: **FAILED**


OpenAI request failed: APITimeoutError (code=None) Inspect worker-error.log in Evidence for details.


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



## Usage

91 model calls; 3171654 input and 23763 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
