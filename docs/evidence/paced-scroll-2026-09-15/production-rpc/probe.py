"""Verify production protocol-4 worker RPC scrolling against the retained Arc SDL backend; no AI requests or game-bug verdicts."""
import asyncio,hashlib,json,shutil,subprocess,time
from pathlib import Path
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import Action,Case,CaseInput
from repro.storage.store import Store

async def main():
 out=Path('.repro/overnight-2026-09-15/scroll-worker-probe').resolve();image='sha256:63be22a3b69283ede936a1bb49c99df7109938a5c13c5c41123b6d0770024162'
 source=Path('/tmp/repro-oai-gaming-workspaces/md-12565-terra-prepared-03/baseline/Mindustry.jar')
 settings=Settings(data_dir=out/'store',sandbox_dir=out/'sandboxes',worker_image=image)
 store=Store(settings.root);case=Case(id='arc-wheel-probe',report=CaseInput(title='Arc wheel delivery probe',body=__doc__,target_commit='7e80948b58138a569e119857e0add95762d7e0bb'))
 box=DockerSandbox(settings,store,case);box.repo.mkdir(exist_ok=True);shutil.copy2(out/'ArcWheelProbe.java',box.root/'ArcWheelProbe.java')
 subprocess.run(['cp','-c',str(source),str(box.repo/'Mindustry.jar')],check=True)
 result={'scope':__doc__,'worker_image':image,'jar_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'probe_java_sha256':hashlib.sha256((out/'ArcWheelProbe.java').read_bytes()).hexdigest(),'probe_python_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'worker_source_sha256':hashlib.sha256(Path('infra/docker/worker.py').read_bytes()).hexdigest(),'sandbox_source_sha256':hashlib.sha256(Path('repro/computer/sandbox.py').read_bytes()).hexdigest(),'samples':[]}
 try:
  await box.start(fresh_profile=True);await box.exec(['javac','-cp','/workspace/repo/Mindustry.jar','-d','/workspace/classes','/workspace/ArcWheelProbe.java'])
  for sleep in [16,50,100]:
   for mode in ['worker-rpc']:
    for number in range(1,4):
     await box.rpc('terminate');ready=box.root/'runtime/probe-ready';ready.unlink(missing_ok=True)
     await box.rpc('launch',{'argv':['java','-cp','/workspace/classes:/workspace/repo/Mindustry.jar','ArcWheelProbe',str(sleep)]})
     async with asyncio.timeout(15):
      while not ready.exists():await asyncio.sleep(.1)
     await asyncio.sleep(.3)
     code="import pyautogui as pg; pg.FAILSAFE=False; pg.PAUSE=.12; pg.moveTo(640,360); " + ("pg.scroll(-8)" if mode=='burst' else "[pg.scroll(-1) for _ in range(8)]")
     amount=8 if number==2 else -8
     before=time.monotonic();await box.action(Action(action='scroll',x=640,y=360,scroll_y=amount,seconds=0));elapsed=time.monotonic()-before;await asyncio.sleep(.4)
     obs=await box.observe();raw=(box.root/'runtime/game.log').read_text();name=f'{sleep}-{mode}-{number}.log';(out/name).write_text(raw)
     rows=[json.loads(l) for l in raw.splitlines() if l.startswith('{"frame":')]
     item={'sleep_ms':sleep,'mode':mode,'trial':number,'requested':amount,'received_wheel_events':sum(r['wheel_events'] for r in rows),'axis_sum':sum(r['axis'] for r in rows),'frames_with_wheel':len(rows),'input_elapsed_seconds':elapsed,'log':name,'log_sha256':hashlib.sha256(raw.encode()).hexdigest()}
     assert item['received_wheel_events']==8 and item['axis_sum']==amount,item
     result['samples'].append(item);print(json.dumps(item),flush=True);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 finally:await box.stop()
asyncio.run(main())
