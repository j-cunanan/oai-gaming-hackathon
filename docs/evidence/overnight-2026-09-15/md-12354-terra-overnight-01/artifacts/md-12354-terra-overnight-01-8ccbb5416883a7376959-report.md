# REPRO — Derelict Payload conveyors do not save current payload


Status: **INSUFFICIENT_EVIDENCE**


Could not complete a save/load reproduction. A new controlled editor map was created with a Sharded core, Payload Source, and Payload Conveyor, but no block payload was configured or observed on the conveyor, no Derelict conversion was completed, and no save/load transition was performed.


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


## Usage

91 model calls; 5771192 input and 13457 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
