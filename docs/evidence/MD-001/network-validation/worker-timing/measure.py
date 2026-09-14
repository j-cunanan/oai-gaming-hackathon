import asyncio
import base64
import hashlib
import json
import shutil
import subprocess
import time
import types
import urllib.request
from pathlib import Path

from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import Case
from repro.storage.store import Store

REVISION = '9701f2c68508409db5f0d063f0f26499f1685156'
out = Path('/tmp/repro-worker-comparison')
out.mkdir(exist_ok=True)
old_source = subprocess.run(
    ['git', 'show', f'{REVISION}:repro/computer/sandbox.py'],
    capture_output=True, text=True, check=True,
).stdout
old_module = types.ModuleType('old_sandbox')
exec(compile(old_source, 'old_sandbox.py', 'exec'), old_module.__dict__)


class ReadyOldSandbox(old_module.DockerSandbox):
    async def launch(self):
        observation = await super().launch()
        async with asyncio.timeout(45):
            while True:
                if not observation['process']['running']:
                    return observation
                if self.adapter.ready_log in observation['logs']:
                    break
                await asyncio.sleep(0.5)
                observation = await self.observe()
        await asyncio.sleep(1)
        return await self.observe()


def health():
    with urllib.request.urlopen('http://127.0.0.1:8000/api/health') as r:
        return json.load(r)


async def main():
    print('Waiting for candidate validation to finish before timing.', flush=True)
    while health()['active_jobs']:
        await asyncio.sleep(2)
    cfg = Settings()
    store = Store(cfg.root)
    original = store.get('md-weather-terra-001')
    probe = Case(id='worker-speed-comparison', report=original.report)
    jar = Path('/tmp/repro-oai-gaming-workspaces/md-weather-terra-001/baseline/Mindustry.jar')
    result = {
        'old_backend_revision': REVISION,
        'baseline_sha256': hashlib.sha256(jar.read_bytes()).hexdigest(),
        'steps': [a.model_dump() for a in original.reproduction.steps],
        'method': 'Three alternating old/new pairs; same baseline, resolution, limits, fresh profile, recorded waits and load-ready guard. Excludes model calls and recorder/database writes.',
        'samples': [],
    }
    for trial in range(1, 4):
        for label, cls, tag in [
            ('old', ReadyOldSandbox, 'repro-worker:amd64'),
            ('new', DockerSandbox, 'repro-worker:amd64-fast'),
        ]:
            assert not health()['active_jobs'], 'A user job started; stop this probe'
            settings = cfg.model_copy(update={'worker_image': tag, 'sandbox_dir': Path('/tmp/repro-worker-speed-check')})
            sandbox = cls(settings, store, probe)
            sandbox.use_baseline = True
            sandbox.repo.mkdir(exist_ok=True)
            (sandbox.root / 'baseline').mkdir(exist_ok=True)
            shutil.copy2(jar, sandbox.root / 'baseline/Mindustry.jar')
            try:
                start = time.monotonic()
                obs = await sandbox.reset()
                launch_seconds = time.monotonic() - start
                timings = []
                for action in original.reproduction.steps:
                    tick = time.monotonic()
                    obs = await sandbox.action(action)
                    timings.append(time.monotonic() - tick)
                total_seconds = time.monotonic() - start
                screenshot = base64.b64decode(obs['screenshot'])
                filename = f'{label}-{trial}.png'
                (out / filename).write_bytes(screenshot)
                sample = {'worker': label, 'trial': trial, 'launch_seconds': launch_seconds, 'action_seconds': timings, 'total_seconds': total_seconds, 'process_running': obs['process']['running'], 'screenshot': filename, 'screenshot_sha256': hashlib.sha256(screenshot).hexdigest()}
                result['samples'].append(sample)
                (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
                print(json.dumps({'worker': label, 'trial': trial, 'total_seconds': total_seconds, 'launch_seconds': launch_seconds}), flush=True)
            finally:
                await sandbox.stop()


asyncio.run(main())
