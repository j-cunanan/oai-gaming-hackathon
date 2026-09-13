import asyncio
import os
import signal
from pathlib import Path


class CommandError(RuntimeError):
    pass


async def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout=1200,
    check=True,
    input_text: str | None = None,
    output_path: Path | None = None,
) -> tuple[int, str]:
    """No host shell. Reap the entire process group on timeout/cancellation."""
    log = output_path.open("wb") if output_path else None
    proc = await asyncio.create_subprocess_exec(
        *argv,
        cwd=cwd,
        stdout=log or asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        stdin=asyncio.subprocess.PIPE if input_text is not None else asyncio.subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        async with asyncio.timeout(timeout):
            stdout, _ = await proc.communicate(
                input_text.encode() if input_text is not None else None
            )
    except BaseException:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await proc.wait()
        raise
    finally:
        if log:
            log.close()
    output = (
        output_path.read_text(errors="replace") if output_path else stdout.decode(errors="replace")
    )
    if check and proc.returncode:
        raise CommandError(f"{argv[0]} exited {proc.returncode}: {output[-5000:]}")
    return proc.returncode, output
