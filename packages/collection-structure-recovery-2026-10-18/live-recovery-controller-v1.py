"""One owned real common-launcher SIGINT/resume run. Prepared; execute only after root freeze signal.
No checkpoints or gates are edited. Source errors/access stops prevent resume.
"""
import argparse,datetime,hashlib,json,os,re,signal,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--proof',required=True,type=Path);p.add_argument('--execute-after-root-freeze',action='store_true');a=p.parse_args()
if not a.execute_after_root_freeze:p.error('Prepared controller requires explicit coordinated frozen-production execution flag')
repo=a.repo.resolve();out=a.out.resolve();proof=a.proof.resolve();python=repo/'.collection-runtime/venv/bin/python';gate=Path('/tmp/compliSolv-official-publication-gate')/hashlib.sha256(b'www.codepublishing.com').hexdigest()[:20]
if proof.exists() or out.exists():raise ValueError('Fresh out and proof paths required')
proof.mkdir(parents=True);now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text())
def save(n,v):
 path=proof/n
 if path.exists():raise FileExistsError('Immutable proof filename already exists: '+n)
 path.write_text(json.dumps(v,indent=2)+'\n')
def bindings():
 paths=[repo/'collect.py',repo/'.collection-runtime/runtime.json']
 for folder in [repo/'collectors/originals',repo/'collectors/ops',repo/'collectors/registry']:
  paths += [q for q in folder.rglob('*') if q.is_file() and q.suffix in ['.py','.cjs','.json','.txt'] and '__pycache__' not in q.parts and 'tests' not in q.parts and 'proof-receipts' not in q.parts]
 return {str(q.relative_to(repo)):sha(q) for q in sorted(set(paths))}
def processes():
 result={}
 for line in subprocess.check_output(['ps','-axo','pid=,ppid=,command='],text=True).splitlines():
  m=re.match(r'\s*(\d+)\s+(\d+)\s+(.*)',line)
  if m:result[int(m[1])]={'ppid':int(m[2]),'command':m[3]}
 return result
def descendant(pid,ancestor,procs):
 seen=set()
 while pid in procs and pid not in seen:
  if pid==ancestor:return True
  seen.add(pid);pid=procs[pid]['ppid']
 return False
def family_child(parent):
 proc=processes();found=[pid for pid,v in proc.items() if descendant(pid,parent,proc) and 'collectors/originals/cli.py collect ' in v['command'] and '--out '+str(out) in v['command']]
 if len(found)>1:raise RuntimeError('Multiple matching family children; refusing ambiguous signal')
 return found[0] if found else None,proc
def source_state():
 path=out/'source/checkpoint.json'
 return load(path) if path.exists() else None
requestlog=gate/'requests.jsonl';gate_before=load(gate/'state.json') if (gate/'state.json').exists() else {};start_offset=requestlog.stat().st_size if requestlog.exists() else 0
if gate_before.get('stop'):raise RuntimeError('Existing CodePublishing access stop; no execution allowed')
argv=[str(python),'-B',str(repo/'collect.py'),'--runtime',str(repo/'.collection-runtime'),'run','--target','original-flagstaff-az','--out',str(out)];before=bindings();save('started.json',{'at':now(),'command':argv,'out':str(out),'source_bindings':before,'gate_state':gate_before,'gate_request_log_start_offset':start_offset,'image_policy':'No separate image fetch/member/extraction/decode/render/OCR; exact[IMAGE]','root_frozen_execution_flag':True})
logs=[(proof/'initial.stdout.log').open('w'),(proof/'initial.stderr.log').open('w')];common=subprocess.Popen(argv,cwd=repo,stdout=logs[0],stderr=logs[1]);save('common-process-started.json',{'at':now(),'pid':common.pid,'command':argv});deadline=time.monotonic()+1200;last=0;child=None
while True:
 if common.poll() is not None:raise RuntimeError('Common job terminated before interruption opportunity: '+str(common.returncode))
 state=source_state();gate_now=load(gate/'state.json') if (gate/'state.json').exists() else {}
 if gate_now.get('stop') or state and (state.get('blocked') or state.get('errors')):
  common.wait();save('blocked-before-interruption.json',{'at':now(),'common_exit':common.returncode,'state':state,'gate':gate_now});raise RuntimeError('Actual source access/error evidence retained; no resume')
 content=[x for x in state.get('artifacts',[]) if x['role']=='content' and x['status']==200] if state else []
 if state and state.get('opening_currency') and len({x['source_url'] for x in content})>=3:
  child,proc=family_child(common.pid)
  if child:
   for entry in state['artifacts']:
    if sha(out/'source'/entry['path'])!=entry['sha256']:raise RuntimeError('Source hash failed before intentional interruption')
   observed={'at':now(),'common_pid':common.pid,'family_pid':child,'process_tree':{str(k):v for k,v in proc.items() if descendant(k,common.pid,proc)},'source_checkpoint_sha256':sha(out/'source/checkpoint.json'),'source_checkpoint':state,'durable_body_count':len(content),'checkpoint_edits':False};save('observed-before-sigint.json',observed);os.kill(child,signal.SIGINT);break
 if time.monotonic()-last>=30:print(json.dumps({'at':now(),'stage':'awaiting_at_least_three_durable_bodies','bodies':len(content)}),flush=True);last=time.monotonic()
 if time.monotonic()>deadline:raise RuntimeError('Bounded interruption opportunity absent; keep actual source/job and investigate, no blind restart')
 time.sleep(.1)
initial_exit=common.wait(timeout=120)
for stream in logs:stream.close()
state=source_state();proc_after=processes();owned=observed['process_tree'];browser_survivors={pid:proc_after[int(pid)] for pid,v in owned.items() if int(pid) in proc_after and proc_after[int(pid)]['command']==v['command'] and any(x in v['command'] for x in ['Google Chrome','chrome_crashpad','playwright/driver','node'])}
save('initial-terminal.json',{'at':now(),'common_exit':initial_exit,'source_checkpoint':state,'source_checkpoint_sha256':sha(out/'source/checkpoint.json'),'owned_browser_survivors':browser_survivors,'checkpoint_edits':False})
if browser_survivors:raise RuntimeError('Own browser descendants still active; preserve evidence and resolve only owned contexts before resume')
if state.get('errors') or state.get('blocked') or load(gate/'state.json').get('stop'):raise RuntimeError('Retained actual source error/access stop prevents automatic resume')
for entry in state['artifacts']:
 if sha(out/'source'/entry['path'])!=entry['sha256']:raise RuntimeError('Terminated generation raw hash mismatch')
cached=[dict(x) for x in state['artifacts'] if x['role']=='content' and x['status']==200];resume_offset=requestlog.stat().st_size;save('resume-started.json',{'at':now(),'same_command':argv,'cached_content':cached,'gate_request_log_resume_offset':resume_offset,'source_bindings':bindings(),'checkpoint_edits':False})
if bindings()!=before:raise RuntimeError('Frozen source/runtime changed; no automatic code migration')
logs=[(proof/'resume.stdout.log').open('w'),(proof/'resume.stderr.log').open('w')];resumed=subprocess.Popen(argv,cwd=repo,stdout=logs[0],stderr=logs[1]);last=0
while resumed.poll() is None:
 if time.monotonic()-last>=30:
  s=source_state();print(json.dumps({'at':now(),'stage':'live_resume_running','bodies':sum(x.get('role')=='content' for x in s.get('artifacts',[])) if s else None,'artifacts':len(s.get('artifacts',[])) if s else 0}),flush=True);last=time.monotonic()
 time.sleep(.5)
for stream in logs:stream.close()
final=source_state();requests=[]
with requestlog.open('rb') as stream:
 stream.seek(start_offset);raw_gate_slice=stream.read()
(proof/'gate-request-window.jsonl').write_bytes(raw_gate_slice)
with requestlog.open('rb') as stream:
 stream.seek(resume_offset)
 for line in stream:requests.append(json.loads(line))
cached_urls={x['source_url'] for x in cached};refetched=[x for x in requests if x.get('url') in cached_urls];hashes_equal=all(sha(out/'source'/x['path'])==x['sha256'] for x in cached);coverage=load(out/'coverage.json') if (out/'coverage.json').exists() else None
result={'schema':'originals-real-browser-transport-recovery-1','at':now(),'initial_common_exit':initial_exit,'resumed_common_exit':resumed.returncode,'intentional_sigint_family_pid':child,'same_command_resumed':True,'checkpoint_edits':False,'real_ordinary_chrome':True,'recorded_fake_backend':False,'cached_body_count_at_terminated_boundary':len(cached),'cached_body_hashes_unchanged':hashes_equal,'cached_body_refetches_after_resume':refetched,'source_errors':final.get('errors'),'source_blocks':final.get('blocked'),'source_content_acquired':final.get('content_acquired'),'source_artifacts':len(final.get('artifacts',[])),'gate_request_window_count':len(raw_gate_slice.splitlines()),'gate_request_window_sha256':hashlib.sha256(raw_gate_slice).hexdigest(),'closing_checks':{k:final.get(k) for k in ['closing_inventory_equal','closing_currency_equal','closing_roots_equal']},'source_runtime_config_binding_unchanged':bindings()==before,'coverage':coverage,'image_policy_followup':'Terminal actual MIME/normalized stream audit and independent source-dimension binding required; not inferred from this controller result'};save('terminal.json',result);print(json.dumps({k:v for k,v in result.items() if k!='coverage'},indent=2),flush=True)
