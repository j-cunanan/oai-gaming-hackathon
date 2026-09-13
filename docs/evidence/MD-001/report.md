# REPRO — Two Weather buttons in map rules


Status: **AWAITING_HUMAN**


Replay refinement finished. Inspect the recorded reduction and validation checks.


Game: mindustry · revision `a5c178ae5abcc630613c233e0afbb361021d3828`


## Player report

In the map rules menu, the button to edit the weather appears twice. Open the map rules menu and scroll down. No mods. No save file required.


## Reproduction

5/5 successful clean replays. 23 → 8 actions (bounded reduction, not a proof of global minimality).

1. Open Editor from main menu — `{"action":"click","x":255,"y":336,"keys":[],"text":"","seconds":2.0,"scroll_y":0,"button":"left","semantic":"Open Editor from main menu"}`

2. Open built-in Glacier map in editor — `{"action":"double_click","x":430,"y":550,"keys":[],"text":"","seconds":3.0,"scroll_y":0,"button":"left","semantic":"Open built-in Glacier map in editor"}`

3. Open selected map in editor — `{"action":"click","x":491,"y":501,"keys":[],"text":"","seconds":4.0,"scroll_y":0,"button":"left","semantic":"Open selected map in editor"}`

4. Open editor menu — `{"action":"click","x":34,"y":52,"keys":[],"text":"","seconds":1.0,"scroll_y":0,"button":"left","semantic":"Open editor menu"}`

5. Open map information and rules — `{"action":"click","x":739,"y":185,"keys":[],"text":"","seconds":2.0,"scroll_y":0,"button":"left","semantic":"Open map information and rules"}`

6. Open map rules — `{"action":"click","x":530,"y":425,"keys":[],"text":"","seconds":2.0,"scroll_y":0,"button":"left","semantic":"Open map rules"}`

7. Focus custom-rules search — `{"action":"click","x":616,"y":92,"keys":[],"text":"","seconds":0.2,"scroll_y":0,"button":"left","semantic":"Focus custom-rules search"}`

8. Filter custom rules to Weather — `{"action":"type","x":null,"y":null,"keys":[],"text":"weather","seconds":2.0,"scroll_y":0,"button":"left","semantic":"Filter custom rules to Weather"}`


## Source findings

CustomRulesDialog.setupMain() explicitly creates the same `@rules.weather` button twice: once in the `environment` category and again in the subsequent `light` category. Both use the identical search predicate and invoke `weatherDialog`, so filtering with "weather" deterministically renders two Weather edit controls in separate category results. The replay's clicks on Environment then Lighting match these two construction sites.

- `core/src/mindustry/ui/dialogs/CustomRulesDialog.java` / CustomRulesDialog.setupMain() (0.99): This is the direct render path for the reported map rules menu. Two independently added controls share the same label and handler, matching both the observed duplicate and the deterministic filtered replay.


Limitations: Source inspection establishes the duplicate construction path but does not independently execute the supplied replay or inspect its screenshots.; The supplied evidence does not establish whether the unfiltered scrolled presentation is visibly duplicated at every UI scale/language; however, both source sites are unconditional with respect to platform and are independently gated only by localized search matching.; This localization does not determine why the second placement was introduced or prescribe a future fix.


## Validation

- Regression before patch: **pass** — Reduced trigger observed in 5/5 clean baseline runs.

- Candidate build: **pass** — Build exit code 0

- Existing tests: **fail** — Test exit code 1. The log contains UnknownHostException; this worker has networking disabled. Inspect the test log.

- Original replay after patch: **pass** — 5/5 reached expected state without the symptom; bug seen 0 times.

- Smoke test: **pass** — Clean desktop launch and live process after startup; deeper gameplay smoke coverage is not implemented.


## Usage

84 model calls; 1057809 input and 11504 output tokens.


Candidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.
