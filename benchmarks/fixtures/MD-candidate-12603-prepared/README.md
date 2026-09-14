# Operator-prepared generator scene

This is an explicitly prepared setup save, not an original reporter attachment. It was generated with the unchanged pre-fix game at `ec656a63eb6c063fd35abbd7e65cb3b5dba1078b`. The [constructor and instructions](../../../scripts/fixtures/README.md), `construction.log` and `provenance.json` establish its origin.

The file starts with a healthy, unfueled Steam Generator; a Water source whose normal delivery reaches the generator; an unconfigured Item Source; an empty payload conveyor; a healthy Mega; and a friendly core on flat terrain. Save/reload assertions confirm these preconditions. **No explosion, damage, ghost state or reproduction result is encoded or tested.**

The separate `MD-candidate-12603-prepared.yaml` input labels this assistance and leaves the entire reported transition to the AI. Import the file through **Play → Load Game → Import Save**, then load it so the saved unit entity is available. Every fresh run restores the same registered bytes.

```bash
uv run repro add-fixture benchmarks/fixtures/MD-candidate-12603-prepared/operator-generator-setup.msav
uv run repro import-case benchmarks/candidates/MD-candidate-12603-prepared.yaml
```
