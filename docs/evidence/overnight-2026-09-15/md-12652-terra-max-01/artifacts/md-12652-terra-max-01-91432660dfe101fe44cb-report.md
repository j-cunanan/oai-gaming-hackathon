# REPRO — Crash in Data Patches & Assets UI


Status: **NOT_REPRODUCED**


Imported the supplied WotM.msav through the game UI, opened it in the editor, entered in-game editor mode, made a tile edit, quit back to the editor, opened Map Info > Data Patches & Assets, visited Patches, Content, Locale Bundles, Images, Sounds, and Music, then pressed Escape. The game remained running with no visible error and an empty captured log. A second immediate Content-tab-to-Escape close also remained stable.


Game: mindustry · revision `89527f879b535b752376d9b935172be576320b59`


## Player report

### Platforms

Mac

### Build

160.2

### Issue

I randomly crashed while trying to reproduce what i thought was a patcheditor mod issue when it was disabled.

### Steps to reproduce

Open a map with datapatched content and new content
edit map in-game, Quit
open editor menu->data patches & assets
i then clicked on the different tabs
press escape

### Mods used

~~testing utils, schembrowser, floodcompat, claj when it happened; all multiplayer-compatible mods uninvolved with datapatches and the crash's source~~ none

### Save file

[WotM.msav.zip](https://github.com/user-attachments/files/32153827/WotM.msav.zip)

### (Crash) logs

modded; [crash-report-09_12_2026_22_19_04.txt](https://github.com/user-attachments/files/32153802/crash-report-09_12_2026_22_19_04.txt)
unmodded; [crash-report-09_12_2026_22_52_19.txt](https://github.com/user-attachments/files/32153925/crash-report-09_12_2026_22_52_19.txt)

Provided original player attachment: WotM.msav. The unmodified map is registered as a fixture and available at /workspace/fixtures/WotM.msav for import through the game UI. This supplies the original report attachment; it adds no fix or source diagnosis.


## Usage

69 model calls; 1828088 input and 15301 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
