#!/usr/bin/env python3
"""Read-only exact explicitly selected eCode engine.verify; never acquisition/migration."""
import sys
sys.dont_write_bytecode=True
import argparse,base64,contextlib,datetime,hashlib,importlib,importlib.metadata,json,platform,socket,subprocess,types
from pathlib import Path
from unittest.mock import patch

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encode(d):return (json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
def tree(root):
 out={}
 for p in sorted(root.rglob('*')):
  if p.is_symlink():raise ValueError('Symlinks refused')
  if p.is_file():out[p.relative_to(root).as_posix()]=sha(p)
 return out
def runtime():return {'python':sys.version,'platform':platform.platform(),'python_executable':str(Path(sys.executable).resolve()),'python_executable_sha256':sha(Path(sys.executable).resolve()),'packages':dict(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions() if d.metadata.get('Name')))}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',required=True,type=Path);ap.add_argument('--collector-root',required=True,type=Path);ap.add_argument('--publication-id',required=True);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
 import re
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}',a.publication_id):raise ValueError('Unsafe publication namespace')
 root=a.input.resolve();src=a.collector_root.resolve();out=a.out.resolve();cp=json.loads((root/'checkpoint.json').read_text());expected=cp['code_fingerprint']
 if out.exists() or out.is_relative_to(root) or root.is_relative_to(out) or out.is_relative_to(src):raise ValueError('Fresh disjoint proof directory required')
 if {p.name:sha(p) for p in src.glob('*.py')}!=expected:raise ValueError('Explicit standard verifier source is not exact retained executed revision')
 if cp['config']['family']!='ecode360':raise ValueError('eCode360 only')
 out.mkdir(parents=True);before=tree(root);codes=tree(src);rt=runtime();started=datetime.datetime.now(datetime.timezone.utc).isoformat();calls=[]
 def forbidden(*args,**kwargs):calls.append('forbidden_network_process_image_decode');raise AssertionError('Offline exact verification forbids network/process/image decoding')
 try:
  from PIL import Image
  with contextlib.ExitStack() as g:
   for obj,key in [(socket,'create_connection'),(socket.socket,'connect'),(subprocess,'Popen'),(base64,'b64decode'),(Image,'open')]:g.enter_context(patch.object(obj,key,forbidden))
   name='_explicit_retained_ecode';pkg=types.ModuleType(name);pkg.__path__=[str(src)];sys.modules[name]=pkg;module=importlib.import_module(name+'.engine')
   if Path(module.__file__).resolve()!=src/'engine.py':raise ValueError('Wrong standard engine loaded')
   result=module.verify(root)
  after=tree(root);ca=tree(src);ra=runtime()
  if before!=after or codes!=ca or rt!=ra or calls:raise ValueError('Evidence/source/runtime changed or forbidden operation')
  if result.get('verified') is not True:raise ValueError('Standard raw reconstruction failed')
  report=encode(result);(out/'family-verification.json').write_bytes(report)
  proof={'schema':'offline-family-readonly-proof-1','family':'ecode','reader':'ecode-html-retained-incomplete-v1','publication_id':a.publication_id,'publication_id_origin':'Caller corpus namespace, not source completeness','selected_config':cp['config'],'evidence_read_only':True,'publisher_requests':0,'source_changed_during_run':False,'runtime_changed_during_run':False,'evidence_sha256_before':before,'evidence_sha256_after':after,'collector_sources_before':expected,'collector_sources_after':{p.name:sha(p) for p in src.glob('*.py')},'family_verification_path':'family-verification.json','verification':{'method':'Actual standard exact explicitly selected engine.verify: full raw reconstruction and every normalized output comparison','captured_runtime_root':str(src),'source_revision_selection':'Explicit retained executed-source; no current or acquisition-runtime equivalence inferred','module_file':str(Path(module.__file__).resolve()),'module_sha256':sha(src/'engine.py'),'adapter_source_sha256':sha(Path(__file__).resolve()),'family_report_sha256':hashlib.sha256(report).hexdigest(),'forbidden_calls':calls,'started_at':started,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime_before':rt,'runtime_after':ra},'scope':'Retained incomplete acquired HTML; verified=true qualifies reconstruction only. Missingclosing, required documents,403 and every original falsegate remain.'}
  (out/'read-only-proof.json').write_bytes(encode(proof));print(json.dumps({'verification_adapter_complete':True,'raw_reconstruction_verified':True,'publication_complete':result['complete'],'family_standard_CLI_expected_exit':0 if result['complete'] else 2,'input_files':len(before),'source_revision':hashlib.sha256(json.dumps(expected,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),'forbidden_calls':calls}));return 0
 except BaseException as e:
  fail={'verified':False,'error':type(e).__name__+': '+str(e),'forbidden_calls':calls,'evidence_unchanged':tree(root)==before,'collector_unchanged':tree(src)==codes};(out/'verification-failure.json').write_bytes(encode(fail));print(json.dumps(fail));return 1
if __name__=='__main__':sys.exit(main())
