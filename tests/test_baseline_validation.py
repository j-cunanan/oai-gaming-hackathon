import asyncio
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from repro.adapters import MINDUSTRY
from repro.api import create_app
from repro.cli import app as cli
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import (
    REQUIRED_VALIDATION_GATES,
    BaselineTestRun,
    Case,
    CaseInput,
    Check,
    State,
    patch_validated,
)
from repro.orchestration.manager import Manager
from repro.validation import (
    PARSER_VERSION,
    existing_tests_check,
    parse_gradle_failures,
)
from repro.validation import (
    test_command as upstream_command,
)

EVIDENCE = Path(__file__).resolve().parents[1] / "docs/evidence/MD-001"
TEST_ID = ":tests:test::ModTestAllure.begin()"
IMAGE = "sha256:" + "b" * 64


@pytest.fixture
def logs():
    return (
        (EVIDENCE / "baseline-offline-mod-test.txt").read_text(),
        (EVIDENCE / "candidate-tests.txt").read_text(),
    )


@pytest.fixture
def context(tmp_path):
    from repro.storage.store import Store

    settings = Settings(_env_file=None, data_dir=tmp_path, OPENAI_API_KEY="")
    store = Store(tmp_path)
    case = Case(
        report=CaseInput(
            title="Duplicate buttons",
            body="Two Weather buttons appear in the menu.",
            target_commit="a" * 40,
        ),
        patch_artifact="candidate.patch",
        state=State.AWAITING_HUMAN,
        checks=[
            Check(name=name, status="pass", detail="Recorded check")
            for name in sorted(REQUIRED_VALIDATION_GATES - {"Existing tests"})
        ],
    )
    return settings, store, case


def baseline(context, output, exit_code=1):
    settings, store, case = context
    record = BaselineTestRun(
        commit_sha=case.report.target_commit,
        status="completed",
        exit_code=exit_code,
        failing_tests=parse_gradle_failures(output, exit_code),
        artifact=store.artifact(case.id, "baseline-tests.log", output),
        log_sha256=hashlib.sha256(output.encode()).hexdigest(),
        command=upstream_command(MINDUSTRY),
        worker_image=IMAGE,
        worker_platform=settings.worker_platform,
        parser_version=PARSER_VERSION,
    )
    case.baseline_tests[record.commit_sha] = record
    return record


def compare(context, output, exit_code=1):
    settings, store, case = context
    artifact = store.artifact(case.id, "candidate-tests.log", output)
    check = existing_tests_check(
        store,
        case,
        exit_code,
        output,
        artifact,
        upstream_command(MINDUSTRY),
        IMAGE,
        settings.worker_platform,
    )
    case.checks = [c for c in case.checks if c.name != "Existing tests"] + [check]
    store.save(case)
    return check


def extra_failure(log):
    return log.replace(
        "1 test completed, 1 failed",
        "InventoryTests > saveAfterDeath() FAILED\n\n2 tests completed, 2 failed",
    )


def test_parser_uses_real_gradle_junit_reports_and_ignores_exception_text(logs):
    for log in logs:
        assert parse_gradle_failures(log, 1) == [TEST_ID]
        assert parse_gradle_failures(log.replace("UnknownHostException", "OtherError"), 1) == [
            TEST_ID
        ]
    assert parse_gradle_failures("BUILD SUCCESSFUL in 2s", 0) == []
    assert parse_gradle_failures(logs[0].replace(" FAILED", "\x1b[31m FAILED\x1b[0m"), 1) == [
        TEST_ID
    ]


@pytest.mark.parametrize(
    "damage",
    [
        lambda s: s[: s.index("BUILD FAILED")],
        lambda s: s[: s.index("1 test completed")],
        lambda s: s.replace("1 failed", "2 failed"),
        lambda s: s.replace("1 test completed", "0 tests completed"),
        lambda s: s.replace("begin() FAILED", "FAILED"),
        lambda s: s.replace("ModTestAllure > begin() FAILED", ""),
        lambda s: s.replace("ModTestAllure > begin() FAILED", "  <unknown> FAILED"),
        lambda s: s.replace("> Task :tests:test\n", ""),
        lambda s: s.replace("BUILD FAILED", "> Task :core:compileJava FAILED\nBUILD FAILED"),
        lambda s: extra_failure(s).replace(
            "InventoryTests > saveAfterDeath()", "ModTestAllure > begin()"
        ),
        lambda s: s + s,
        lambda s: "java.net.UnknownHostException: github.com",
        lambda s: "",
    ],
)
def test_parser_fails_closed_for_incomplete_or_ambiguous_logs(logs, damage):
    with pytest.raises(ValueError):
        parse_gradle_failures(damage(logs[0]), 1)


def test_parser_preserves_parameterized_test_names_and_task_scope(logs):
    text = logs[0].replace("begin()", "begin(String) > [2] rainy weather")
    assert parse_gradle_failures(text, 1) == [
        ":tests:test::ModTestAllure.begin(String) > [2] rainy weather"
    ]


@pytest.mark.parametrize("branch", ["equal", "subset", "new", "replaced", "pass", "baseline_pass"])
def test_differential_branches_and_approval(context, logs, branch):
    before, after = logs
    if branch in {"subset", "replaced"}:
        before = extra_failure(before)
    if branch == "baseline_pass":
        baseline(context, "BUILD SUCCESSFUL in 2s", 0)
    else:
        baseline(context, before)
    if branch == "new":
        after = extra_failure(logs[0])
    if branch == "replaced":
        after = after.replace("ModTestAllure", "NewlyBrokenTest")
    check = compare(context, after, 0 if branch == "pass" else 1)
    expected = (
        "pass"
        if branch == "pass"
        else ("baseline_failed" if branch in {"equal", "subset"} else "fail")
    )
    assert check.status == expected
    assert patch_validated(context[2]) == (expected != "fail")
    assert check.artifact and check.baseline_artifact
    if branch in {"new", "replaced", "baseline_pass"}:
        assert "New failures absent from baseline:" in check.detail
    if branch == "subset":
        assert "InventoryTests.saveAfterDeath()" in check.detail


def test_no_baseline_record_blocks_failed_tests_but_not_success(context, logs):
    check = compare(context, logs[1])
    assert check.status == "fail"
    assert "No recorded baseline" in check.detail
    assert not patch_validated(context[2])
    assert compare(context, "success", 0).status == "pass"


@pytest.mark.parametrize(
    "stale",
    [
        "commit",
        "command",
        "image",
        "platform",
        "parser",
        "timestamp",
        "missing_log",
        "tampered_log",
        "identifiers",
        "incomplete",
        "unparseable_baseline",
        "exit_code",
    ],
)
def test_baseline_evidence_fails_closed(context, logs, stale):
    record = baseline(context, logs[0])
    _, store, case = context
    if stale == "commit":
        record.commit_sha = "c" * 40
    elif stale == "command":
        record.command += ["--tests", "ModTestAllure"]
    elif stale == "image":
        record.worker_image = "sha256:changed"
    elif stale == "platform":
        record.worker_platform = "linux/arm64"
    elif stale == "parser":
        record.parser_version = 0
    elif stale == "timestamp":
        record.timestamp = "invalid"
    elif stale in {"missing_log", "tampered_log"}:
        path, _ = store.artifact_path(case.id, record.artifact)
        if stale == "missing_log":
            path.unlink()
        else:
            path.write_text("modified")
    elif stale == "identifiers":
        record.failing_tests = []
    elif stale == "incomplete":
        record.status = "running"
    elif stale == "exit_code":
        record.exit_code = None
    elif stale == "unparseable_baseline":
        output = "partial baseline log"
        record.artifact = store.artifact(case.id, "baseline-tests.log", output)
        record.log_sha256 = hashlib.sha256(output.encode()).hexdigest()
    assert compare(context, logs[1]).status == "fail"
    assert not patch_validated(case)


def test_unparseable_candidate_cannot_borrow_baseline_status(context, logs):
    baseline(context, logs[0])
    assert compare(context, logs[1][:1000]).status == "fail"
    assert "unparseable" in context[2].checks[-1].detail
    assert not patch_validated(context[2])


@pytest.mark.parametrize(
    "blocking", ["fail", "not_run", "error", "missing", "no_patch", "duplicate"]
)
def test_patch_validated_still_requires_every_gate(context, logs, blocking):
    baseline(context, logs[0])
    compare(context, logs[1])
    case = context[2]
    assert patch_validated(case)
    if blocking == "missing":
        case.checks.pop(0)
    elif blocking == "no_patch":
        case.patch_artifact = None
    elif blocking == "duplicate":
        case.checks.insert(0, Check(name="Existing tests", status="fail", detail="Earlier failure"))
    else:
        case.checks[0].status = blocking
    assert not patch_validated(case)


def worker(log):
    return SimpleNamespace(
        adapter=MINDUSTRY,
        start=AsyncMock(),
        stop=AsyncMock(),
        prepare=AsyncMock(),
        image_id=AsyncMock(return_value=IMAGE),
        baseline_source_is_clean=AsyncMock(),
        exec=AsyncMock(return_value=(1, log)),
    )


async def test_prepare_records_baseline_and_refresh_bypasses_cache(context, logs, monkeypatch):
    settings, store, case = context
    case.patch_artifact = None
    sandbox = worker(logs[1])
    monkeypatch.setattr("repro.orchestration.manager.DockerSandbox", lambda *args: sandbox)
    manager = Manager(settings, store)
    await manager.prepare(case)
    record = store.get(case.id).baseline_tests[case.report.target_commit]
    assert record.status == "completed" and record.exit_code == 1
    assert record.failing_tests == [TEST_ID]
    assert store.artifact_path(case.id, record.artifact)[0].read_text() == logs[1]
    assert sandbox.prepare.await_count == 1
    sandbox.start.assert_awaited_with(network=False, fresh_profile=True)
    assert sandbox.exec.call_args.args[0] == upstream_command(MINDUSTRY)
    await manager.prepare(case)
    assert sandbox.exec.await_count == 1
    assert case.baseline_tests[case.report.target_commit].timestamp == record.timestamp
    await manager.prepare(case, refresh_baseline_tests=True)
    assert sandbox.exec.await_count == 2
    assert case.baseline_tests[case.report.target_commit].timestamp != record.timestamp


@pytest.mark.parametrize("failure", ["timeout", "cancelled", "dirty", "unparseable"])
async def test_baseline_unavailable_run_is_explicit_and_retains_log(context, logs, failure):
    settings, store, case = context
    sandbox = worker(logs[1])
    progress = store.workspace(case.id) / "baseline-test-progress.log"

    async def interrupted(*args, **kwargs):
        progress.write_text("partial output from this run")
        raise asyncio.CancelledError() if failure == "cancelled" else TimeoutError()

    if failure in {"timeout", "cancelled"}:
        sandbox.exec.side_effect = interrupted
    elif failure == "dirty":
        sandbox.baseline_source_is_clean.side_effect = ValueError("Dirty baseline")
    else:
        sandbox.exec.return_value = (1, "unfinished Gradle output")
    manager = Manager(settings, store)
    if failure == "cancelled":
        with pytest.raises(asyncio.CancelledError):
            await manager.record_baseline_tests(case, sandbox)
    else:
        await manager.record_baseline_tests(case, sandbox)
    record = store.get(case.id).baseline_tests[case.report.target_commit]
    assert record.status == ("completed" if failure == "unparseable" else "error")
    assert record.artifact
    if failure in {"timeout", "cancelled"}:
        assert (
            store.artifact_path(case.id, record.artifact)[0].read_text()
            == "partial output from this run"
        )
    assert compare(context, logs[1]).status == "fail"
    assert sandbox.stop.await_count == 1


async def test_candidate_test_runner_stores_both_log_links(context, logs):
    settings, store, case = context
    baseline(context, logs[0])
    await Manager(settings, store).check_existing_tests(case, worker(logs[1]))
    check = store.get(case.id).checks[-1]
    assert check.status == "baseline_failed"
    assert check.baseline_artifact and check.artifact


async def test_online_candidate_failure_cannot_reuse_offline_baseline(context, logs):
    settings, store, case = context
    baseline(context, logs[0])
    settings.validation_network = True
    sandbox = worker(logs[1])
    await Manager(settings, store).check_existing_tests(case, sandbox)
    check = store.get(case.id).checks[-1]
    assert check.status == "fail"
    assert check.failing_tests == [TEST_ID]
    assert "cannot be waived" in check.detail
    assert "--offline" not in sandbox.exec.call_args.args[0]
    assert not patch_validated(case)


def test_network_validation_is_opt_in_and_reported_by_health(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    assert settings.validation_network is False
    settings.validation_network = True
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/health").json()["validation_network"] is True


async def test_baseline_clean_guard_checks_actual_source(context, monkeypatch):
    settings, store, case = context
    sandbox = DockerSandbox(settings, store, case)
    run = AsyncMock(side_effect=[(0, case.report.target_commit), (0, " M tests/Test.java")])
    monkeypatch.setattr("repro.computer.sandbox.run", run)
    with pytest.raises(ValueError, match="untouched source"):
        await sandbox.baseline_source_is_clean()


async def test_preparation_resolves_runtime_dependencies_without_running_assertions(
    context, monkeypatch
):
    settings, store, case = context
    sandbox = DockerSandbox(settings, store, case)
    jar = sandbox.repo / "desktop/build/libs/Mindustry.jar"
    jar.parent.mkdir(parents=True)
    jar.write_bytes(b"fixture baseline build")
    monkeypatch.setattr("repro.computer.sandbox.run", AsyncMock(return_value=(0, "")))
    monkeypatch.setattr("repro.computer.sandbox.audit_history", AsyncMock(return_value={}))
    sandbox.start = AsyncMock()
    sandbox.stop = AsyncMock()
    sandbox.exec = AsyncMock(return_value=(0, "Dependencies ready"))
    await sandbox.prepare()
    command = sandbox.exec.call_args_list[1].args[0]
    assert "tests:test" not in command
    assert "tests:testClasses" in command
    assert "reproResolveTestRuntime" in command
    assert "--init-script" in command
    assert (
        "testRuntimeClasspath.files"
        in (sandbox.root / "prepare-test-dependencies.gradle").read_text()
    )
    assert (sandbox.root / "baseline/Mindustry.jar").read_bytes() == b"fixture baseline build"


def test_case_api_and_approval_expose_differential_evidence(context, logs):
    settings, store, case = context
    record = baseline(context, logs[0])
    check = compare(context, logs[1])
    with TestClient(create_app(settings)) as client:
        data = client.get(f"/api/cases/{case.id}").json()
        assert data["baseline_tests"][case.report.target_commit]["exit_code"] == 1
        api_check = next(c for c in data["checks"] if c["name"] == "Existing tests")
        assert api_check["status"] == "baseline_failed"
        assert api_check["failing_tests"] == [TEST_ID]
        for artifact, content in [(record.artifact, logs[0]), (check.artifact, logs[1])]:
            assert client.get(f"/api/cases/{case.id}/artifacts/{artifact}").text == content
        assert client.post(f"/api/cases/{case.id}/approve").status_code == 200


def test_cli_refresh_flag_is_forwarded(context, monkeypatch):
    settings, store, case = context
    case.patch_artifact = None
    store.save(case)
    prepare = AsyncMock()
    monkeypatch.setattr("repro.cli.context", lambda: (settings, store))
    monkeypatch.setattr("repro.cli.Manager.prepare", prepare)
    result = CliRunner().invoke(cli, ["prepare", case.id, "--refresh-baseline-tests"])
    assert result.exit_code == 0, result.output
    assert prepare.call_args.kwargs == {"refresh_baseline_tests": True}


def test_baseline_failure_cannot_waive_other_gates(context):
    _, _, case = context
    case.checks = [Check(name=name, status="pass", detail="ok") for name in REQUIRED_VALIDATION_GATES]
    assert patch_validated(case)
    for check in case.checks:
        check.status = "baseline_failed"
        assert patch_validated(case) == (check.name == "Existing tests")
        check.status = "pass"
