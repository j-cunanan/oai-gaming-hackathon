"""Conservative comparison of recorded Gradle/JUnit test failures.

Only a complete, single test-task console report is supported. Unrecognized or
interleaved output blocks differential acceptance; exception text is never used.
"""

import hashlib
import re
from datetime import UTC, datetime

from repro.adapters import GameAdapter
from repro.models import BaselineTestRun, Case, Check
from repro.storage.store import Store

PARSER_VERSION = 1
ANSI = re.compile(r"\x1b\[[0-9;]*[mK]")
FAILURE = re.compile(r"(?P<class>[\w.$]+) > (?P<test>\S.*?) FAILED")
SUMMARY = re.compile(r"(\d+) tests? completed, (\d+) failed(?:, (\d+) skipped)?")


def test_command(adapter: GameAdapter, *, network: bool = False) -> list[str]:
    command = [arg for arg in adapter.tests if not (network and arg == "--offline")]
    if adapter.id == "mindustry":
        # Execute assertions afresh, even after dependency preparation or a rerun.
        command += ["--rerun-tasks", "--no-build-cache", "--console=plain"]
    return command


def parse_gradle_failures(output: str, exit_code: int) -> list[str]:
    """Return task-scoped JUnit identifiers, or reject incomplete/ambiguous logs."""
    if exit_code == 0:
        return []
    if exit_code < 0:
        raise ValueError("Test process did not exit normally")
    lines = ANSI.sub("", output).splitlines()
    summaries = [(i, m) for i, line in enumerate(lines) if (m := SUMMARY.fullmatch(line))]
    ends = [i for i, line in enumerate(lines) if re.fullmatch(r"BUILD FAILED in .+", line)]
    tasks = [
        (i, line.removeprefix("> Task ").removesuffix(" FAILED"))
        for i, line in enumerate(lines)
        if re.fullmatch(r"> Task :\S+ FAILED", line)
    ]
    if len(summaries) != 1 or len(ends) != 1 or len(tasks) != 1:
        raise ValueError("Expected one complete test summary, failed task and BUILD FAILED marker")
    summary_index, summary = summaries[0]
    task_index, task = tasks[0]
    starts = [i for i, line in enumerate(lines) if line == f"> Task {task}"]
    if len(starts) != 1 or not starts[0] < summary_index < task_index < ends[0]:
        raise ValueError(
            "Missing or out-of-order test task output; log may be truncated/interleaved"
        )
    failures = []
    for i, line in enumerate(lines):
        if line.endswith(" FAILED") and not line.startswith("> Task "):
            match = FAILURE.fullmatch(line)
            if not match or not starts[0] < i < summary_index:
                raise ValueError("Unrecognized or misplaced failing test identifier")
            failures.append(f"{task}::{match['class']}.{match['test']}")
    total, failed, skipped = int(summary[1]), int(summary[2]), int(summary[3] or 0)
    if failed == 0 or total < failed + skipped or len(failures) != failed:
        raise ValueError("Failing test identifiers do not match the completed-test summary")
    if len(set(failures)) != len(failures):
        raise ValueError("Duplicate test identifiers are ambiguous")
    return sorted(failures)


def baseline_evidence(
    store: Store, case: Case, command: list[str], worker_image: str, worker_platform: str
) -> tuple[BaselineTestRun | None, str | None]:
    """Re-read the original artifact and reject missing, stale or inconsistent evidence."""
    record = case.baseline_tests.get(case.report.target_commit)
    if record is None:
        return None, "No recorded baseline test run for this commit"
    if (
        record.commit_sha != case.report.target_commit
        or record.command != command
        or record.worker_image != worker_image
        or record.worker_platform != worker_platform
        or record.parser_version != PARSER_VERSION
    ):
        return record, "Baseline test record is stale (commit, command, worker or parser changed)"
    if record.status != "completed" or record.exit_code is None:
        return record, f"Baseline test run did not complete: {record.detail}"
    try:
        timestamp = datetime.fromisoformat(record.timestamp)
        if timestamp.tzinfo is None or timestamp > datetime.now(UTC):
            raise ValueError("Invalid baseline timestamp")
        if not record.artifact:
            raise ValueError("Baseline log artifact is missing")
        path, _ = store.artifact_path(case.id, record.artifact)
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != record.log_sha256:
            raise ValueError("Baseline log integrity check failed")
        parsed = parse_gradle_failures(raw.decode("utf-8"), record.exit_code)
        if record.parse_error or parsed != record.failing_tests:
            raise ValueError("Baseline parsed identifiers disagree with the stored record")
    except (KeyError, OSError, UnicodeError, ValueError) as exc:
        return record, f"Baseline evidence unavailable or unparseable: {exc}"
    return record, None


def existing_tests_check(
    store: Store,
    case: Case,
    exit_code: int,
    output: str,
    artifact: str,
    command: list[str],
    worker_image: str,
    worker_platform: str,
    *,
    network: bool = False,
) -> Check:
    record, baseline_error = baseline_evidence(store, case, command, worker_image, worker_platform)
    check = Check(
        name="Existing tests",
        status="pass" if exit_code == 0 else "fail",
        detail=f"Test exit code {exit_code}.",
        artifact=artifact,
        baseline_artifact=record.artifact if record else None,
    )
    if exit_code == 0:
        return check
    try:
        check.failing_tests = parse_gradle_failures(output, exit_code)
    except ValueError as exc:
        check.detail += f" Candidate test identifiers are unparseable: {exc}."
        return check
    check.detail += " Failing tests: " + ", ".join(check.failing_tests) + "."
    if network:
        check.detail += " Network-enabled candidate failures cannot be waived by an offline baseline."
        return check
    if baseline_error:
        check.detail += f" {baseline_error}; differential acceptance is blocked."
        return check
    baseline_failures = set(record.failing_tests)
    new = set(check.failing_tests) - baseline_failures
    if new:
        check.detail += " New failures absent from baseline: " + ", ".join(sorted(new)) + "."
        return check
    check.status = "baseline_failed"
    check.detail += " Pre-existing — these tests also fail on the recorded baseline."
    resolved = baseline_failures - set(check.failing_tests)
    if resolved:
        check.detail += " Baseline failures no longer present: " + ", ".join(sorted(resolved)) + "."
    return check
