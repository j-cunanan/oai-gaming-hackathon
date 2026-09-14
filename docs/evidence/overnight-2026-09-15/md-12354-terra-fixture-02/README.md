# Cargo disappearance — original-map attempt remains inconclusive

This fresh MAX context received the two unchanged small maps selected from the reporter's data export, with their selection and hashes documented. It did not receive the future developer fix or a prepared bug state.

Terra imported both maps. In “test map,” the UI identified a **Derelict Payload Conveyor** and a nearby **World Processor**. It saved and reopened that running scene; both objects remained visible. It could not establish whether the World Processor was the conveyor's carried payload or a separate placed building, so that observation does not qualify the report's payload-persistence trigger. The “mix tech” map did not yield the required transport setup. A later constructed scene also stopped before completing a source/payload/save/load sequence.

The result is **INSUFFICIENT_EVIDENCE**, not a negative bug confirmation. The original report-only attempt remains in its sibling folder. The exact historical Arc source dependency enabled the build after the original JitPack dependency was unavailable; the game source revision was unchanged, and the dependency audit is retained in the artifacts.

This package contains **189 events and 92 artifacts**. Usage: **90 Terra MAX calls, 1,820,608 input tokens and 22,361 output tokens**. No reproduction, candidate patch or validation success was produced.

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12354-terra-fixture-02 --manifest benchmarks/candidates/MD-candidate-12354-fixture.yaml --id recorded-md-12354-fixture
```
