"""Exercise bounded sequences against real X11 events; no game or model calls."""
import argparse
import asyncio
import hashlib
import json
import shutil
from pathlib import Path
from repro.computer.recorder import Recorder
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import Action, Case, CaseInput
from repro.orchestration.computer_tools import ActionSequence, sequence_tool
from repro.storage.store import Store

WINDOW = r'''
import json
from pathlib import Path
from Xlib import X, XK, display
c=display.Display(); w=c.screen().root.create_window(100,100,300,200,0,c.screen().root_depth,X.InputOutput,X.CopyFromParent,background_pixel=c.screen().white_pixel,override_redirect=True,event_mask=X.KeyPressMask|X.KeyReleaseMask|X.ButtonPressMask|X.ButtonReleaseMask)
w.map();w.set_input_focus(X.RevertToParent,X.CurrentTime);c.sync()
p=Path('/workspace/runtime/probe-events.json');events=[]
p.write_text('[]');Path('/workspace/runtime/probe-ready').write_text('ready')
while True:
 e=c.next_event()
 if e.type not in (X.KeyPress,X.KeyRelease,X.ButtonPress,X.ButtonRelease):continue
 key=c.keycode_to_keysym(e.detail,0) if e.type in (X.KeyPress,X.KeyRelease) else 0
 events.append({'type':e.type,'detail':e.detail,'state':e.state,'time':e.time,'keysym':key})
 p.write_text(json.dumps(events))
 if e.type==X.KeyRelease and key==XK.XK_Escape:break
w.destroy();c.close()
'''

async def main(out, image):
 assert not out.exists(), 'Use a new output folder'
 out.mkdir(parents=True)
 settings=Settings(data_dir=out/'store',sandbox_dir=out/'sandboxes',worker_image=image)
 store=Store(settings.root);case=Case(id='sequence-driver-probe',report=CaseInput(title='X11 sequence probe',body='Infrastructure validation only; not a game reproduction.',target_commit='a'*40))
 store.save(case,'received')
 sandbox=DockerSandbox(settings,store,case);sandbox.repo.mkdir(exist_ok=True)
 (sandbox.root/'probe-window.py').write_text(WINDOW)
 recorder=Recorder(store,case,sandbox);flattened=[]
 async def computer(action):
  result=await recorder.act(action,phase='driver-sequence')
  flattened.append(action);return result
 tool=sequence_tool(recorder,computer,lambda:20-len(flattened),phase='driver-sequence')
 async def start():
  await sandbox.start(fresh_profile=True)
  await sandbox.rpc('launch',{'argv':['python3','/workspace/probe-window.py']})
  async with asyncio.timeout(10):
   while not (sandbox.root/'runtime/probe-ready').exists():await asyncio.sleep(.05)
  recorder.reset_attempt();return recorder.capture(await sandbox.observe(),'probe-initial')
 def events():return json.loads((sandbox.root/'runtime/probe-events.json').read_text())
 def verify(xs):
  click=next(e for e in xs if e['type']==4)
  down=next(e for e in xs if e['type']==2 and e['keysym']==ord('w'))
  up=next(e for e in xs if e['type']==3 and e['keysym']==ord('w'))
  held=(up['time']-down['time'])%2**32
  typed=''.join(chr(e['keysym']) for e in xs if e['type']==2 and 32<=e['keysym']<127 and e['keysym']!=ord('w'))
  assert click['state']&4 and held>=300 and typed=='repro',(click,held,typed)
  return {'ctrl_at_click':True,'held_w_ms':held,'typed_text':typed}
 try:
  await start(); image_id=await sandbox.image_id()
  actions=[Action(action='click',x=150,y=150,keys=['ctrl'],seconds=0,checkpoint='modifier'),Action(action='keypress',keys=['w'],hold_seconds=.3,seconds=0,checkpoint='held-key'),Action(action='type',text='repro',seconds=0),Action(action='keypress',keys=['enter'],seconds=.2,checkpoint='completed')]
  result=await tool.handler(ActionSequence(actions=actions));first=events();a=verify(first)
  assert result['sequence']['executed']==4 and flattened==actions
  (out/'sequence-x11.json').write_text(json.dumps(first,indent=2)+'\n')
  await start()
  for action in flattened:await recorder.act(action,phase='ordinary-replay')
  second=events();b=verify(second)
  assert [(e['type'],e['detail'],e['state']) for e in first]==[(e['type'],e['detail'],e['state']) for e in second]
  (out/'replay-x11.json').write_text(json.dumps(second,indent=2)+'\n')
  stopped=await tool.handler(ActionSequence(actions=[Action(action='keypress',keys=['esc'],seconds=.5),Action(action='type',text='must-not-run',seconds=0)]))
  assert stopped['sequence']['executed']==1 and stopped['sequence']['stop_reason']=='game_not_running'
  already=await tool.handler(ActionSequence(actions=[Action(action='type',text='also-must-not-run',seconds=0),Action(action='wait',seconds=0)]))
  assert already['sequence']['executed']==0 and already['sequence']['stop_reason']=='game_not_running'
  all_events=[];cursor=0
  while page:=store.events(case.id,cursor):all_events+=page;cursor=page[-1]['seq']
  (out/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in all_events))
  artifacts={}
  (out/'artifacts').mkdir()
  for item in store.artifacts(case.id):
   source,_=store.artifact_path(case.id,item['id']);shutil.copy2(source,out/'artifacts'/item['id']);artifacts[item['id']]=item['sha256']
  summary={'scope':__doc__,'worker_image':image_id,'sequence_actions':4,'model_calls':0,'normal_replay_matches_x11_events':True,'sequence':a,'ordinary_replay':b,'stopped_after_exit_executed':1,'already_exited_executed':0,'sequence_elapsed_seconds':[e['data']['elapsed_seconds'] for e in all_events if e['kind']=='action_sequence'],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('repro/orchestration/computer_tools.py'),Path('repro/computer/recorder.py'),Path(__file__)]},'artifact_sha256':artifacts}
  (out/'result.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in {'source_sha256','artifact_sha256'}},indent=2))
 finally:await sandbox.stop()

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--image',required=True);args=p.parse_args();asyncio.run(main(args.output.resolve(),args.image))
