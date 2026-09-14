# Original-map lifecycle crash — not reproduced in this attempt

The original reporter's `WotM.msav` was restored from its registered SHA-256 input and imported through the Mindustry UI. Terra opened it in the editor, entered in-game editor mode, changed a tile, returned to the editor, opened **Data Patches & Assets**, visited its six tabs, and pressed Escape. The process remained running with no visible error and an empty captured log. A second immediate Content-tab-to-Escape close was also stable.

This is one fresh **NOT_REPRODUCED** investigation, not five negative confirmations or a finding that the reported bug does not exist. The report concerned macOS; the investigation used the isolated Linux worker. Missing conditions or platform differences remain possible. There is no AI patch or candidate validation result.

The run used `gpt-5.6-terra`, **max reasoning**, for **69 calls, 1,828,088 input tokens and 15,301 output tokens**; the recorded job duration is **874.92 seconds**. The package retains **146 events and 62 artifacts**, including the original provided map and UI evidence. The separate [fixture manifest](../../../../benchmarks/candidates/MD-candidate-12652-fixture.yaml) contains only the supplied report and input metadata in its investigator section.

Import the frozen recording without Docker or model calls:

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12652-terra-max-01 --manifest benchmarks/candidates/MD-candidate-12652-fixture.yaml --id recorded-md-12652
```

To attempt a fresh run, first register the retained original map with `repro add-fixture`, then import the fixture manifest as a new case. The original attachment and its source/hash notes are in `benchmarks/fixtures/MD-candidate-12652/`. A fresh run makes model calls and may reach a different outcome.
