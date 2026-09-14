"""Provided maps and setup saves, identified by content and restored before every replay."""

import hashlib
import os
import shutil
import tempfile
import zlib
from pathlib import Path

from repro.models import FixtureSpec
from repro.storage.store import Store

MAX_COMPRESSED_BYTES = 32 * 1024 * 1024
MAX_EXPANDED_BYTES = 64 * 1024 * 1024


def inspect_map(raw: bytes) -> int:
    """Check the bounded save envelope, not gameplay validity or compatibility."""
    if not raw or len(raw) > MAX_COMPRESSED_BYTES:
        raise ValueError("A provided map must be nonempty and no larger than 32 MiB")
    try:
        decoder = zlib.decompressobj()
        expanded = decoder.decompress(raw, MAX_EXPANDED_BYTES + 1)
    except zlib.error as exc:
        raise ValueError("Provided map is not a compressed Mindustry save") from exc
    if len(expanded) > MAX_EXPANDED_BYTES:
        raise ValueError("Provided map expands beyond 64 MiB")
    if not decoder.eof or decoder.unused_data or len(expanded) < 8 or expanded[:4] != b"MSAV":
        raise ValueError("Provided map has an incomplete or invalid Mindustry save envelope")
    version = int.from_bytes(expanded[4:8], "big", signed=True)
    if version < 1:
        raise ValueError("Provided map has an invalid save version")
    return version


def _read_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Provided map must be a regular file: {path.name}")
    with path.open("rb") as source:
        raw = source.read(MAX_COMPRESSED_BYTES + 1)
    if len(raw) > MAX_COMPRESSED_BYTES:
        raise ValueError("Provided map exceeds 32 MiB")
    return raw


def _registered_path(store: Store, fixture: FixtureSpec) -> Path:
    root = store.root.resolve()
    directory = root / "fixtures" / fixture.sha256
    if any(path.is_symlink() for path in (root / "fixtures", directory)):
        raise ValueError("Provided map storage must not use symbolic links")
    return directory / fixture.filename


def register_fixture(store: Store, source: Path) -> FixtureSpec:
    raw = _read_file(source)
    inspect_map(raw)
    fixture = FixtureSpec(filename=source.name, sha256=hashlib.sha256(raw).hexdigest())
    destination = _registered_path(store, fixture)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        if read_fixture(store, fixture) != raw:
            raise ValueError("Registered map differs from its content identity")
        return fixture
    fd, temporary = tempfile.mkstemp(dir=destination.parent, prefix=".register-")
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(raw)
        os.chmod(temporary, 0o444)
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return fixture


def read_fixture(store: Store, fixture: FixtureSpec) -> bytes:
    path = _registered_path(store, fixture)
    if not path.exists():
        raise ValueError(
            f"Missing provided map {fixture.filename} ({fixture.sha256[:12]}). "
            "Register the original file with repro add-fixture before running this case."
        )
    raw = _read_file(path)
    if hashlib.sha256(raw).hexdigest() != fixture.sha256:
        raise ValueError(f"Provided map checksum mismatch: {fixture.filename}")
    inspect_map(raw)
    return raw


def stage_fixtures(store: Store, fixtures: list[FixtureSpec], sandbox_root: Path) -> list[dict]:
    # Read and verify all originals before replacing the previous working copies.
    originals = [(fixture, read_fixture(store, fixture)) for fixture in fixtures]
    directory = sandbox_root / "fixtures"
    if directory.is_symlink():
        raise ValueError("Provided map staging directory must not be a symbolic link")
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir()
    staged = []
    for fixture, raw in originals:
        destination = directory / fixture.filename
        destination.write_bytes(raw)
        destination.chmod(0o444)
        staged.append({**fixture.model_dump(), "bytes": len(raw)})
    return staged
