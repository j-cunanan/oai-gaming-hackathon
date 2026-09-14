# Prepared payload scenes

`OperatorSceneBuilder.java` creates healthy starting conditions with the matching historical game's normal objects and native `SaveIO` serializer. It follows the initialization pattern in that revision's `tests/src/test/java/ApplicationTests.java`. It is a separate operator tool, not a change to Mindustry or an AI-generated patch.

Two scenes are supported:

- **generator:** a friendly core, a healthy unfueled Steam Generator, a working Water source, an unconfigured Item Source, an empty conveyor and one healthy Mega. The AI still has to fuel, damage, pick up, transport, observe destruction, retrieve and inspect the generator.
- **unit:** a friendly core, three healthy Daggers and three connected empty conveyors with open output space. The AI still has to select a specific unit, execute entry and determine whether it is lost or transported normally.

Both use a flat 160×120 map with normal Sandbox rules, `editor=false`, infinite resources, reactor explosions and no automatic wave timer. Units are instantiated through native game constructors; the setup does not measure the unit-production or building-construction workflow. Generator water delivery runs through normal source/building updates. Both modes save and reload their output, then check the same healthy preconditions and empty conveyors. The builder never triggers or tests the reported symptom.

Use an unchanged, already prepared REPRO workspace for the exact report revision. The wrapper verifies its isolated history and clean source, mounts it read-only, and runs the constructor in a network-disabled container. It retains constructor output and the game JAR, backend JAR, source, image and fixture hashes. It refuses to overwrite an earlier output directory.

```bash
uv run python scripts/build_payload_fixture.py \
  --workspace /path/to/prepared/CASE \
  --commit ec656a63eb6c063fd35abbd7e65cb3b5dba1078b \
  --scene generator --image repro-worker:local \
  --output /path/to/new-generator-setup
```

For the unit report, use its exact revision `7e80948b58138a569e119857e0add95762d7e0bb` and `--scene unit`. A rebuild may have a different file hash because the game serializes timestamps; retained inputs are identified by their recorded checksum.

Register a resulting `.msav` with `repro add-fixture` and label it as **operator-prepared setup** in the case input. These are saved games with unit entities: import and load them through the game's **Load Game** flow. A precondition audit is neither a fresh reproduction, an independent bug trial, a candidate pass nor an AI result.
