"""Continue the same final color qualification budget with the two omitted, already-recorded wall checkpoints; no action or target-state relaxation."""
import asyncio,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
from repro.agents.openai import Model,BudgetExceeded
from repro.computer.recorder import Recorder
from repro.computer.replay import replay
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.models import State
from repro.orchestration.manager import Manager
from repro.storage.store import Store

async def main():
 started=time.monotonic();deadline=datetime(2026,9,14,22,4,37,tzinfo=timezone.utc)
 store=Store(Settings().root);case=store.get('md-12623-terra-replay-02')
 assert case.state==State.INSUFFICIENT_EVIDENCE and case.patch_artifact is None and case.findings is None
 rep=case.reproduction;assert len(rep.steps)==29 and rep.total_runs==1 and rep.successful_runs==0
 original_elapsed=case.elapsed_seconds
 seconds=min(3300-int(original_elapsed),int((deadline-datetime.now(timezone.utc)).total_seconds())-420)
 assert seconds>600,'Insufficient remaining time for continuation'
 image='sha256:63be22a3b69283ede936a1bb49c99df7109938a5c13c5c41123b6d0770024162'
 settings=Settings(worker_image=image,model='gpt-5.6-terra',reasoning_effort='max',max_output_tokens=24000,request_timeout_seconds=450,max_model_calls=120,max_actions=200,max_seconds=seconds,validation_network=True,repetitions=5)
 sandbox=DockerSandbox(settings,store,case);manager=Manager(settings,store);model=None
 try:
  await sandbox.baseline_source_is_clean();assert len(rep.oracle.checkpoints)==6
  old_oracle=rep.oracle.model_dump();old_steps=[a.model_dump() for a in rep.steps]
  names=set(rep.oracle.checkpoints)|{'final-place-wall-input','final-pick-placed-wall'}
  chosen=[a.checkpoint for a in rep.steps if a.checkpoint in names];assert len(chosen)==8 and len(set(chosen))==8
  first=Path('docs/evidence/overnight-2026-09-15/md-12623-terra-replay-02-first')
  snapshot=store.artifact(case.id,'qualification-before-checkpoint-completion.json',case.model_dump_json(indent=2),'application/json')
  rep.oracle=rep.oracle.model_copy(update={'checkpoints':chosen})
  assert rep.oracle.description==old_oracle['description'] and [a.model_dump() for a in rep.steps]==old_steps
  proof={'scope':__doc__,'old_oracle':old_oracle,'new_oracle':rep.oracle.model_dump(),'actions_unchanged':True,'required_postcondition_unchanged':True,'previous_fresh_result':'0/1 inconclusive: wall placement/picking not present in selected checkpoint images','previous_snapshot_artifact':snapshot,'frozen_first_result_sha256':hashlib.sha256((first/'result.json').read_bytes()).hexdigest(),'frozen_first_events_sha256':hashlib.sha256((first/'events.jsonl').read_bytes()).hexdigest(),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'original_elapsed_seconds':original_elapsed,'continuation_max_seconds':seconds,'original_total_job_budget_seconds':3300,'same_cumulative_model_call_budget':120,'worker_image':image,'request_timeout_seconds':450,'max_output_tokens':24000,'fresh_profile_each_replay':True}
  origin=store.artifact(case.id,'checkpoint-selection-revision.json',json.dumps(proof,indent=2),'application/json')
  rep.successful_runs=rep.total_runs=0;rep.evidence=[];rep.deterministic=False
  store.save(case,'checkpoint_selection_revised',{'artifact':origin,'summary':'Added the existing wall placement and picking checkpoints to the original six. Actions and required target state unchanged. Previous 0/1 result frozen; five new confirmations required within the same total job budget.'})
  model=Model(settings,store,case);recorder=Recorder(store,case,sandbox);sandbox.use_baseline=True
  store.transition(case,State.INVESTIGATING,'Freshly checking the unchanged supplied color trace with all eight required checkpoint images.')
  async with asyncio.timeout(seconds-(time.monotonic()-started)):
   for number in range(1,6):
    verdict,_=await replay(sandbox,recorder,model,rep.steps,rep.oracle,phase='complete-color-confirmation')
    rep.total_runs+=1;rep.successful_runs+=int(verdict.observed);rep.evidence.extend(verdict.evidence)
    if verdict.observed and case.first_reproduced_seconds is None:case.first_reproduced_seconds=original_elapsed+(time.monotonic()-started)
    store.save(case);print('FRESH BASELINE',number,verdict.model_dump(),flush=True)
    if not verdict.observed:break
   rep.deterministic=rep.successful_runs==rep.total_runs==5;manager.save_replay(case)
   if not rep.deterministic:
    store.transition(case,State.INSUFFICIENT_EVIDENCE,f'Complete-checkpoint trigger confirmed in {rep.successful_runs}/{rep.total_runs} fresh verdicts; 5/5 required. No source diagnosis or patching started.');return
   store.transition(case,State.REPRO_CONFIRMED,'Unchanged supplied color trace confirmed 5/5 with all eight checkpoint images. Explicit assistance and the earlier inconclusive selection remain recorded.')
   sandbox.use_baseline=False;await manager.finish_confirmed_case(case,sandbox,model,recorder)
 except asyncio.CancelledError:
  store.transition(case,State.CANCELLED,'Color qualification continuation cancelled; completed evidence retained.');raise
 except (BudgetExceeded,TimeoutError) as exc:
  store.transition(case,State.INSUFFICIENT_EVIDENCE,str(exc) or 'The original total color job budget was exhausted; partial evidence retained.')
 except Exception as exc:manager.record_failure(case,exc)
 finally:
  await sandbox.stop()
  if model:await model.close()
  case.elapsed_seconds+=time.monotonic()-started;store.save(case)
  store.artifact(case.id,'report.md',manager.report(case),'text/markdown');print('FINAL',case.state,case.usage.model_dump(),case.summary,flush=True)
asyncio.run(main())
