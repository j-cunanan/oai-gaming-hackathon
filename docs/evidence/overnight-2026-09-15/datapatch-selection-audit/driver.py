import asyncio,base64,hashlib,json
from pathlib import Path
from repro.agents.openai import Model
from repro.agents.oracle import verify
from repro.config import Settings
from repro.models import Action,Case
from repro.storage.store import Store

async def main():
 source=Store(Settings().root); original=source.get('md-12620-terra-overnight-01')
 output=Path('.repro/overnight-2026-09-15/datapatch-selection-audit')
 assert not output.exists(); output.mkdir()
 settings=Settings(max_model_calls=5,reasoning_effort='medium',data_dir=output/'store')
 store=Store(settings.root); case=Case(id='audit-12620-selection',report=original.report)
 model=Model(settings,store,case)
 oracle=original.reproduction.oracle.model_copy(deep=True)
 oracle.checkpoints.insert(1,'patch_initial_save')
 rows=[]; hashes={}; pending=[]
 result={'scope':'Reverification of five retained baseline recordings with the omitted initial-save checkpoint included; no fresh game executions and no change to original case outcome.','original_case':original.id,'original_result':'3/5 confirmed','original_oracle':original.reproduction.oracle.model_dump(),'reviewed_oracle':oracle.model_dump(),'model':settings.model,'reasoning_effort':settings.reasoning_effort,'runs':rows,'source_sha256':hashes}
 try:
  for event in source.latest_events(original.id,400):
   d=event['data']
   if event['kind']=='action' and d.get('phase')=='confirmation':pending.append(d)
   if event['kind']!='replay' or d.get('phase')!='confirmation':continue
   assert len(pending)==len(original.reproduction.steps)
   frames={};actions=[]
   for index,item in enumerate(pending,1):
    action=Action.model_validate(item['action']);actions.append(action)
    if not action.checkpoint:continue
    artifact=item['screenshot_after'];path,_=source.artifact_path(original.id,artifact);raw=path.read_bytes();hashes[artifact]=hashlib.sha256(raw).hexdigest()
    observation={'screenshot':base64.b64encode(raw).decode(),'screenshot_artifact':artifact,'process':item['process']}
    frames[action.checkpoint]={'index':index,'action':action.model_dump(exclude={'semantic'}),'observation':observation}
   verdict=await verify(model,oracle,observation,launched_ok=True,checkpoints=frames,actions=actions)
   rows.append({'recorded_replay_event':event['seq'],'original_verdict':d['verdict'],'reviewed_verdict':verdict.model_dump()})
   result['usage']=case.usage.model_dump();(output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
   print(event['seq'],verdict.observed,verdict.confidence,verdict.explanation,flush=True);pending=[]
 finally:await model.close()
asyncio.run(main())
