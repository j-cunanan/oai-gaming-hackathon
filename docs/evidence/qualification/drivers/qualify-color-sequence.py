import asyncio,json,sys
from pathlib import Path
from pydantic import BaseModel
from repro.agents.openai import Model
from repro.computer.recorder import Recorder
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import Action
from repro.storage.store import Store

class ColorVerdict(BaseModel):
    colored_floor_picker_verified:bool
    colored_wall_picker_verified:bool
    floor_entered_hex:str
    floor_reopened_hex:str
    wall_entered_hex:str
    wall_reopened_hex:str
    confidence:float
    explanation:str

def rgb(s):
    s=s.lower().strip().lstrip('#')
    return s[:6] if len(s)==8 else s

async def main():
    original=Store(Settings().root);source=original.get('4ef4f91d50fa')
    control=sys.argv[1] if len(sys.argv)>1 else None
    cfg=Settings(data_dir=Path('.repro/qualification-controls') if control else Path('.repro'),max_model_calls=6)
    store=Store(cfg.root);case=store.get(control or source.id);box=DockerSandbox(cfg,store,case);recorder=Recorder(store,case,box);model=Model(cfg,store,case)
    steps=[Action.model_validate(e['data']['action']) for e in original.events(source.id) if e['kind']=='action' and e['data'].get('phase')=='investigation']
    steps=[a.model_copy(update={'seconds':max(a.seconds,0.75)}) for a in steps]
    results=[]
    try:
        for trial in range(1,2 if control else 6):
            recorder.capture(await box.reset(),f'color-{trial}-start');frames=[]
            for index,action in enumerate(steps,1):
                obs=await recorder.act(action,phase=f'color-{trial}')
                if index in (12,15,23,26):frames.append({'step':index,'label':action.semantic,'image':obs['screenshot'],'artifact':obs['screenshot_artifact']})
            content=[{'type':'input_text','text':'Read the literal entered and reopened hex strings from the four chronological screenshots, first Colored Floor then Colored Wall. Report actual visible values, do not infer correctness from the labels. If a picker or value is not visible, report unknown and low confidence. The actual UI actions: '+json.dumps([a.model_dump() for a in steps])}]
            for f in frames:content.extend([{'type':'input_text','text':f"Step {f['step']}: {f['label']}"},{'type':'input_image','image_url':'data:image/png;base64,'+f['image'],'detail':'original'}])
            model.budget()
            resp=await model.client.responses.parse(model=cfg.model,store=False,input=[{'role':'user','content':content}],text_format=ColorVerdict,reasoning={'effort':cfg.reasoning_effort},max_output_tokens=1200)
            model.record(resp,'qualification chronological hex verification');v=resp.output_parsed
            expected='ff0300' if control else 'ff0200'
            ok=bool(v and v.colored_floor_picker_verified and v.colored_wall_picker_verified and rgb(v.floor_entered_hex)=='ff0300' and rgb(v.wall_entered_hex)=='ff0300' and rgb(v.floor_reopened_hex)==expected and rgb(v.wall_reopened_hex)==expected and v.confidence>=0.8 and obs['process']['running'])
            row={'trial':trial,'passed':ok,'verdict':v.model_dump() if v else None,'frames':[{k:x for k,x in f.items() if k!='image'} for f in frames]};results.append(row);print(json.dumps(row),flush=True)
        result={'case_id':case.id,'source_case_id':source.id,'commit':case.report.target_commit,'control':bool(control),'passed':sum(r['passed'] for r in results),'total':len(results),'runs':results,'steps':[a.model_dump() for a in steps],'oracle':'Entered RGB ff0300 compared with reopened RGB; alpha ff accepted separately. Both Colored Floor and Colored Wall must reach their pickers.','limitations':['Chronological qualification verifier, not yet supported by standard single-frame replay verifier.','This checks ff0300 rounding to ff0200; it does not exhaust all hex values.']}
        path=Path('.repro')/('4ef4f91d50fa'+('-control-repeat' if control else '-qualification-repeat')+'.json');path.write_text(json.dumps(result,indent=2));store.artifact(case.id,'qualification-color.json',json.dumps(result,indent=2),'application/json');print('RESULT',result['passed'],result['total'],flush=True)
    finally:await box.stop();await model.close()

asyncio.run(main())
