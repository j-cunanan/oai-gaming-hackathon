import re
import tempfile
from pathlib import Path

from repro.process import run


async def isolate_snapshot(upstream: str, commit: str, destination: Path):
    """Depth-one pre-fix history. Exact upstream SHA, no future objects or remote."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("An exact commit SHA is required")
    if destination.exists():
        raise ValueError("Destination already exists")
    await run(["git", "init", str(destination)])
    await run(["git", "-C", str(destination), "fetch", "--depth=1", upstream, commit])
    await run(["git", "-C", str(destination), "checkout", "--detach", commit])
    await run(["git", "-C", str(destination), "config", "user.name", "REPRO candidate"])
    await run(["git", "-C", str(destination), "config", "user.email", "repro@localhost"])
    await audit_history(destination, commit)


async def isolate_history(source: Path, commit: str, destination: Path):
    """Export only commit + ancestors; no hardlinks, alternates, future refs or remote."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("An exact commit SHA is required")
    if destination.exists():
        raise ValueError("Destination already exists")
    _, resolved = await run(["git", "-C", str(source), "rev-parse", f"{commit}^{{commit}}"])
    if resolved.strip() != commit:
        raise ValueError("Commit mismatch")
    with tempfile.TemporaryDirectory(prefix="repro-bundle-") as tmp:
        bundle = Path(tmp) / "case.bundle"
        ref = f"refs/heads/repro-export-{commit[:12]}"
        await run(["git", "-C", str(source), "update-ref", ref, commit])
        try:
            await run(["git", "-C", str(source), "bundle", "create", str(bundle), ref])
        finally:
            await run(["git", "-C", str(source), "update-ref", "-d", ref])
        await run(
            [
                "git",
                "clone",
                "--branch",
                ref.removeprefix("refs/heads/"),
                str(bundle),
                str(destination),
            ]
        )
        await run(["git", "-C", str(destination), "remote", "remove", "origin"])
    await run(["git", "-C", str(destination), "config", "user.name", "REPRO candidate"])
    await run(["git", "-C", str(destination), "config", "user.email", "repro@localhost"])
    await audit_history(destination, commit)


async def audit_history(repo: Path, commit: str) -> dict:
    _, head = await run(["git", "-C", str(repo), "rev-parse", "HEAD"])
    _, remotes = await run(["git", "-C", str(repo), "remote"])
    _, extra = await run(["git", "-C", str(repo), "rev-list", "--all", "--not", commit])
    _, unreachable = await run(["git", "-C", str(repo), "fsck", "--unreachable", "--no-reflogs"])
    if head.strip() != commit or remotes.strip() or extra.strip() or "unreachable" in unreachable:
        raise ValueError("Historical repository isolation failed")
    if (repo / ".git/objects/info/alternates").exists():
        raise ValueError("Shared Git object database is not allowed")
    return {"commit": commit, "future_objects": False, "remotes": [], "isolated": True}
