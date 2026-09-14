import hashlib
import zlib
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import Case, CaseInput, FixtureSpec
from repro.orchestration.manager import Manager
from repro.storage import fixtures
from repro.storage.store import Store


def original_map(tmp_path):
    path = tmp_path / "Reported.msav"
    path.write_bytes(zlib.compress(b"MSAV\x00\x00\x00\x0d" + b"test fixture data"))
    return path


def report(**kwargs):
    return CaseInput(
        title="Reported map crash",
        body="The editor crashes after reopening.",
        target_commit="a" * 40,
        **kwargs,
    )


@pytest.mark.parametrize("filename", ["../x.msav", "/x.msav", "x\\y.msav", "x.zip", ".msav"])
def test_fixture_references_cannot_name_paths_or_other_formats(filename):
    with pytest.raises(ValidationError):
        FixtureSpec(filename=filename, sha256="a" * 64)


def test_fixture_input_rejects_duplicate_names_and_unsupported_game():
    fixture = FixtureSpec(filename="Map.msav", sha256="a" * 64)
    with pytest.raises(ValidationError, match="distinct"):
        report(fixtures=[fixture, fixture.model_copy(update={"filename": "map.msav"})])
    with pytest.raises(ValidationError, match="Mindustry only"):
        report(fixtures=[fixture], game="luanti")


def test_registration_retains_exact_bytes_and_detects_tampering(tmp_path):
    store = Store(tmp_path / "store")
    source = original_map(tmp_path)
    fixture = fixtures.register_fixture(store, source)
    assert fixture.sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    assert fixtures.read_fixture(store, fixture) == source.read_bytes()
    assert fixtures.register_fixture(store, source) == fixture
    stored = store.root / "fixtures" / fixture.sha256 / fixture.filename
    stored.chmod(0o644)
    stored.write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum mismatch"):
        fixtures.read_fixture(store, fixture)


def test_fixture_storage_rejects_symlink_escape(tmp_path):
    store = Store(tmp_path / "store")
    outside = tmp_path / "outside"
    outside.mkdir()
    (store.root / "fixtures").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic links"):
        fixtures.register_fixture(store, original_map(tmp_path))
    assert not list(outside.iterdir())


@pytest.mark.parametrize(
    "raw",
    [
        b"not zlib",
        zlib.compress(b"wrong header"),
        zlib.compress(b"MSAV\0\0\0\r")[:-1],
        zlib.compress(b"MSAV\0\0\0\r") + b"extra",
    ],
)
def test_invalid_save_envelopes_are_rejected(raw):
    with pytest.raises(ValueError):
        fixtures.inspect_map(raw)


def test_save_expansion_is_bounded(monkeypatch):
    monkeypatch.setattr(fixtures, "MAX_EXPANDED_BYTES", 100)
    with pytest.raises(ValueError, match="expands beyond"):
        fixtures.inspect_map(zlib.compress(b"MSAV\0\0\0\r" + b"x" * 1000))


async def test_fresh_game_reset_restores_original_and_records_input(tmp_path, monkeypatch):
    store = Store(tmp_path / "store")
    source = original_map(tmp_path)
    fixture = fixtures.register_fixture(store, source)
    case = Case(report=report(fixtures=[fixture]))
    store.save(case)
    settings = Settings(_env_file=None, data_dir=store.root, sandbox_dir=tmp_path / "sandboxes")
    sandbox = DockerSandbox(settings, store, case)
    staged = sandbox.root / "fixtures" / fixture.filename
    starts = AsyncMock()

    async def launch():
        assert staged.read_bytes() == source.read_bytes()
        assert not (staged.stat().st_mode & 0o222)
        return {"running": True}

    monkeypatch.setattr(sandbox, "start", starts)
    monkeypatch.setattr(sandbox, "launch", launch)
    await sandbox.reset()
    staged.chmod(0o644)
    staged.write_bytes(b"modified in prior game")
    await sandbox.reset()
    assert starts.await_count == 2
    events = [e for e in store.events(case.id) if e["kind"] == "fixtures_staged"]
    assert len(events) == 2
    artifact_id = events[-1]["data"]["fixtures"][0]["artifact"]
    assert store.artifact_path(case.id, artifact_id)[0].read_bytes() == source.read_bytes()
    assert fixtures.read_fixture(store, fixture) == source.read_bytes()


async def test_missing_original_fails_before_build_or_model_call(tmp_path, monkeypatch):
    store = Store(tmp_path / "store")
    fixture = FixtureSpec(filename="Missing.msav", sha256="a" * 64)
    case = Case(report=report(fixtures=[fixture]))
    settings = Settings(_env_file=None, data_dir=store.root)
    sandbox = DockerSandbox(settings, store, case)
    commands = AsyncMock()
    monkeypatch.setattr("repro.computer.sandbox.run", commands)
    with pytest.raises(ValueError, match="Missing provided map"):
        await sandbox.prepare()
    commands.assert_not_called()
    with pytest.raises(ValueError, match="Missing provided map"):
        await Manager(settings, store)._investigate(case, sandbox, None, 0)
    assert not store.events(case.id)


async def test_no_fixture_reset_keeps_existing_behavior(tmp_path, monkeypatch):
    store = Store(tmp_path / "store")
    sandbox = DockerSandbox(
        Settings(_env_file=None, data_dir=store.root), store, Case(report=report())
    )
    monkeypatch.setattr(sandbox, "start", AsyncMock())
    monkeypatch.setattr(sandbox, "launch", AsyncMock(return_value={"running": True}))
    assert await sandbox.reset() == {"running": True}
    assert not (sandbox.root / "fixtures").exists()
