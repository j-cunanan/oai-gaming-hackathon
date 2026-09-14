# REPRO — [RU] Призрачное состояние генератора после взрыва на грузовом конвейере. [EN] Generator 0‑HP ghost state after payload explosion.


Status: **INSUFFICIENT_EVIDENCE**


Could not execute the reported fueled-generator payload explosion. A local editor map was created and playtested; a Core Shard was added so the playtest launched, and the Steam Generator was identified and selected. However, the intended infinite-resources rule was not effective in the launched playtest (the placed generator remained a construction ghost due to missing lead/graphite/silicon). Consequently I could not construct, fuel, damage, transport, explode, retrieve, place, or reload the target block.


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


## Usage

80 model calls; 1032495 input and 8793 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
