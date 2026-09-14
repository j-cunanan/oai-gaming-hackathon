import asyncio
import json
import shutil
from pathlib import Path

from repro.adapters import ADAPTERS
from repro.computer.rpc import WorkerRPC
from repro.config import Settings
from repro.github.history import audit_history, isolate_snapshot
from repro.models import Action, Case
from repro.process import run
from repro.storage.fixtures import read_fixture, stage_fixtures
from repro.storage.store import Store


class DockerSandbox:
    def __init__(self, settings: Settings, store: Store, case: Case):
        self.settings, self.store, self.case = settings, store, case
        self.adapter = ADAPTERS[case.report.game]
        self.root = (
            (settings.sandbox_dir.resolve() / case.id)
            if settings.sandbox_dir
            else store.workspace(case.id) / "sandbox"
        )
        self.repo = self.root / "repo"
        self.name = f"repro-{case.id}"
        self.use_baseline = False
        self._rpc: WorkerRPC | None = None
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "runtime").mkdir(exist_ok=True)
        (self.root / "gradle").mkdir(exist_ok=True)

    async def prepare(self):
        for fixture in self.case.report.fixtures:
            read_fixture(self.store, fixture)
        await run(["docker", "image", "inspect", self.settings.worker_image], timeout=20)
        if not self.repo.exists():
            await isolate_snapshot(self.adapter.upstream, self.case.report.target_commit, self.repo)
        audit = await audit_history(self.repo, self.case.report.target_commit)
        self.store.artifact(
            self.case.id, "history-audit.json", json.dumps(audit, indent=2), "application/json"
        )
        await self.start(network=True)
        try:
            progress = self.store.workspace(self.case.id) / "build-progress.log"
            try:
                code, output = await self.exec(
                    list(self.adapter.build), timeout=1200, check=False, output_path=progress
                )
            finally:
                if progress.exists():
                    self.store.artifact(self.case.id, "prepare-build.log", progress.read_bytes())
            artifact = self.store.artifact(self.case.id, "prepare-build.log", output)
            if code:
                raise RuntimeError(f"Game build failed (exit {code}); inspect {artifact}")
            if self.case.report.game == "mindustry":
                baseline = self.root / "baseline"
                baseline.mkdir(exist_ok=True)
                shutil.copy2(
                    self.repo / "desktop/build/libs/Mindustry.jar", baseline / "Mindustry.jar"
                )
            preparation_tests = [arg for arg in self.adapter.tests if arg != "--offline"]
            if self.case.report.game == "mindustry":
                # Resolve/compile test dependencies during preparation. Actual
                # baseline assertions run separately with networking disabled.
                init_script = self.root / "prepare-test-dependencies.gradle"
                init_script.write_text(
                    "gradle.projectsEvaluated {\n"
                    "    gradle.rootProject.tasks.register('reproResolveTestRuntime') {\n"
                    "        doLast {\n"
                    "            gradle.rootProject.project(':tests')"
                    ".configurations.testRuntimeClasspath.files\n"
                    "        }\n"
                    "    }\n"
                    "}\n"
                )
                preparation_tests = [
                    "tests:testClasses" if arg == "tests:test" else arg for arg in preparation_tests
                ]
                preparation_tests += [
                    "--init-script",
                    "/workspace/prepare-test-dependencies.gradle",
                    "reproResolveTestRuntime",
                ]
            code, output = await self.exec(preparation_tests, timeout=600, check=False)
            self.store.artifact(self.case.id, "prepare-test-dependencies.log", output)
            (self.root / "prepared.json").write_text(
                json.dumps(
                    {
                        "commit": self.case.report.target_commit,
                        "image": self.settings.worker_image,
                        "test_dependencies_exit_code": code,
                    }
                )
            )
        finally:
            await self.stop()

    async def baseline_source_is_clean(self):
        _, commit = await run(["git", "-C", str(self.repo), "rev-parse", "HEAD"])
        _, changes = await run(["git", "-C", str(self.repo), "status", "--porcelain"])
        if commit.strip() != self.case.report.target_commit or changes.strip():
            raise ValueError("Baseline tests require the untouched source at the target commit")

    async def image_id(self) -> str:
        # Resolve the running image, not a mutable tag that may have been rebuilt.
        _, output = await run(["docker", "inspect", "--format", "{{.Image}}", self.name])
        if not output.strip().startswith("sha256:"):
            raise ValueError("Cannot establish the running worker image identity")
        return output.strip()

    async def start(self, network=False, *, fresh_profile=False):
        await self.stop()
        if fresh_profile:
            runtime = self.root / "runtime"
            if runtime.exists():
                shutil.rmtree(runtime)
            (runtime / "profile").mkdir(parents=True)
        await run(
            [
                "docker",
                "run",
                "-d",
                "--platform",
                self.settings.worker_platform,
                "--name",
                self.name,
                "--network",
                "bridge" if network else "none",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--pids-limit=512",
                "--cpus=3",
                "--memory=5g",
                "--shm-size=256m",
                "--read-only",
                "--tmpfs",
                "/tmp:rw,size=512m",
                "--tmpfs",
                "/home/worker:rw,uid=1000,gid=1000,size=256m",
                "--mount",
                f"type=bind,source={self.root},target=/workspace",
                "-e",
                "GRADLE_USER_HOME=/workspace/gradle",
                self.settings.worker_image,
            ],
            timeout=30,
        )
        await asyncio.sleep(1)
        # Xvfb and Openbox start asynchronously. A game opened before Openbox is
        # ready may keep its default size, invalidating recorded coordinates.
        await self.exec(["python3", "/opt/repro/wait_desktop.py", "--wm"], timeout=20)
        self._rpc = await WorkerRPC.start(
            ["docker", "exec", "-i", self.name, "python3", "-u", "/opt/repro/worker.py", "serve"],
            self.root / "worker-rpc.log",
        )
        if (await self.rpc("ping")).get("protocol") != 4:
            raise RuntimeError(
                "Rebuild the worker image to enable paced scrolling, modifier clicks and timed input"
            )

    async def stop(self):
        try:
            await run(["docker", "rm", "-f", self.name], check=False, timeout=30)
        finally:
            if self._rpc:
                await self._rpc.close()
                self._rpc = None

    async def exec(self, argv, *, timeout=120, check=True, input_text=None, output_path=None):
        return await run(
            ["docker", "exec", "-i", self.name, *argv],
            timeout=timeout,
            check=check,
            input_text=input_text,
            output_path=output_path,
        )

    async def rpc(self, operation: str, args: dict | None = None):
        if not self._rpc:
            raise RuntimeError("Start the worker before issuing desktop commands")
        return await self._rpc.request(operation, args)

    async def launch(self):
        argv = self.adapter.launch
        if self.use_baseline:
            if (
                self.case.report.game != "mindustry"
                or not (self.root / "baseline/Mindustry.jar").exists()
            ):
                raise ValueError("A retained baseline desktop build is not available")
            argv = (
                "java",
                "-Duser.home=/workspace/runtime/profile",
                "-jar",
                "/workspace/baseline/Mindustry.jar",
            )
        await self.rpc("launch", {"argv": argv})
        await asyncio.sleep(8)
        if self.adapter.ready_log:
            # Emulated startup can exceed the minimum wait. Do not lose the first
            # replay click while assets are still loading; never dismiss dialogs.
            async with asyncio.timeout(45):
                while True:
                    observation = await self.observe()
                    if not observation.get("process", {}).get("running", False):
                        return observation
                    if self.adapter.ready_log in observation.get("logs", ""):
                        break
                    await asyncio.sleep(0.5)
            # ClientLoadEvent precedes the final resize and first interactive frames.
            await asyncio.sleep(1)
        return await self.observe()

    async def reset(self):
        # Recreate the container, which reaps all game/Gradle child processes.
        await self.start(fresh_profile=True)
        if self.case.report.fixtures:
            staged = stage_fixtures(self.store, self.case.report.fixtures, self.root)
            for fixture, item in zip(self.case.report.fixtures, staged, strict=True):
                item["artifact"] = self.store.artifact(
                    self.case.id,
                    fixture.filename,
                    read_fixture(self.store, fixture),
                    "application/octet-stream",
                )
            self.store.save(
                self.case,
                "fixtures_staged",
                {
                    "summary": "Restored the registered input files before this fresh game launch.",
                    "fixtures": staged,
                },
            )
        return await self.launch()

    async def observe(self):
        return await self.rpc("observe")

    async def action(self, action: Action):
        return await self.rpc("action", action.model_dump())

    async def read_source(self, path: str, start: int = 1, count: int = 160):
        target = (self.repo / path).resolve()
        if not target.is_relative_to(self.repo.resolve()) or ".git" in Path(path).parts:
            raise ValueError("Source path must stay within the repository")
        if not target.is_file() or target.stat().st_size > 2_000_000:
            raise ValueError("Not a readable source file")
        start = max(1, start)
        lines = target.read_text(errors="replace").splitlines()
        return "\n".join(
            f"{i + 1}: {line}"
            for i, line in enumerate(lines)
            if start - 1 <= i < start - 1 + min(count, 240)
        )

    async def search(self, query: str):
        _, output = await self.exec(
            [
                "rg",
                "-n",
                "-i",
                "-m",
                "8",
                "--max-count",
                "8",
                "--glob",
                "!*.svg",
                "--glob",
                "!*.json",
                "--glob",
                "!gradle.lockfile",
                "--",
                query,
                ".",
            ],
            check=False,
        )
        return output[:16000]
