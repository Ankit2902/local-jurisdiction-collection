"""One owned real native-inventory common-launcher SIGINT/resume run after explicit root freeze.
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
def tree(folder):
 return {str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
def initialization():
 path=out/'source/inventory-initialization.json'
 return load(path) if path.exists() else None
logs=[(proof/'initial.stdout.log').open('w'),(proof/'initial.stderr.log').open('w')];common=subprocess.Popen(argv,cwd=repo,stdout=logs[0],stderr=logs[1]);save('common-process-started.json',{'at':now(),'pid':common.pid,'command':argv});deadline=time.monotonic()+600;last=0;child=None
while True:
 if common.poll() is not None:raise RuntimeError('Common job terminated before native interruption boundary: '+str(common.returncode))
 init=initialization();gate_now=load(gate/'state.json') if (gate/'state.json').exists() else {}
 if gate_now.get('stop') or init and init.get('error'):
  common.wait();save('blocked-before-interruption.json',{'at':now(),'common_exit':common.returncode,'initialization':init,'gate':gate_now});raise RuntimeError('Actual source access/error evidence retained; no resume')
 if source_state() is not None:raise RuntimeError('Initial native boundary missed; no intentional late signal or blind restart')
 attempt=next((v for v in (init or {}).get('attempts',[]) if v.get('status')=='running'),None)
 generation=out/'source'/attempt['path'] if attempt else None
 native=list(generation.glob('network-*.bin')) if generation and generation.exists() else []
 if init and init.get('stage')=='native_inventory' and native:
  child,proc=family_child(common.pid)
  if child:
   if (out/'source/checkpoint.json').exists():raise RuntimeError('Source checkpoint appeared before signal; required boundary missed')
   observed={'at':now(),'common_pid':common.pid,'family_pid':child,'process_tree':{str(k):v for k,v in proc.items() if descendant(k,common.pid,proc)},'initialization_sha256':sha(out/'source/inventory-initialization.json'),'initialization':init,'native_generation':str(generation.relative_to(out)),'observed_native_raw_files':{str(p.relative_to(generation)):sha(p) for p in native},'generation_before_signal':tree(generation),'source_checkpoint_exists':False,'operative_body_count':0,'checkpoint_edits':False,'recorded_backend':False};save('observed-before-sigint.json',observed);os.kill(child,signal.SIGINT);break
 if time.monotonic()-last>=30:print(json.dumps({'at':now(),'stage':'awaiting_first_actual_native_response_before_source_checkpoint','initialization_stage':(init or {}).get('stage'),'native_responses':len(native)}),flush=True);last=time.monotonic()
 if time.monotonic()>deadline:raise RuntimeError('Native boundary not observed; preserve actual job, no blind restart')
 time.sleep(.05)
initial_exit=common.wait(timeout=120)
for stream in logs:stream.close()
init=initialization();proc_after=processes();owned=observed['process_tree'];browser_survivors={pid:proc_after[int(pid)] for pid,v in owned.items() if int(pid) in proc_after and proc_after[int(pid)]['command']==v['command'] and any(x in v['command'] for x in ['Google Chrome','chrome_crashpad','playwright/driver','node'])}
if browser_survivors:
 time.sleep(3);proc_after=processes();browser_survivors={pid:proc_after[int(pid)] for pid,v in owned.items() if int(pid) in proc_after and proc_after[int(pid)]['command']==v['command'] and any(x in v['command'] for x in ['Google Chrome','chrome_crashpad','playwright/driver','node'])}
generation=out/observed['native_generation'];terminated_generation=tree(generation);meta=load(generation/'receipt.json') if (generation/'receipt.json').exists() else None
save('initial-terminal.json',{'at':now(),'common_exit':initial_exit,'initialization':init,'initialization_sha256':sha(out/'source/inventory-initialization.json'),'native_generation':observed['native_generation'],'generation_after_shutdown':terminated_generation,'native_receipt':meta,'source_checkpoint_exists':(out/'source/checkpoint.json').exists(),'owned_browser_survivors':browser_survivors,'checkpoint_edits':False})
if browser_survivors:raise RuntimeError('Own browser descendants still active; resolve owned contexts only, do not restart')
if (out/'source/checkpoint.json').exists() or init.get('error') or load(gate/'state.json').get('stop'):raise RuntimeError('Required native boundary/access qualification failed; no automatic resume')
# Same production guard used by initialization: inspect durable response ledgers
# before trusting even a missing final receipt. This performs no gate writes or requests.
import sys
sys.path.insert(0,str(repo/'collectors/originals'))
from flagstaff_initialization import checked_receipt
checked_receipt(generation)
for name,digest in observed['observed_native_raw_files'].items():
 if sha(generation/name)!=digest:raise RuntimeError('Observed native raw bytes changed during shutdown')
if not meta or meta.get('blocked') or meta.get('error') or meta.get('whole_publication_selected_values'):raise RuntimeError('Native partial/error/full-scope boundary does not qualify safe intended restart')
resume_offset=requestlog.stat().st_size;save('resume-started.json',{'at':now(),'same_command':argv,'native_partial_generation':observed['native_generation'],'generation_sha256':terminated_generation,'gate_request_log_resume_offset':resume_offset,'source_bindings':bindings(),'checkpoint_edits':False,'scope':'Incomplete native controls require a new ordinary source inventory generation. Native re-requests expected; no operative bodies cached yet.'})
if bindings()!=before:raise RuntimeError('Frozen source/runtime changed; no automatic code migration')
logs=[(proof/'resume.stdout.log').open('w'),(proof/'resume.stderr.log').open('w')];resumed=subprocess.Popen(argv,cwd=repo,stdout=logs[0],stderr=logs[1]);last=0;observed_resume=False
while resumed.poll() is None:
 current_init=initialization()
 if current_init and not observed_resume and any(v.get('status')=='interrupted_preserved' for v in current_init.get('attempts',[])) and len(current_init.get('attempts',[]))>=2:
  save('resumed-initialization-observed.json',{'at':now(),'initialization':current_init,'original_generation_unchanged':tree(generation)==terminated_generation,'old_generation_sha256':terminated_generation,'actual_ordinary_browser_backend':True});observed_resume=True
 if time.monotonic()-last>=30:
  s=source_state();print(json.dumps({'at':now(),'stage':'live_native_resume_running','initialization_stage':(current_init or {}).get('stage'),'native_generations':len((current_init or {}).get('attempts',[])),'bodies':sum(x.get('role')=='content' for x in s.get('artifacts',[])) if s else 0,'artifacts':len(s.get('artifacts',[])) if s else 0}),flush=True);last=time.monotonic()
 time.sleep(.5)
for stream in logs:stream.close()
final=source_state();finalinit=initialization()
with requestlog.open('rb') as stream:stream.seek(start_offset);raw_gate_slice=stream.read()
(proof/'gate-request-window.jsonl').write_bytes(raw_gate_slice)
coverage=load(out/'coverage.json') if (out/'coverage.json').exists() else None
result={'schema':'originals-real-native-inventory-browser-recovery-1','at':now(),'initial_common_exit':initial_exit,'resumed_common_exit':resumed.returncode,'intentional_sigint_family_pid':child,'same_command_resumed':True,'checkpoint_edits':False,'real_ordinary_chrome':True,'recorded_fake_backend':False,'initial_native_raw_response_count':len(observed['observed_native_raw_files']),'operative_bodies_at_interruption':0,'source_checkpoint_absent_at_interruption':True,'partial_native_generation_unchanged':tree(generation)==terminated_generation,'partial_native_generation':observed['native_generation'],'initialization':finalinit,'source_errors':final.get('errors') if final else None,'source_blocks':final.get('blocked') if final else None,'source_content_acquired':final.get('content_acquired') if final else None,'source_artifacts':len(final.get('artifacts',[])) if final else 0,'gate_request_window_count':len(raw_gate_slice.splitlines()),'gate_request_window_sha256':hashlib.sha256(raw_gate_slice).hexdigest(),'closing_checks':{k:final.get(k) for k in ['closing_inventory_equal','closing_currency_equal','closing_roots_equal']} if final else None,'source_runtime_config_binding_unchanged':bindings()==before,'coverage':coverage,'image_policy_followup':'Terminal actual MIME/browser-response/normalized stream audit must include BOTH partial and selected native generations. No separate image extraction/decode/render/OCR.','native_refetch_scope':'New native inventory after interrupted controls is expected. No cached-operative-body no-refetch claim applies at this boundary.'};save('terminal.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['coverage','initialization']},indent=2),flush=True)
