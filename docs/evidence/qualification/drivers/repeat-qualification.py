import asyncio, json, sys
from pathlib import Path
from pydantic import BaseModel
from repro.agents.openai import Model
from repro.computer.recorder import Recorder
from repro.computer.replay import replay
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import Action, State
from repro.storage.store import Store

class PersistenceVerdict(BaseModel):
    patch_present_before: bool
    patch_list_empty_after_deletion: bool
    same_map_saved_and_reopened: bool
    patch_present_after_reopen: bool
    confidence: float
    explanation: str

async def main():
    source_store=Store(Settings().root); source=source_store.get(sys.argv[1])
    control=sys.argv[2] if len(sys.argv)>2 else None
    cfg=Settings(data_dir=Path('.repro/qualification-controls') if control else Path('.repro'),max_model_calls=10)
    store=Store(cfg.root);case=store.get(control or source.id);box=DockerSandbox(cfg,store,case);model=Model(cfg,store,case);recorder=Recorder(store,case,box)
    persistence=source.id=='6b067de945d7'
    if persistence:
        steps=[Action.model_validate(e['data']['action']) for e in source_store.events(source.id) if e['kind']=='action' and e['data'].get('phase')=='investigation']
    else:
        steps=source.reproduction.steps
        store.artifact(case.id,'qualification-before-startup-fix.json',case.model_dump_json(indent=2),'application/json')
    results=[]
    try:
        for trial in range(1,2 if control else 6):
            if not persistence:
                verdict,obs=await replay(box,recorder,model,steps,source.reproduction.oracle,phase=f'qualified-{trial}')
                ok=verdict.observed and 'Cannot read field "id" because "this.unitTeam" is null' in obs.get('logs','')
                row={'trial':trial,'passed':ok,'verdict':verdict.model_dump(),'signature_matched':ok,'screenshot':obs['screenshot_artifact']}
            else:
                recorder.capture(await box.reset(),f'temporal-{trial}-start')
                frames=[]
                for index,action in enumerate(steps,1):
                    obs=await recorder.act(action,phase=f'temporal-{trial}')
                    if index in (26,28,31,36,40):
                        frames.append({'step':index,'label':action.semantic,'image':obs['screenshot'],'artifact':obs['screenshot_artifact']})
                content=[{'type':'input_text','text':'Independently inspect this chronological game UI sequence. Determine whether the sole patch entry (one field) is present before deletion, the list becomes empty after deletion with no search filter, and a patch entry is present or absent after saving and reopening the same PatchPersistence map. Its optional displayed name may be PersistenceProbe or <unnamed>; name spelling is not the reported bug. Verify the list contents and map identity rather than relying on the name. Do not assume an outcome based on baseline/fixed labels. The actual recorded steps are: '+json.dumps([a.model_dump() for a in steps])}]
                for f in frames:
                    content.extend([{'type':'input_text','text':f"Recorded step {f['step']}: {f['label']}"},{'type':'input_image','image_url':'data:image/png;base64,'+f['image'],'detail':'original'}])
                model.budget()
                response=await model.client.responses.parse(model=cfg.model,store=False,input=[{'role':'user','content':content}],text_format=PersistenceVerdict,reasoning={'effort':cfg.reasoning_effort},max_output_tokens=1000)
                model.record(response,'qualification chronological persistence verification')
                verdict=response.output_parsed
                ok=bool(verdict and verdict.patch_present_before and verdict.patch_list_empty_after_deletion and verdict.same_map_saved_and_reopened and verdict.patch_present_after_reopen==(not bool(control)) and verdict.confidence>=0.8 and obs['process']['running'])
                row={'trial':trial,'passed':ok,'verdict':verdict.model_dump() if verdict else None,'frames':[{k:v for k,v in f.items() if k!='image'} for f in frames]}
            results.append(row)
            print(json.dumps(row),flush=True)
        passed=sum(r['passed'] for r in results)
        summary={'case_id':case.id,'source_case_id':source.id,'commit':case.report.target_commit,'control':bool(control),'passed':passed,'total':len(results),'runs':results,'steps':[a.model_dump() for a in steps],'oracle':'chronological screenshot sequence' if persistence else 'nonzero exit and TargetDummy null unitTeam signature','limitations':['Qualification evidence only; temporal oracle is not yet implemented in the standard single-frame replay verifier.'] if persistence else []}
        path=Path('.repro')/(source.id+('-control-repeat' if control else '-qualification-repeat')+'.json');path.write_text(json.dumps(summary,indent=2))
        store.artifact(case.id,'qualification-repeat.json',json.dumps(summary,indent=2),'application/json')
        if not persistence and not control:
            case.reproduction.successful_runs=passed;case.reproduction.total_runs=len(results);case.reproduction.deterministic=passed==5
            store.transition(case,State.REPRO_CONFIRMED if passed==5 else State.INSUFFICIENT_EVIDENCE,f'Post-readiness-fix qualification: {passed}/5 clean runs matched the save-crash signature. Original 4/5 attempt retained; human-fixed control pending.')
        print('RESULT',passed,len(results),flush=True)
    finally:
        await box.stop();await model.close()

asyncio.run(main())
