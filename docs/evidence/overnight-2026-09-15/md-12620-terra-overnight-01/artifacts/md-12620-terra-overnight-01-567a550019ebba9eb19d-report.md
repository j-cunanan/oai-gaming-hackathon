# REPRO — Persistent Datapatch bug


Status: **INSUFFICIENT_EVIDENCE**


Observed in 3/5 fresh replays. A stable trigger still needs investigation.


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


## Reproduction

3/5 successful clean replays. 34 → 34 actions (bounded reduction, not a proof of global minimality).

1. Open the map editor from the main menu. — `{"action":"click","x":262,"y":334,"keys":[],"text":"","seconds":2.0,"scroll_y":0,"button":"left","semantic":"Open the map editor from the main menu.","checkpoint":"editor_menu"}`

2. Create a new editor map. — `{"action":"click","x":641,"y":681,"keys":[],"text":"","seconds":2.0,"scroll_y":0,"button":"left","semantic":"Create a new editor map.","checkpoint":"new_map_dialog"}`

3. Focus the new map name field. — `{"action":"click","x":668,"y":322,"keys":[],"text":"","seconds":0.2,"scroll_y":0,"button":"left","semantic":"Focus the new map name field.","checkpoint":""}`

4. Name the new map for the datapatch persistence test. — `{"action":"type","x":668,"y":322,"keys":[],"text":"datapatch-repro","seconds":0.2,"scroll_y":0,"button":"left","semantic":"Name the new map for the datapatch persistence test.","checkpoint":""}`

5. Navigate focus to the map-name input. — `{"action":"keypress","x":0,"y":0,"keys":["tab"],"text":"","seconds":0.2,"scroll_y":0,"button":"left","semantic":"Navigate focus to the map-name input.","checkpoint":""}`

6. Focus map-name field. — `{"action":"click","x":699,"y":352,"keys":[],"text":"","seconds":0.2,"scroll_y":0,"button":"left","semantic":"Focus map-name field.","checkpoint":""}`

7. Enter a map name. — `{"action":"type","x":699,"y":352,"keys":[],"text":"datapatch-repro","seconds":0.3,"scroll_y":0,"button":"left","semantic":"Enter a map name.","checkpoint":""}`

8. Confirm creation of the editor map. — `{"action":"click","x":705,"y":428,"keys":[],"text":"","seconds":3.0,"scroll_y":0,"button":"left","semantic":"Confirm creation of the editor map.","checkpoint":""}`

9. Open editor actions menu to locate map data assets. — `{"action":"click","x":33,"y":50,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Open editor actions menu to locate map data assets.","checkpoint":""}`

10. Open Map Info where map assets are configured. — `{"action":"click","x":735,"y":185,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Open Map Info where map assets are configured.","checkpoint":""}`

11. Open the map Data Patches and Assets editor. — `{"action":"click","x":635,"y":606,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Open the map Data Patches and Assets editor.","checkpoint":""}`

12. Add a datapatch to the map. — `{"action":"click","x":745,"y":680,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Add a datapatch to the map.","checkpoint":""}`

13. Choose datapatch import from clipboard. — `{"action":"click","x":643,"y":321,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Choose datapatch import from clipboard.","checkpoint":""}`

14. Confirm the newly added datapatch is visibly listed before saving. — `{"action":"wait","x":0,"y":0,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Confirm the newly added datapatch is visibly listed before saving.","checkpoint":"patch_added"}`

15. Return from the datapatches list to map information. — `{"action":"click","x":540,"y":681,"keys":[],"text":"","seconds":0.5,"scroll_y":0,"button":"left","semantic":"Return from the datapatches list to map information.","checkpoint":""}`

16. Open editor actions. — `{"action":"click","x":34,"y":50,"keys":[],"text":"","seconds":0.4,"scroll_y":0,"button":"left","semantic":"Open editor actions.","checkpoint":""}`

17. Save map with the added datapatch. — `{"action":"click","x":544,"y":186,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Save map with the added datapatch.","checkpoint":"patch_initial_save"}`

18. Open actions to return to map data assets. — `{"action":"click","x":33,"y":51,"keys":[],"text":"","seconds":0.3,"scroll_y":0,"button":"left","semantic":"Open actions to return to map data assets.","checkpoint":""}`

19. Open map info. — `{"action":"click","x":739,"y":187,"keys":[],"text":"","seconds":0.5,"scroll_y":0,"button":"left","semantic":"Open map info.","checkpoint":""}`

20. Open datapatches list for removal. — `{"action":"click","x":623,"y":608,"keys":[],"text":"","seconds":0.5,"scroll_y":0,"button":"left","semantic":"Open datapatches list for removal.","checkpoint":""}`

21. Delete the listed datapatch. — `{"action":"click","x":955,"y":178,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Delete the listed datapatch.","checkpoint":"patch_delete_transition"}`

22. Confirm datapatch deletion and verify the list becomes empty. — `{"action":"click","x":742,"y":403,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Confirm datapatch deletion and verify the list becomes empty.","checkpoint":"patch_deleted"}`

23. Return to editor after deleting the datapatch. — `{"action":"click","x":536,"y":681,"keys":[],"text":"","seconds":0.3,"scroll_y":0,"button":"left","semantic":"Return to editor after deleting the datapatch.","checkpoint":""}`

24. Open editor actions to save the deletion. — `{"action":"click","x":34,"y":51,"keys":[],"text":"","seconds":0.3,"scroll_y":0,"button":"left","semantic":"Open editor actions to save the deletion.","checkpoint":""}`

25. Save the map after datapatch deletion. — `{"action":"click","x":543,"y":186,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Save the map after datapatch deletion.","checkpoint":"patch_deleted_save"}`

26. Open menu to exit the editor. — `{"action":"click","x":32,"y":51,"keys":[],"text":"","seconds":0.3,"scroll_y":0,"button":"left","semantic":"Open menu to exit the editor.","checkpoint":""}`

27. Quit the editor after saving the deletion. — `{"action":"click","x":639,"y":510,"keys":[],"text":"","seconds":2.0,"scroll_y":0,"button":"left","semantic":"Quit the editor after saving the deletion.","checkpoint":"editor_exit_after_delete"}`

28. Confirm exiting the saved editor session. — `{"action":"click","x":742,"y":411,"keys":[],"text":"","seconds":3.0,"scroll_y":0,"button":"left","semantic":"Confirm exiting the saved editor session.","checkpoint":""}`

29. Return to the map editor map list. — `{"action":"click","x":263,"y":334,"keys":[],"text":"","seconds":2.0,"scroll_y":0,"button":"left","semantic":"Return to the map editor map list.","checkpoint":""}`

30. Reopen the same custom map after saving the deletion. — `{"action":"double_click","x":208,"y":258,"keys":[],"text":"","seconds":3.0,"scroll_y":0,"button":"left","semantic":"Reopen the same custom map after saving the deletion.","checkpoint":"map_reopened"}`

31. Open the saved map in editor to inspect loaded datapatches. — `{"action":"click","x":490,"y":502,"keys":[],"text":"","seconds":3.0,"scroll_y":0,"button":"left","semantic":"Open the saved map in editor to inspect loaded datapatches.","checkpoint":""}`

32. Open map info after reopening. — `{"action":"click","x":34,"y":51,"keys":[],"text":"","seconds":0.3,"scroll_y":0,"button":"left","semantic":"Open map info after reopening.","checkpoint":""}`

33. View reopened map information. — `{"action":"click","x":738,"y":187,"keys":[],"text":"","seconds":0.5,"scroll_y":0,"button":"left","semantic":"View reopened map information.","checkpoint":""}`

34. Inspect datapatches after reopening the saved map. — `{"action":"click","x":631,"y":607,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Inspect datapatches after reopening the saved map.","checkpoint":"reopened_patch_absent"}`


## Usage

46 model calls; 422239 input and 8123 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
