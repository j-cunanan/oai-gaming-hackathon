import asyncio
import json
import shutil
from pathlib import Path

from repro.adapters import ADAPTERS
from repro.config import Settings
from repro.github.history import audit_history, isolate_snapshot
from repro.models import Action, Case
from repro.process import run
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
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "runtime").mkdir(exist_ok=True)
        (self.root / "gradle").mkdir(exist_ok=True)

    async def prepare(self):
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
            code, output = await self.exec(list(self.adapter.tests), timeout=600, check=False)
            self.store.artifact(self.case.id, "baseline-tests.log", output)
            (self.root / "prepared.json").write_text(
                json.dumps(
                    {
                        "commit": self.case.report.target_commit,
                        "image": self.settings.worker_image,
                        "baseline_tests_exit_code": code,
                    }
                )
            )
        finally:
            await self.stop()

    async def start(self, network=False):
        await self.stop()
        await run(
            [
                "docker",
                "run",
                "-d",
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

    async def stop(self):
        await run(["docker", "rm", "-f", self.name], check=False, timeout=30)

    async def exec(self, argv, *, timeout=120, check=True, input_text=None, output_path=None):
        return await run(
            ["docker", "exec", "-i", self.name, *argv],
            timeout=timeout,
            check=check,
            input_text=input_text,
            output_path=output_path,
        )

    async def rpc(self, operation: str, args: dict | None = None):
        _, output = await self.exec(
            ["python3", "/opt/repro/worker.py", operation, json.dumps(args or {})], timeout=30
        )
        return json.loads(output)

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
        await run(
            [
                "docker",
                "exec",
                "-d",
                self.name,
                "python3",
                "/opt/repro/worker.py",
                "launch",
                json.dumps({"argv": argv}),
            ],
            timeout=20,
        )
        await asyncio.sleep(8)
        return await self.observe()

    async def reset(self):
        # Recreate the container, which reaps all game/Gradle child processes.
        await self.stop()
        runtime = self.root / "runtime"
        if runtime.exists():
            shutil.rmtree(runtime)
        runtime.mkdir()
        (runtime / "profile").mkdir()
        await self.start()
        return await self.launch()

    async def observe(self):
        return await self.rpc("observe")

    async def action(self, action: Action):
        await self.rpc("action", action.model_dump())
        return await self.observe()

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
