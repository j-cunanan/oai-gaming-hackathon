# REPRO — [Prepared setup] Generator ghost state after payload explosion


Status: **INSUFFICIENT_EVIDENCE**


The prepared save was imported through Load Game and tested in gameplay. The Steam Generator was visibly supplied with Water and Blast Compound, showed 132.0 power output, and later showed nonfatal health loss while fueled. I controlled the supplied Mega and attempted pickup/transport, but did not obtain a confirmed Steam Generator payload on the conveyor, a visible post-explosion retrievable payload, or a placed empty/0-HP generator. The reported anomalous state was therefore not established.


Game: mindustry · revision `ec656a63eb6c063fd35abbd7e65cb3b5dba1078b`


## Player report

### Platforms

Windows

### Build

release build 159.7

### Issue

[RU] 
Генератор, заправленный взрывчатой смесью, может пережить собственный взрыв, если он стоит на грузовом конвейере. В результате появляется генератор с 0 HP, который неуязвим, продолжает работать и ломает ИИ юнитов, пытающихся с ним взаимодействовать. При перезаходе на сохранение, генератор теряет забагованные свойства, и становится просто блоком с 0 хп.
Демонстрация бага и его воспроизведения будет прикреплена в виде записи экрана (Простите за плохое качество и фреймрейт, мой ноутбук лучше не запишет)

[EN (DeepSeek translate)]
A generator can survive its own explosion if it is placed on a payload conveyor while fueled with Blast Compound. The resulting block has 0 HP, is indestructible, still functions, and can break enemy AI pathfinding. After reloading the save, the generator loses its bugged properties and becomes a normal block with 0 HP.
A video demonstration of the bug and its reproduction is included as a screen recording.
Please excuse the low resolution and framerate — my laptop is not capable of capturing higher quality footage.

https://drive.google.com/file/d/1Ikw9oJ3dS4ffMi4ViG005SJQR1KysG-m/view?usp=sharing

### Steps to reproduce

[RU]
- Поставьте ГВС/Паровой генератор, и запитайте его взрывчатой смесью;
- Дайте ему повредиться, и подхватите юнитом;
- Выгрузите генератор на грузовой конвейер, и подождите до взрыва (Важно: "Взрывы реакторов" должны быть включены);
- Достаньте взорвавшийся генератор с конвейера юнитом, и установите его на землю.
Если у генератора пустая полоса здоровья, то баг удался. Ручную погрузку генератора можно заменить на грузовой загрузчик с Эрекира.

[EN (DeepSeek translate)]
- Place a Steam Generator (or Combustion generator) and fuel it with Blast Compound.
- Allow it to take damage, then pick it up using a unit.
- Unload the damaged generator onto a Payload Conveyor and wait for it to explode. (Important: Reactor explosions must be enabled in the game settings.)
- After it explodes, pick it up from the conveyor using a unit, and place it back on the ground.
If the generator has an empty health bar — the bug has successfully been triggered. Manual loading of the generator can be replaced with a payload loader from Erekir.

### Mods used

[RU]
Без модов

[EN]
No mods

### Save file

[RU]
Баг может быть воспроизведён на любом сохранении.

[EN (Google translater)]
The bug can be reproduced on any save.

### (Crash) logs

_No response_

### REPRO video/setup assistance (not part of the upstream report)

This fresh attempt is explicitly assisted. Codex inspected sampled frames of the original report's linked 331.267-second, 780x438 video on September 15 JST. Those frames are third-party report material, not a fresh REPRO reproduction.

Observed setup in the original video: around 25 seconds a placed Payload Source has a configuration panel with a search field and unit choices. Around 35-55 seconds there is a Steam Generator with adjacent resource sources, a water bar and nonzero power output. The player controls a green payload-capable flying unit; a separate Payload Conveyor is placed nearby. Around 65 seconds the generator is on that conveyor with a visible effect. Later (around 105-115 seconds) hovering the placed Steam Generator shows an empty health bar, water and nonzero power output. Sampled frames do not establish every intermediate input or the exact unit identity.

General setup facts checked in this historical source, not a diagnosis or fix: Payload Source is in the Units category, is 5x5 and requires sandbox/infinite resources. Its configuration combines block and unit choices, so use its search field to find a unit by name rather than guessing an icon. Mega is a payload-capable flying unit with capacity for a 2x2 building. Confirm actual unit output, then use Ctrl-click to control it. Default pickup/drop keys are [ and ]; Space pauses time, E pauses construction, and sustained movement needs keypress hold_seconds.

For Steam Generator, configure an Item Source with Blast Compound and a Liquid Source with Water and verify actual delivery and generator operation before the damage/pickup sequence. Allow enough open terrain for the large source and the flight/transport route. A blank editor map with a friendly core can be saved and played as a custom Sandbox map if existing terrain makes setup difficult. Record the actual rules/mode; editor invulnerability would invalidate a damage test. Reactor explosions must be enabled as the original report says.

Keep checkpoints for generator present and fueled, damaged but alive, loaded on conveyor, explosion/effect, then retrieved and placed with its health and operation inspected. A missing item, unbuilt outline, normal payload drawing or an unexecuted step is not the reported ghost-state bug. Stop with a clear setup limitation if those prerequisites cannot be reached. No historical developer fix, future source or root-cause hint was supplied.


### REPRO operator-prepared saved scene (explicit additional assistance)

This variant begins from a small prepared SAVE GAME supplied at /workspace/fixtures/operator-generator-setup.msav. It is not an original player attachment. Import it using Play > Load Game > Import Save (follow the actual UI labels), then load the saved game. Importing it only as an editor map may omit the saved unit entities, so verify that the units are present in gameplay.

The scene was constructed with the unchanged historical game's normal objects and native SaveIO serializer. It uses a flat 160x120 stone map, a friendly Sharded core and normal Sandbox rules (editor=false, infinite resources=true, reactor explosions=true, no automatic wave timer). The construction audit saved and reloaded the file and checked healthy initial objects and empty conveyors. This is a precondition audit, not a bug reproduction, candidate test or an AI result. There is no damaged, dead or ghost object embedded in the file.

The scene has one healthy Steam Generator at tile (84,60), a Water-configured Liquid Source to its west at (83,60), an UNCONFIGURED Item Source to its east at (86,60), an empty right-facing Payload Conveyor at (96,60), and one healthy Mega near (82,56). Native source delivery was checked: water reaches the generator; it starts without fuel at full health. Camera metadata is near tile (86,60), but choose screen coordinates from the actual image.

First inspect the healthy setup and control the Mega. The AI must configure the Item Source with Blast Compound, establish actual damage, perform pickup and transport onto the conveyor, observe the explosion, then retrieve/place the object and check its health and operation. Pause time deliberately when needed for the timing-sensitive steps; normal gameplay damage must occur with editor mode disabled. The construction source supplies no root-cause diagnosis or future patch.



## Usage

91 model calls; 3292742 input and 26189 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
