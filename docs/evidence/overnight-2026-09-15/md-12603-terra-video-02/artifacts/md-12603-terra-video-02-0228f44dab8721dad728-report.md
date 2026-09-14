# REPRO — [Video/setup guided] Generator 0-HP ghost state after payload explosion


Status: **INSUFFICIENT_EVIDENCE**


No 0-HP generator ghost state was observed. I created a controlled editor-mode map, explicitly enabled Reactor Explosions, and placed Steam Generators with an adjacent Item Source, but the required Blast Compound configuration and the payload-conveyor explosion/retrieval/redeployment sequence were not completed before the tool-time limit.


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



## Usage

91 model calls; 4028221 input and 14469 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
