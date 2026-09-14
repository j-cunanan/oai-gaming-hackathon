import asyncio, json, sys, time
from pathlib import Path
from pydantic import BaseModel
from repro.agents.openai import Model, Tool
from repro.computer.recorder import Recorder
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import Action, State
from repro.orchestration.manager import Empty, FixedVerdict
from repro.storage.store import Store

class Finish(BaseModel):
    expected_behavior_verified: bool
    summary: str
    limitations: list[str]

async def main():
    source=Store(Settings().root).get(sys.argv[1])
    if not source.reproduction or not source.reproduction.deterministic:
        raise SystemExit('Baseline must be qualified first')
    cfg=Settings(data_dir=Path('.repro/qualification-controls'),max_model_calls=30,max_seconds=600)
    store=Store(cfg.root); case=store.get(sys.argv[2]); box=DockerSandbox(cfg,store,case)
    if not (box.root/'prepared.json').exists(): raise SystemExit('Control is not prepared')
    model=Model(cfg,store,case); recorder=Recorder(store,case,box)
    finished=None; started=time.monotonic(); result={'baseline_case_id':source.id,'control_case_id':case.id,'baseline_commit':source.report.target_commit,'control_commit':case.report.target_commit,'scope':'Historical human-fixed qualification control, not a generated patch.'}
    try:
        async with asyncio.timeout(600):
            obs=recorder.capture(await box.reset(),'control-start')
            for action in source.reproduction.steps:
                obs=await recorder.act(action.model_copy(update={"seconds":max(action.seconds,0.75)}),phase='baseline-trigger-on-control')
            async def computer(action):return await recorder.act(action.model_copy(update={"seconds":max(action.seconds,0.75)}),phase='control-target-verification')
            async def observe(_):return await recorder.observe()
            async def finish(args):
                nonlocal finished
                finished=args
                return {'recorded':True}
            await model.loop('You are checking a historical fixed build, not generating a patch. The baseline trigger has just been replayed with extra settling time. Verify that the required block/patch was actually selected and placed; if the setup missed its target, repair it through the UI before testing save/reload. Use only the UI to verify the expected behavior. For a save-crash report, explicitly save, leave the editor, reopen the same saved map, and show that the Target Dummy remains. For a deleted data-patch report, reopen the saved map and show that the deleted patch stays absent. For hex precision, verify ff0200 and ff0300 remain distinct and inspect the displayed retained hex values after reopening the picker. Do not claim success merely because the app is alive. If blocked or unclear, finish honestly. Public report follows:\n'+source.report.body,[Tool('computer','Perform one action in the disposable game UI.',Action,computer),Tool('observe','Observe the current game UI.',Empty,observe),Tool('finish','Record the control outcome and limitations.',Finish,finish)],purpose='qualification human-fixed control',done=lambda:finished is not None,observation=obs,max_turns=25)
            obs=recorder.capture(await box.observe(),'control-final')
            verdict=await model.structured(FixedVerdict,'Independently assess this screen for the expected outcome of this public report: '+source.report.body+'\nThe recorded UI actions were: '+json.dumps([a.model_dump() for a in recorder.actions])+'. Check whether the actual relevant map/picker state is visible. A different menu is inconclusive. Do not infer successful save/reload without actions reaching that state. Process: '+json.dumps(obs['process']),purpose='independent control verification',screenshot=obs['screenshot'])
            result.update({'outcome':finished.model_dump(),'independent_verdict':verdict.model_dump(),'process':obs['process'],'screenshot_artifact':obs['screenshot_artifact'],'actions':[a.model_dump() for a in recorder.actions]})
            result['qualified']=bool(finished.expected_behavior_verified and verdict.expected_state_reached and verdict.symptom_absent and verdict.confidence>=0.8 and obs['process']['running'])
    except Exception as exc:
        result.update({'qualified':False,'error':type(exc).__name__+': '+str(exc)[:300]})
    finally:
        await box.stop();await model.close()
    result['usage']=case.usage.model_dump();result['elapsed_seconds']=round(time.monotonic()-started,2)
    path=Path('.repro/qualification-controls')/(source.id+'-result.json');path.write_text(json.dumps(result,indent=2))
    store.artifact(case.id,'qualification-control.json',json.dumps(result,indent=2),'application/json')
    print(json.dumps(result,indent=2))

asyncio.run(main())
