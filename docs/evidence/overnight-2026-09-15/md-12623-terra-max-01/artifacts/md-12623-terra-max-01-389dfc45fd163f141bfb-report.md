# REPRO — Colored tiles do not accept every valid hex code given, instead skipping over some or using the same value twice


Status: **FAILED**


OpenAI response incomplete; no partial actions were executed Inspect worker-error.log in Evidence for details.


Game: mindustry · revision `ef5d3cb26bcd794a6e560dbb8d20b6f8200b130c`


## Player report

### Platforms

Windows

### Build

v159.7

### Issue

'Colored Wall' & 'Colored Floor' tiles in editor do not accept every hex color code given to them in game. I tested this on both v159.7 and BE 27795 just to make sure it was not yet addressed.

In the save file below I did it for the following values: ff0000 to ff2000. Here is the table for the hex codes inputted vs accepted by the editor so you can copy paste: 
ff0000 -> ff0000
ff0100 -> ff0100
ff0200 -> ff0200
ff0300 -> ff0200
ff0400 -> ff0300
ff0500 -> ff0500 
ff0600 -> ff0600
ff0700 -> ff0700
ff0800 -> ff0700
ff0900 -> ff0800
ff0a00 -> ff0a00
ff0b00 -> ff0b00
ff0c00 -> ff0b00
ff0d00 -> ff0c00
ff0e00 -> ff0e00
ff0f00 -> ff0f00
ff1000 -> ff1000
ff1100 -> ff1000
ff1200 -> ff1100
ff1300 -> ff1300
ff1400 -> ff1400
ff1500 -> ff1400
ff1600 -> ff1500
ff1700 -> ff1600
ff1800 -> ff1800
ff1900 -> ff1900
ff1a00 -> ff1900
ff1b00 -> ff1a00
ff1c00 -> ff1c00
ff1d00 -> ff1d00
ff1e00 -> ff1e00
ff1f00 -> ff1e00
ff2000 -> ff1f00

### Steps to reproduce

1. Open the map editor and go to edit any map
2. Select the 'Colored Floor' or 'Colored Wall' tile in editor 
3. Paste in any hex color codes that differ by 1 in value and place each one down next to one another, eventually you'll see that the tiles no longer separate as the hex color code did not change its value properly

<img width="1589" height="354" alt="Image" src="https://github.com/user-attachments/assets/4108df1e-991f-4c17-8249-2a855d052525" />

### Mods used

none

### Save file

[Debris Field With Color Tiles For You To Look At.zip](https://github.com/user-attachments/files/32078489/Debris.Field.With.Color.Tiles.For.You.To.Look.At.zip)

### (Crash) logs

_No response_


## Usage

52 model calls; 1313193 input and 42109 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
