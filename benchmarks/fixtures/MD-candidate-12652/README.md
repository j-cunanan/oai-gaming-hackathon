# Original map for Mindustry issue 12652

The reporter supplied [WotM.msav.zip](https://github.com/user-attachments/files/32153827/WotM.msav.zip) in [issue 12652](https://github.com/Anuken/Mindustry/issues/12652). Both the downloaded archive and the unchanged `WotM.msav` entry are retained here. The archive also contains a 220-byte macOS resource fork, which is not installed.

`manifest.json` records the source, byte counts and SHA-256 values. Bounded zlib decoding confirms the `MSAV` envelope and save version 13. This is input inspection, not a claim that the map loads on Linux or that the reported crash reproduces. No map contents were edited.

Register the original before importing [the fixture case manifest](../../candidates/MD-candidate-12652-fixture.yaml):

```bash
uv run repro add-fixture benchmarks/fixtures/MD-candidate-12652/WotM.msav
uv run repro import-case benchmarks/candidates/MD-candidate-12652-fixture.yaml
```

The runner restores an identical working copy before each fresh game launch. The AI must import it through its recorded UI actions. Only the manifest input fields reach the investigator; evaluator metadata and future fixes do not.
