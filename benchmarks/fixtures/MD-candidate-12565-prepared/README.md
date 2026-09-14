# Operator-prepared unit scene

This is an explicitly prepared setup save, not an original reporter attachment. It was generated with the unchanged pre-fix game at `7e80948b58138a569e119857e0add95762d7e0bb`. The [constructor and instructions](../../../scripts/fixtures/README.md), `construction.log` and `provenance.json` establish its origin.

The file starts with three healthy friendly Daggers, three connected empty right-facing conveyors, clear output space and a friendly core on flat terrain. Save/reload assertions confirm those preconditions. **No entry, transport, missing-unit state or reproduction result is encoded or tested.** The three available units are setup resources, not three independent bug trials.

The separate `MD-candidate-12565-prepared.yaml` input labels this assistance and leaves the reported entry transition and loss assessment to the AI. Import the file through **Play → Load Game → Import Save**, then load it so the saved unit entities are available. Every fresh run restores the same registered bytes.

```bash
uv run repro add-fixture benchmarks/fixtures/MD-candidate-12565-prepared/operator-unit-setup.msav
uv run repro import-case benchmarks/candidates/MD-candidate-12565-prepared.yaml
```
