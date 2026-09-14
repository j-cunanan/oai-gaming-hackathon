"""Freshly qualify an explicitly supplied AI-recorded trigger before AI diagnosis/patching."""
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
 seconds=min(5400,int((deadline-datetime.now(timezone.utc)).total_seconds())-240)
 assert seconds>600,'Insufficient time for a new paid job'
 image='sha256:d3c91fca2fc42c5f8d48433d0ce2cb4cb565f5f48dcf2ab6facdb924d597ba3d'
 settings=Settings(worker_image=image,model='gpt-5.6-terra',reasoning_effort='max',max_output_tokens=16000,request_timeout_seconds=300,max_model_calls=120,max_actions=200,max_seconds=seconds,validation_network=True,repetitions=5)
 store=Store(settings.root);cid='md-12565-terra-replay-05';assert cid not in {c.id for c in store.list()}
 manifest=Path('benchmarks/candidates/MD-candidate-12565-replay-guided.yaml');data=yaml.safe_load(manifest.read_text())
 source=Path('docs/evidence/overnight-2026-09-15/md-12565-terra-prepared-03')
 original=json.loads((source/'result.json').read_text())
 auditpath=Path('.repro/overnight-2026-09-15/unit-rts-retained-audit/audit.json');audit=json.loads(auditpath.read_text());assert audit['verdict']['observed'] and audit['verdict']['expected_state_reached']
 events=[json.loads(line) for line in (source/'events.jsonl').read_text().splitlines()]
 rows=[e for e in events if e['kind']=='action' and e['data']['phase']=='investigation' and e['data']['index']<=33]
 assert [e['data']['index'] for e in rows]==list(range(1,34))
 steps=[Action.model_validate(e['data']['action']) for e in rows];oracle=OracleSpec.model_validate(audit['reviewed_oracle'])
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
  for commit,b in old.baseline_tests.items():
   assert commit==case.report.target_commit and b.worker_image==image and b.status=='completed'
   path,_=store.artifact_path(old.id,b.artifact);raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==b.log_sha256
   copied=b.model_copy(deep=True);copied.artifact=store.artifact(case.id,'reused-baseline-tests.log',raw);case.baseline_tests[commit]=copied
   baseline_sources.append({'original_case':old.id,'original_artifact':b.artifact,'new_artifact':copied.artifact,'original_timestamp':b.timestamp,'sha256':b.log_sha256})
  proof={'scope':__doc__,'selection':'Operator selected first 33 existing AI-recorded actions and five existing RTS labels. No action parameters were changed. No retained-image review is counted as a fresh replay.','source_case_id':old.id,'source_events_sha256':digest(source/'events.jsonl'),'source_result_sha256':digest(source/'result.json'),'manifest_sha256':digest(manifest),'driver_sha256':digest(Path(__file__)),'selected_source_events':[e['seq'] for e in rows],'selected_source_action_indices':list(range(1,34)),'oracle':oracle.model_dump(),'steps':[a.model_dump() for a in steps],'worker_image':image,'history_audit':history,'baseline_jar_sha256':digest(sandbox.root/'baseline/Mindustry.jar'),'baseline_tests_reused':baseline_sources,'fresh_profile_each_replay':True,'max_seconds':seconds,'max_model_calls':120,'parallel_scope':'Separate disposable worker from the app-managed generator investigation; no shared writable game checkout or profile.'}
  origin=store.artifact(case.id,'recorded-trigger-input.json',json.dumps(proof,indent=2),'application/json')
  store.save(case,'received',{'summary':'Recorded AI trigger supplied with explicit operator checkpoint selection; not yet freshly verified.'})
  store.save(case,'recorded_trigger_input',{'artifact':origin,'summary':proof['selection']})
  case.reproduction=Reproduction(version=2,game='mindustry',commit=case.report.target_commit,steps=steps,oracle=oracle,original_actions=len(steps))
  model=Model(settings,store,case);recorder=Recorder(store,case,sandbox)
  store.transition(case,State.INVESTIGATING,'Replaying the supplied recorded trigger on fresh profiles before source analysis. No confirmation is assumed.')
  async with asyncio.timeout(seconds-(time.monotonic()-started)):
   for number in range(1,6):
    verdict,_=await replay(sandbox,recorder,model,steps,oracle,phase='recorded-trigger-confirmation')
    case.reproduction.total_runs+=1;case.reproduction.successful_runs+=int(verdict.observed);case.reproduction.evidence.extend(verdict.evidence)
    if verdict.observed and case.first_reproduced_seconds is None:case.first_reproduced_seconds=time.monotonic()-started
    store.save(case);print('FRESH BASELINE',number,verdict.model_dump(),flush=True)
   rep=case.reproduction;rep.deterministic=rep.successful_runs==rep.total_runs==5;manager.save_replay(case)
   if not rep.deterministic:
    store.transition(case,State.INSUFFICIENT_EVIDENCE,f'Supplied trigger confirmed in {rep.successful_runs}/5 fresh profiles; source analysis and patching did not start.')
    return
   store.transition(case,State.REPRO_CONFIRMED,'Supplied AI-recorded RTS trigger confirmed in 5/5 fresh profiles. Operator checkpoint selection remains explicit.')
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
