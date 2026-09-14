# REPRO — [Setup guided] Unit disappears when entering payload conveyor


Status: **INSUFFICIENT_EVIDENCE**


Could not test the reported payload-entry behavior. In sandbox, a Payload Conveyor was identified and placed, but a valid ground unit payload and a connected output route were not configured. No unit entering a conveyor, disappearance, destruction, or downstream emergence was observed.


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



## Usage

37 model calls; 420738 input and 5051 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
