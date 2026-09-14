# REPRO — [Original test maps] Derelict conveyor loses current payload on reload


Status: **INSUFFICIENT_EVIDENCE**


Both supplied maps were imported through the editor and inspected. cargo-test-map.msav (shown as “test map”) did run: hovering its large transport block identified “Payload Conveyor — Derelict,” and a nearby visible object identified as “World Processor.” I saved that running scene as first-fixture-derelict-test, loaded the same save, and the post-load view still showed both the Derelict conveyor and the World Processor; no disappearance was visible in that ambiguous scene. However, the UI inspection did not establish that the visible World Processor was actually the conveyor’s current carried payload rather than a separate placed building. cargo-mix-tech.msav (shown as “mix tech”) ran with a Shard core and terrain/resource clusters; its inspected dark marks identified as Coal and no payload conveyor/block-payload setup was found. I also created a separate controlled map and placed a Derelict Payload Conveyor, but did not complete a source/payload/save/load cycle before the investigation limit.


Game: mindustry · revision `2c066e9c8c7e153e4eb91d730ead02e9011edd75`


## Player report

### Platforms

Windows

### Build

release build 159.3

### Issue

derelict payload conveyors lose their current payload (blocks) after restarting the map or reloading the save

(originally this was a suggestion to rework payload conveyors, but I decided to issue this as a bug instead)

### Steps to reproduce

1.) Place block on payload conveyor and make sure it's derelict
2.) Save game
3.) Load game
4.) See results

### Mods used

_No response_

### Save file

[mindustry-data-export.zip](https://github.com/user-attachments/files/29970021/mindustry-data-export.zip)

### (Crash) logs

_No response_

### REPRO supplied original files (explicit input selection)

This fresh attempt receives two unchanged maps extracted from the report's linked mindustry-data-export.zip: maps/test map.msav as /workspace/fixtures/cargo-test-map.msav, and maps/mix tech.msav as /workspace/fixtures/cargo-mix-tech.msav. They were selected because they are small, named test scenes (both 200x200); it is not known which map best demonstrates the report. Their save envelopes are version 13, build tag 159, and list no active mods. Import and inspect the first test map through the game's editor UI before constructing an unrelated scene. The fixture copies are restored identically before each fresh run.

The full original archive also includes larger maps, save slots, settings and a mod ZIP. Those other files are not installed in this case. The two selected maps' mods tags are empty, which is narrower than proving that the reporter never used mods. If either map fails to load or lacks the needed setup, record that limitation.

The previous report-only attempt never established a payload on a Derelict conveyor and never saved/reloaded. This is a new context with supplied original inputs, not a successful continuation of that attempt. Require visible payload and Derelict ownership before the save, and inspect the same location after reopening. Normal unloading, a map that was already empty, or a unit remaining in payload form does not establish the reported loss. These notes do not supply a source diagnosis or fix.



## Usage

90 model calls; 1820608 input and 22361 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
