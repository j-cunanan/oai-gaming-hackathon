import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from repro.computer.rpc import WorkerRPC
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import Case, CaseInput, State
from repro.orchestration.manager import Manager
from repro.storage.store import Store


@pytest.mark.parametrize("protocol", [2, 3])
async def test_worker_handshake_rejects_drivers_that_silently_ignore_timed_input(
    tmp_path, monkeypatch, protocol
):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    case = Case(
        report=CaseInput(
            title="Unit control", body="The unit disappears in transit.", target_commit="a" * 40
        )
    )
    sandbox = DockerSandbox(settings, Store(tmp_path), case)
    rpc = SimpleNamespace(request=AsyncMock(return_value={"protocol": protocol}))
    monkeypatch.setattr(sandbox, "stop", AsyncMock())
    monkeypatch.setattr(sandbox, "exec", AsyncMock())
    monkeypatch.setattr("repro.computer.sandbox.run", AsyncMock())
    monkeypatch.setattr("repro.computer.sandbox.asyncio.sleep", AsyncMock())
    monkeypatch.setattr(WorkerRPC, "start", AsyncMock(return_value=rpc))
    if protocol == 2:
        with pytest.raises(RuntimeError, match="Rebuild the worker image"):
            await sandbox.start()
    else:
        await sandbox.start()
    rpc.request.assert_awaited_once_with("ping", None)


async def test_persistent_rpc_orders_large_replies_and_recovers_from_rejected_action(tmp_path):
    script = """
import json,sys
for line in sys.stdin:
    request=json.loads(line)
    if request['operation']=='reject':
        result={'ok':False,'error':'Unsupported key'}
    else:
        result={'ok':True,'result':request['args']}
    print(json.dumps(result),flush=True)
"""
    rpc = await WorkerRPC.start([sys.executable, "-u", "-c", script], tmp_path / "stderr")
    try:
        args = [{"screenshot": "x" * 300_000, "index": i} for i in range(3)]
        assert await asyncio.gather(*(rpc.request("observe", a) for a in args)) == args
        with pytest.raises(ValueError, match="Unsupported key"):
            await rpc.request("reject")
        assert await rpc.request("ping", {"alive": True}) == {"alive": True}
    finally:
        await rpc.close()
    assert rpc.process.returncode == 0


async def test_rpc_timeout_closes_connection_so_late_reply_cannot_be_reused(tmp_path):
    script = "import sys,time; sys.stdin.readline(); time.sleep(30)"
    rpc = await WorkerRPC.start([sys.executable, "-u", "-c", script], tmp_path / "stderr")
    with pytest.raises(TimeoutError):
        await rpc.request("slow", timeout=0.05)
    assert rpc.process.returncode is not None


@pytest.mark.parametrize("network", [True, False])
async def test_validation_network_policy_is_explicit_and_failed_build_blocks_replays(
    tmp_path, network
):
    settings = Settings(_env_file=None, data_dir=tmp_path, validation_network=network)
    store = Store(tmp_path)
    case = Case(
        report=CaseInput(
            title="Weather controls",
            body="Two Weather buttons are visible.",
            target_commit="a" * 40,
        )
    )
    store.save(case)
    calls = []

    async def start(**kwargs):
        calls.append(("start", kwargs))

    async def execute(argv, **kwargs):
        calls.append(("exec", argv))
        return 1, "Compilation failed"

    sandbox = SimpleNamespace(
        start=start,
        exec=execute,
        adapter=SimpleNamespace(build=("bash", "./gradlew", "desktop:dist")),
    )
    await Manager(settings, store).validate(case, sandbox, None, None)
    assert calls[0] == ("start", {"network": network, "fresh_profile": True})
    assert ("--offline" in calls[1][1]) is not network
    assert case.state == State.VALIDATING
    assert [check.status for check in case.checks] == ["fail", "not_run", "not_run", "not_run"]
    event = next(e for e in store.events(case.id) if e["kind"] == "validation_environment")
    assert event["data"]["network"] == ("bridge" if network else "none")
