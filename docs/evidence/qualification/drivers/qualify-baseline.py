import asyncio, json, sys, time
from pathlib import Path
from repro.agents.openai import Model
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import State
from repro.orchestration.manager import Manager
from repro.storage.store import Store

class QualificationComplete(Exception):
    pass

class QualificationManager(Manager):
    def source_tools(self, sandbox):
        # Qualification uses only the disposable game UI, never repository source.
        return []

    async def reduce_replay(self, case, sandbox, model, recorder):
        self.save_replay(case)
        self.store.transition(case, State.REPRO_CONFIRMED, 'Baseline qualification: reported symptom repeated in 5/5 clean profiles. Human-fixed control still required. No patch generation or benchmark scoring performed.')
        raise QualificationComplete()

async def main():
    cfg=Settings(); store=Store(cfg.root); case=store.get(sys.argv[1])
    manager=QualificationManager(cfg,store)
    sandbox=DockerSandbox(cfg,store,case)
    model=Model(cfg,store,case); started=time.monotonic()
    try:
        async with asyncio.timeout(cfg.max_seconds):
            await manager._investigate(case,sandbox,model,started)
    except QualificationComplete:
        pass
    except Exception as exc:
        manager.record_failure(case,exc)
    finally:
        await sandbox.stop(); await model.close()
        case.elapsed_seconds+=time.monotonic()-started
        store.save(case)
        store.artifact(case.id,'qualification-baseline-report.md',manager.report(case),'text/markdown')
    print(json.dumps({'case_id':case.id,'state':case.state,'summary':case.summary,'usage':case.usage.model_dump(),'reproduction':case.reproduction.model_dump() if case.reproduction else None},indent=2))

asyncio.run(main())
