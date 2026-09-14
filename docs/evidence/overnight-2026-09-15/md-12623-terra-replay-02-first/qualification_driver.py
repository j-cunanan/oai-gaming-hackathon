"""Freshly qualify a supplied AI color-readback trace with operator-selected checkpoints before AI diagnosis/patching."""
import asyncio,hashlib,json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
import yaml
from repro.agents.openai import Model,BudgetExceeded
from repro.computer.recorder import Recorder
from repro.computer.replay import replay
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.github.history import audit_history
from repro.models import Action,BugSpec,Case,CaseInput,OracleSpec,Reproduction,State
from repro.orchestration.manager import Manager
from repro.process import run
from repro.storage.store import Store

async def main():
 started=time.monotonic();deadline=datetime(2026,9,14,22,4,37,tzinfo=timezone.utc)
 seconds=min(3300,int((deadline-datetime.now(timezone.utc)).total_seconds())-480)
 assert seconds>600,'Insufficient time for a new paid job'
 image='sha256:63be22a3b69283ede936a1bb49c99df7109938a5c13c5c41123b6d0770024162'
 settings=Settings(worker_image=image,model='gpt-5.6-terra',reasoning_effort='max',max_output_tokens=24000,request_timeout_seconds=450,max_model_calls=120,max_actions=200,max_seconds=seconds,validation_network=True,repetitions=5)
 store=Store(settings.root);cid='md-12623-terra-replay-02';assert cid not in {c.id for c in store.list()}
 manifest=Path('benchmarks/candidates/MD-candidate-12623-replay-guided.yaml');data=yaml.safe_load(manifest.read_text())
 source=Path('docs/evidence/overnight-2026-09-15/md-12623-terra-max-01')
 original=json.loads((source/'result.json').read_text())
 events=[json.loads(line) for line in (source/'events.jsonl').read_text().splitlines()]
 rows=[e for e in events if e['kind']=='action' and e['data']['phase']=='investigation' and 55<=e['data']['index']<=83]
 assert [e['data']['index'] for e in rows]==list(range(55,84))
 steps=[Action.model_validate(e['data']['action']) for e in rows]
 assert len(steps)==29 and all(a.action!='scroll' for a in steps)
 oracle=OracleSpec(kind='sequence',description='Required sequence: enter six-digit ff0300 in the Colored Wall picker, confirm it, place and pick the wall, then reopen its picker; also enter and confirm ff0300 for Colored Floor and reopen that picker. The reported bug is readback ff0200ff instead of the committed ff0300ff for both tile types. Establish actual input, commit and relevant picker identity from chronological evidence. Correct behavior is retaining ff0300ff in both readbacks. This scope does not test all reported values or adjacent floor placement.',checkpoints=['final-enter-wall-ff0300','final-confirm-wall-ff0300','final-readback-wall-ff0200','final-enter-floor-ff0300','final-confirm-floor-ff0300','final-readback-floor-ff0200'])
 assert [a.checkpoint for a in steps if a.checkpoint in oracle.checkpoints]==oracle.checkpoints
 case=Case(id=cid,benchmark_id=data['id'],report=CaseInput.model_validate(data['input']),spec=BugSpec.model_validate(original['spec']))
 assert case.report.target_commit==original['report']['target_commit'] and case.report.fixtures==CaseInput.model_validate(original['report']).fixtures
 old=store.get(original['case_id']);assert old.patch_artifact is None
 sourcebox=DockerSandbox(settings,store,old);sandbox=DockerSandbox(settings,store,case)
 model=None;manager=Manager(settings,store);digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 try:
  _,resolved=await run(['docker','image','inspect','--format','{{.Id}}',image]);assert resolved.strip()==image
  await audit_history(sourcebox.repo,case.report.target_commit);await sourcebox.baseline_source_is_clean()
  for name in ['repo','gradle','baseline','prepared.json']:
   dest=sandbox.root/name
   if dest.exists():assert dest.is_dir() and not any(dest.iterdir());dest.rmdir()
   subprocess.run(['cp','-cR',str(sourcebox.root/name),str(dest)],check=True)
  history=await audit_history(sandbox.repo,case.report.target_commit);await sandbox.baseline_source_is_clean()
  assert digest(sourcebox.repo/'desktop/build/libs/Mindustry.jar')==digest(sandbox.repo/'desktop/build/libs/Mindustry.jar')==digest(sandbox.root/'baseline/Mindustry.jar')
  baseline_sources=[]
  proof={'scope':__doc__,'selection':'Operator selected the final 29 recorded actions after reset (original indices 55–83) and six existing color-input/readback labels. No action parameters changed; cached triage is explicit. No retained images count as fresh confirmations.','source_case_id':old.id,'source_events_sha256':digest(source/'events.jsonl'),'source_result_sha256':digest(source/'result.json'),'manifest_sha256':digest(manifest),'driver_sha256':digest(Path(__file__)),'selected_source_events':[e['seq'] for e in rows],'selected_source_action_indices':list(range(55,84)),'source_reset_screenshot':rows[0]['data']['screenshot_before'],'oracle':oracle.model_dump(),'steps':[a.model_dump() for a in steps],'worker_image':image,'history_audit':history,'baseline_jar_sha256':digest(sandbox.root/'baseline/Mindustry.jar'),'baseline_tests_reused':baseline_sources,'fresh_profile_each_replay':True,'max_seconds':seconds,'max_model_calls':120,'parallel_scope':'Final standalone qualification job in a disposable worker; no concurrent app-managed job or shared writable game checkout/profile.'}
  proof['request_timeout_seconds']=450;proof['max_output_tokens']=24000;proof['baseline_test_scope']='Fresh baseline assertions on protocol-4 worker; no old-worker test result reused.'
  origin=store.artifact(case.id,'recorded-trigger-input.json',json.dumps(proof,indent=2),'application/json')
  store.save(case,'received',{'summary':'Recorded AI trigger supplied with explicit operator checkpoint selection; not yet freshly verified.'})
  store.save(case,'recorded_trigger_input',{'artifact':origin,'summary':proof['selection']})
  store.transition(case,State.ENVIRONMENT_PREPARING,'Running fresh baseline assertions on the new worker; compiled historical JAR and dependency cache were reused with explicit provenance.')
  await manager.record_baseline_tests(case,sandbox,refresh=True)
  sandbox.use_baseline=True
  case.reproduction=Reproduction(version=2,game='mindustry',commit=case.report.target_commit,steps=steps,oracle=oracle,original_actions=len(steps))
  model=Model(settings,store,case);recorder=Recorder(store,case,sandbox)
  store.transition(case,State.INVESTIGATING,'Replaying the supplied recorded trigger on fresh profiles before source analysis. No confirmation is assumed.')
  async with asyncio.timeout(seconds-(time.monotonic()-started)):
   for number in range(1,6):
    verdict,_=await replay(sandbox,recorder,model,steps,oracle,phase='supplied-color-confirmation')
    case.reproduction.total_runs+=1;case.reproduction.successful_runs+=int(verdict.observed);case.reproduction.evidence.extend(verdict.evidence)
    if verdict.observed and case.first_reproduced_seconds is None:case.first_reproduced_seconds=time.monotonic()-started
    store.save(case);print('FRESH BASELINE',number,verdict.model_dump(),flush=True)
    if not verdict.observed:break # An unsuccessful verdict prevents 5/5 qualification.
   rep=case.reproduction;rep.deterministic=rep.successful_runs==rep.total_runs==5;manager.save_replay(case)
   if not rep.deterministic:
    store.transition(case,State.INSUFFICIENT_EVIDENCE,f'Supplied color trigger confirmed in {rep.successful_runs}/{rep.total_runs} completed fresh verdicts; 5/5 was required. Source analysis and patching did not start.')
    return
   store.transition(case,State.REPRO_CONFIRMED,'Supplied AI-recorded color trigger confirmed in 5/5 fresh profiles. Operator checkpoint selection and cached triage remain explicit.')
   sandbox.use_baseline=False
   await manager.finish_confirmed_case(case,sandbox,model,recorder)
 except asyncio.CancelledError:
  store.transition(case,State.CANCELLED,'Recorded-trigger qualification cancelled; completed evidence retained.');raise
 except (BudgetExceeded,TimeoutError) as exc:
  store.transition(case,State.INSUFFICIENT_EVIDENCE,str(exc) or 'Recorded-trigger job reached its bounded time limit; partial evidence retained.')
 except Exception as exc:
  manager.record_failure(case,exc)
 finally:
  await sandbox.stop()
  if model:await model.close()
  case.elapsed_seconds+=time.monotonic()-started;store.save(case)
  store.artifact(case.id,'report.md',manager.report(case),'text/markdown')
  print('FINAL',case.state,case.usage.model_dump(),case.summary,flush=True)
asyncio.run(main())
