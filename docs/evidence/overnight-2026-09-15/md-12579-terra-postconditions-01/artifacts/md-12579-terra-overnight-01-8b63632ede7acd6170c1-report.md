# REPRO — Target Dummies crash the game when saved in editor


Status: **INSUFFICIENT_EVIDENCE**


source localization reached its 12-turn budget; partial evidence is preserved


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

1. Open Editor from main menu — `{"action":"click","x":253,"y":335,"keys":[],"text":"","seconds":2.0,"scroll_y":0,"button":"left","semantic":"Open Editor from main menu","checkpoint":"open-editor"}`

2. Create a new editor map — `{"action":"click","x":640,"y":680,"keys":[],"text":"","seconds":2.0,"scroll_y":0,"button":"left","semantic":"Create a new editor map","checkpoint":"new-map-dialog"}`

3. Focus the modal map name input underline — `{"action":"click","x":640,"y":383,"keys":[],"text":"","seconds":0.2,"scroll_y":0,"button":"left","semantic":"Focus the modal map name input underline","checkpoint":""}`

4. Input new blank map name — `{"action":"type","x":null,"y":null,"keys":[],"text":"DummySaveTest","seconds":0.3,"scroll_y":0,"button":"left","semantic":"Input new blank map name","checkpoint":"map-name-entered"}`

5. Confirm creation of blank map — `{"action":"click","x":704,"y":429,"keys":[],"text":"","seconds":3.0,"scroll_y":0,"button":"left","semantic":"Confirm creation of blank map","checkpoint":"blank-editor"}`

6. Switch editor palette to block placement — `{"action":"click","x":94,"y":225,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Switch editor palette to block placement","checkpoint":""}`

7. Focus editor block search — `{"action":"click","x":1112,"y":43,"keys":[],"text":"","seconds":0.2,"scroll_y":0,"button":"left","semantic":"Focus editor block search","checkpoint":""}`

8. Search for Target Dummy block — `{"action":"type","x":null,"y":null,"keys":[],"text":"Target Dummy","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Search for Target Dummy block","checkpoint":"target-dummy-search"}`

9. Select Target Dummy block from results — `{"action":"click","x":1165,"y":133,"keys":[],"text":"","seconds":0.3,"scroll_y":0,"button":"left","semantic":"Select Target Dummy block from results","checkpoint":""}`

10. Place selected Target Dummy on blank map — `{"action":"click","x":600,"y":370,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Place selected Target Dummy on blank map","checkpoint":"target-dummy-placed"}`

11. Open editor map menu to save — `{"action":"click","x":35,"y":52,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Open editor map menu to save","checkpoint":""}`

12. Save map containing Target Dummy — `{"action":"click","x":548,"y":186,"keys":[],"text":"","seconds":5.0,"scroll_y":0,"button":"left","semantic":"Save map containing Target Dummy","checkpoint":"save-target-dummy"}`


## Usage

41 model calls; 379653 input and 3777 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
