"""Metadata/byte-hash peer review only. Never invokes a verifier or image API."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,shutil
from pathlib import Path,PurePosixPath

HERE=Path(__file__).resolve().parent
ACTUAL=HERE.parent/'flagstaff-proof-helper-actual-v1'

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(path):return json.loads(path.read_text())
def safe(root,name):
 assert isinstance(name,str) and name and '\\' not in name
 p=PurePosixPath(name);assert not p.is_absolute() and p.as_posix()==name and all(x not in ('','..','.') for x in name.split('/'))
 q=root
 for x in p.parts:q=q/x;assert not q.is_symlink()
 assert q.is_file() and q.resolve().is_relative_to(root)
 return q

def main():
 selected=[p for p in sorted(ACTUAL.rglob('*')) if p.is_file()]
 actual_before={p.relative_to(ACTUAL).as_posix():sha(p) for p in selected}
 original=ACTUAL/'proof/common-readonly.json';derivative=ACTUAL/'proof/read-only-proof.json';family=ACTUAL/'proof/family-verification.json'
 r=load(original);d=load(derivative);f=load(family);t=load(ACTUAL/'proof/terminal.json');inv=load(ACTUAL/'proof/invocation.json')
 root=Path(inv['collector_root']);runtime=Path(inv['runtime']);source=Path(inv['input'])
 assert json.loads((ACTUAL/'cli.stdout').read_text())==t
 assert (ACTUAL/'cli.stderr').read_bytes()==b'' and (ACTUAL/'proof/common.stderr').read_bytes()==b''
 assert t['common_exit']==0 and t['verification_adapter_complete'] is True and t['publication_acceptance_added'] is False
 assert r['status']=='verified_publication' and r['verification_exit']==0 and r['family_verifier_passed'] is True
 assert r['publication_id']=='original-flagstaff-az-primary'
 assert r['output']==str(source) and r['selected_config']==load(source/'checkpoint.json')['config']
 assert r['evidence_read_only'] is True and r['publisher_requests']==0 and r['source_changed_during_run'] is False and r['runtime_changed_during_run'] is False
 assert r['evidence_sha256_before']==r['evidence_sha256_after'] and len(r['evidence_sha256_before'])==558
 # Hash bytes only; do not parse source HTML, native inventory, images or PDF/DOCX.
 evidence={p.relative_to(source).as_posix():sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
 assert evidence==r['evidence_sha256_before']
 srcs=r['collector_sources_before'];assert srcs==r['collector_sources_after'] and len(srcs)==61
 for name,expected in srcs.items():assert sha(safe(root,name))==expected
 # Execute only the reviewed code_binding function AST with local hash dependency;
 # no launcher/family imports, runtime checks, subprocesses or native parsing.
 launcher=root/'collectors/ops/launcher.py';tree=ast.parse(launcher.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='code_binding')
 ns={'ROOT':root,'HERE':launcher.parent,'FAMILIES':(),'sha':sha};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(launcher),'exec'),ns)
 assert ns['code_binding']('originals')==srcs
 rt=Path(r['runtime_receipt_path']);assert rt==runtime/'runtime.json' and sha(rt)==r['runtime_receipt_sha256']==t['runtime_receipt_sha256']
 log=Path(r['log']);assert log.is_absolute() and log.is_relative_to(runtime/'verifications')
 log=safe(runtime,log.relative_to(runtime).as_posix());saved=safe(runtime,log.with_suffix('.json').relative_to(runtime).as_posix())
 assert load(saved)==r and log.read_bytes()==family.read_bytes()
 py=runtime/'venv/bin/python'
 expected=[str(py),'-B',str(root/'collectors/registry/collect.py'),'verify','--target','original-flagstaff-az','--publication','original-flagstaff-az-primary','--out',str(source),'--python',str(py)]
 assert r['verification_argv']==expected
 assert inv['argv']==[str(py),'-B',str(root/'collect.py'),'--runtime',str(runtime),'verify','--target','original-flagstaff-az','--publication','original-flagstaff-az-primary','--out',str(source)]
 original_keys=set(r);added=set(d)-original_keys
 assert added=={'family_verification_path','family_verification_sha256','proof_origin'}
 assert {k:d[k] for k in original_keys}==r
 assert d['family_verification_path']=='family-verification.json' and d['family_verification_sha256']==sha(family)
 origin=d['proof_origin'];assert origin=={'original_common_receipt_path':'common-readonly.json','original_common_receipt_sha256':sha(original),'derivative_changes':['relative family report path','family report SHA256','this lineage object'],'original_common_receipt_unchanged':True}
 assert f['full_raw_replay_equal'] is True and f['input_files_modified'] is False and f['source_route_ledger_verified'] is True and f['opening_body_closing_chronology_verified'] is True
 assert f['publication_config']==r['selected_config'] and f['complete'] is True and f['publication_accepted'] is True
 acceptance=r['acceptance'];assert acceptance==d['acceptance'] and acceptance['publication_accepted'] is True and acceptance['jurisdiction_complete'] is False
 assert acceptance['native_capture_verified'] is False and acceptance['edition_complete'] is None
 prior=source.parent/'terminal-proof/current-family-readonly.log';assert prior.read_bytes()==family.read_bytes()
 assert sha(family)=='53818c2ea07a257cba24b8c86f0cc12b31b4d4af367aba488c9f2696c1faed74'
 helper=root/'collectors/corpus_package/verify_flagstaff_input.py'
 candidate=HERE.parent/'flagstaff-proof-helper-v1/candidate/verify_flagstaff_input.py'
 assert sha(helper)==sha(candidate)==t['helper_sha256']==inv['helper_sha256']=='c94751ea78c2fea768195cec45b73d0936d2f5a96f56ef0c205134eed175fb40'
 events=[]
 for p in sorted((ACTUAL/'guard-events').glob('*.jsonl')):
  for line in p.read_text().split('\n'):
   if line:events.append(json.loads(line))
 assert len(events)==13 and len({e['pid'] for e in events})==13 and all(e['kind']=='guard_loaded' for e in events)
 assert any(e['argv']==r['verification_argv'][2:] for e in events)
 assert any(e['argv']==['collectors/originals/cli.py','verify','--config','collectors/originals/configs/flagstaff.json','--out',str(source)] for e in events)
 assert any(e['argv']==inv['argv'][2:] for e in events)
 guard=ACTUAL/'guard/sitecustomize.py';text=guard.read_text()
 for marker in ['socket.socket.connect=','socket.socket.connect_ex=','socket.create_connection=','from PIL import Image',"['open','frombytes','frombuffer']",'fitz.Page.get_pixmap=','fitz.Document.extract_image=','pdfplumber.page.Page.to_image=','pypdfium2.PdfPage.render=']:assert marker in text
 assert "event('forbidden_call',name)" in text and "raise RuntimeError('QA_FORBIDDEN:'+name)" in text
 assert actual_before=={p.relative_to(ACTUAL).as_posix():sha(p) for p in selected}
 assert evidence=={p.relative_to(source).as_posix():sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
 assert ns['code_binding']('originals')==srcs and sha(rt)==r['runtime_receipt_sha256']
 for name in ['proof/common-readonly.json','proof/read-only-proof.json','proof/family-verification.json','proof/invocation.json','proof/terminal.json','cli.stdout','cli.stderr','guard/sitecustomize.py']:
  dest=HERE/'captured'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ACTUAL/name,dest)
 report={'schema':'independent-actual-flagstaff-helper-proof-review-1','passed':True,'actual_verifier_rerun':False,'production_or_actual_folder_modified':False,'original_common_receipt':{'sha256':sha(original),'saved_runtime_receipt_sha256':sha(saved),'saved_receipt_semantic_equal':True,'status':r['status'],'verification_exit':r['verification_exit']},'family_report':{'sha256':sha(family),'exact_runtime_log_bytes':True,'exact_prior_actual_family_report_bytes':True,'publication_config_equal':True,'full_raw_replay_equal':True},'derivative':{'sha256':sha(derivative),'exact_original_fields_preserved':True,'added_fields':sorted(added),'lineage_hash_valid':True,'safe_relative_family_report':'family-verification.json'},'before_after_independent_rehash':{'evidence_files':len(evidence),'evidence_equal':True,'source_files':len(srcs),'exact_current_binding_equal':True,'runtime_receipt_equal':True},'helper_sha256':sha(helper),'guard':{'source_sha256':sha(guard),'loaded_events':13,'distinct_python_processes':13,'forbidden_events':0,'events':events,'scope':'Named socket/image API tripwires installed in logged Python processes; not a universal claim about all possible native/Node APIs.'},'acceptance_unchanged':acceptance,'source_mode':f.get('acquisition_mode'),'all_actual_file_hashes_before_after_equal':True,'actual_file_sha256':actual_before,'publisher_requests':0,'peer_image_download_decode_render_extract_ocr_operations':0,'limits':['No full common/family/source/native parser executed by peer. Independent input checks are byte hashing only.','Exact actual read-only proof validates this existing acquired Flagstaff publication; no fresh acquisition, scope, native, edition or whole-jurisdiction claim is added.','Candidate-root unmanifested guard mentioned by root is not treated as part of prior frozen helper manifest; this review binds the separate actual/guard/sitecustomize.py bytes actually supplied.']}
 (HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n')
 manifest={p.relative_to(HERE).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
 (HERE/'MANIFEST.json').write_text(json.dumps({'files':manifest},indent=2)+'\n')
 print(json.dumps({'passed':True,'review_sha256':sha(HERE/'review.json'),'manifest_sha256':sha(HERE/'MANIFEST.json'),'files':len(manifest)}))
if __name__=='__main__':main()
