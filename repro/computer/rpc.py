import asyncio
import json
from pathlib import Path


class WorkerRPC:
    """One ordered JSON-lines connection to a worker, never a public network service."""

    def __init__(self, process, stderr_path):
        self.process, self.stderr_path = process, stderr_path
        self.lock = asyncio.Lock()

    @classmethod
    async def start(cls, argv: list[str], stderr_path: Path):
        with stderr_path.open("wb") as stderr:
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=stderr,
                limit=16 * 1024 * 1024,
            )
        return cls(process, stderr_path)

    async def request(self, operation: str, args: dict | None = None, *, timeout=30):
        async with self.lock:
            try:
                async with asyncio.timeout(timeout):
                    self.process.stdin.write(
                        (json.dumps({"operation": operation, "args": args or {}}) + "\n").encode()
                    )
                    await self.process.stdin.drain()
                    line = await self.process.stdout.readline()
                    if not line:
                        detail = self.stderr_path.read_text(errors="replace")[-2000:]
                        raise RuntimeError(
                            f"Worker connection closed. Rebuild the worker image. {detail}"
                        )
                    response = json.loads(line)
            except (TimeoutError, asyncio.CancelledError):
                # An unread reply must never be confused with the next action's result.
                await self.close()
                raise
            except (ConnectionError, ValueError) as exc:
                await self.close()
                raise RuntimeError(
                    "Invalid or interrupted worker connection; restart the worker"
                ) from exc
            if not response.get("ok"):
                raise ValueError(response.get("error", "Worker rejected the request"))
            return response["result"]

    async def close(self):
        if self.process.stdin:
            self.process.stdin.close()
        try:
            async with asyncio.timeout(2):
                await self.process.wait()
        except TimeoutError:
            if self.process.returncode is None:
                self.process.kill()
            await self.process.wait()
