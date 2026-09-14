"""Independent review of selected retained RTS frames, not a fresh game execution."""
import asyncio,base64,hashlib,json
from pathlib import Path
from repro.agents.openai import Model
from repro.agents.oracle import verify
from repro.config import Settings
from repro.models import Action,Case,CaseInput,OracleSpec
from repro.storage.store import Store

async def main():
 source=Path('docs/evidence/overnight-2026-09-15/md-12565-terra-prepared-03')
 output=Path('.repro/overnight-2026-09-15/unit-rts-retained-audit');assert not output.exists();output.mkdir()
 original=json.loads((source/'result.json').read_text())
 events=[json.loads(line) for line in (source/'events.jsonl').read_text().splitlines()]
 selected=[27,28,29,30,33]
 rows=[e for e in events if e['kind']=='action' and e['data']['phase']=='investigation' and e['data']['index']<=33]
 assert [e['data']['index'] for e in rows]==list(range(1,34))
 settings=Settings(data_dir=output/'store',model='gpt-5.6-terra',reasoning_effort='max',max_output_tokens=16000,max_model_calls=1,request_timeout_seconds=300)
 store=Store(settings.root);case=Case(id='audit-unit-rts-retained',report=CaseInput.model_validate(original['report']));model=Model(settings,store,case)
 frames={};actions=[];sources={};labels=[]
 result={'scope':__doc__,'source_case_id':original['case_id'],'original_outcome':'FAILED: independent verifier timed out; no saved reproduction or patch','selection':'Operator-selected five existing investigator checkpoint labels from the retained RTS segment. The original timed-out final oracle is unknown and is not reconstructed or attributed to the investigator.','selected_action_indices':selected,'model':settings.model,'reasoning_effort':settings.reasoning_effort,'request_timeout_seconds':settings.request_timeout_seconds,'automatic_retries':0,'source_sha256':sources}
 for e in rows:
  d=e['data'];a=Action.model_validate(d['action']);actions.append(a)
  if d['index'] not in selected:continue
  assert a.checkpoint
  name=d['screenshot_after'];p=source/'artifacts'/name;raw=p.read_bytes();sources[str(p)]=hashlib.sha256(raw).hexdigest()
  obs={'screenshot':base64.b64encode(raw).decode(),'screenshot_artifact':name,'process':d['process']}
  frames[a.checkpoint]={'index':d['index'],'action':a.model_dump(),'observation':obs};labels.append(a.checkpoint)
 for p in [source/'result.json',source/'events.jsonl',source/'artifacts.json',Path(__file__)]:sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 oracle=OracleSpec(kind='sequence',description=original['spec']['observed_behavior'],checkpoints=labels);result['reviewed_oracle']=oracle.model_dump();result['trace']=[a.model_dump() for a in actions]
 (output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
 try:
  async with asyncio.timeout(330):verdict=await verify(model,oracle,obs,launched_ok=True,checkpoints=frames,actions=actions)
  result['verdict']=verdict.model_dump();print(json.dumps(result['verdict'],indent=2),flush=True)
 except Exception as exc:
  result['error']={'type':type(exc).__name__,'message':str(exc)};print(result['error'],flush=True)
 finally:
  await model.close();result['usage']=case.usage.model_dump();(output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
  (output/'audit-events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in store.events(case.id)))
  print(result['usage'],flush=True)
asyncio.run(main())
