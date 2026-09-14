# Original cargo report test maps

These are unchanged files from the archive linked in [Mindustry issue #12354](https://github.com/Anuken/Mindustry/issues/12354). The complete [original attachment](https://github.com/user-attachments/files/29970021/mindustry-data-export.zip) is 1,337,494 bytes; its SHA-256 and the exact archive members are recorded in `provenance.json`.

The two smallest named test maps were selected for a separate input-assisted investigation. Their internal names are **test map** and **mix tech**, both 200×200, save format 13 and build tag 159. Each metadata section lists `mods: []`. They are renamed only to safe local filenames; every byte matches the corresponding archive member. This inspection does not establish that either map reproduces the report.

The original archive also contains larger maps, saved games, settings and a mod ZIP. Those files were not installed. Empty mod metadata in the selected maps is not proof that the reporter never used mods.

Register these inputs before a fresh attempt:

```bash
uv run repro add-fixture benchmarks/fixtures/MD-candidate-12354/cargo-test-map.msav
uv run repro add-fixture benchmarks/fixtures/MD-candidate-12354/cargo-mix-tech.msav
uv run repro import-case benchmarks/candidates/MD-candidate-12354-fixture.yaml
```

The runner restores identical copies at `/workspace/fixtures/` before each fresh launch. The manifest explicitly preserves the input selection and the earlier report-only attempt's setup failure. The exact missing historical Arc revision, `7637600c41922c078ac6bde26953ef1e71746f35`, is needed as an adjacent isolated `Arc` checkout if JitPack remains unavailable; the case's dependency audit records that preparation.
