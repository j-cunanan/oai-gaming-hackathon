import asyncio, json, sys
from pathlib import Path
import yaml
from repro.config import Settings
from repro.models import Case, CaseInput
from repro.orchestration.manager import Manager
from repro.storage.store import Store

async def main():
    manifest=yaml.safe_load(Path(sys.argv[1]).read_text())
    cfg=Settings(data_dir=Path('.repro/qualification-controls'))
    store=Store(cfg.root)
    inputs=dict(manifest['input']);inputs['target_commit']=manifest['evaluator']['fix_commit'];inputs['title']='Human-fixed control: '+inputs['title']
    case=Case(report=CaseInput.model_validate(inputs))
    store.save(case,'received')
    index=Path('.repro/qualification-controls/index.json')
    rows=json.loads(index.read_text()) if index.exists() else {}
    rows[manifest['id']]=case.id;index.write_text(json.dumps(rows,indent=2))
    print('Preparing control',manifest['id'],case.id,flush=True)
    await Manager(cfg,store).prepare(case)
    result=store.get(case.id)
    print(result.state,result.summary,flush=True)

asyncio.run(main())
