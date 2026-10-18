#!/usr/bin/env python3
"""Portable offline verification adapter for source-owned HTML corpus readers.

Select the exact collector source tree explicitly. This runs its standard verify()
under socket/image guards; it never collects, upgrades, adopts, or modifies input.
A historical source tree remains labelled historical/explicit, never current by
inference. Use the interpreter/dependencies appropriate for that source revision.
"""
import sys
sys.dont_write_bytecode=True
import argparse,contextlib,datetime,hashlib,importlib,importlib.metadata,json,platform,socket,types,re
from pathlib import Path
from unittest.mock import patch,PropertyMock

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def tree(root):
 result={}
 for p in sorted(root.rglob('*')):
  if p.is_symlink():raise ValueError('Symlink evidence/source refused: '+str(p))
  if p.is_file():result[p.relative_to(root).as_posix()]=sha(p)
 return result
def runtime():
 return {'python_executable':str(Path(sys.executable).resolve()),'python_executable_sha256':sha(Path(sys.executable).resolve()),'python_version':sys.version,'implementation':platform.python_implementation(),'packages':dict(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions() if d.metadata.get('Name')))}
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--reader',required=True,choices=['municode-html-publication-v1','encodeplus-html-publication-v1','american-legal-native-html-publication-v1']);ap.add_argument('--input',required=True,type=Path);ap.add_argument('--collector-root',required=True,type=Path);ap.add_argument('--publication-id',required=True);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args(argv)
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}',a.publication_id):raise ValueError('publication-id must be a safe caller-assigned stable slug (1-128 ASCII letters/digits/_/-)')
 root=a.input.resolve();chosen=a.collector_root.resolve();out=a.out.resolve();mode={'municode-html-publication-v1':'municode','encodeplus-html-publication-v1':'encodeplus','american-legal-native-html-publication-v1':'american-legal'}[a.reader];familyroot=chosen/'collectors'/mode if (chosen/'collectors'/mode/'verify.py').is_file() else chosen
 if not (familyroot/'verify.py').is_file():raise ValueError('collector-root must contain verify.py or collectors/'+mode+'/verify.py')
 if not root.is_dir() or out.exists() or out.is_relative_to(root) or root.is_relative_to(out) or out.is_relative_to(familyroot) or familyroot.is_relative_to(out):raise ValueError('Fresh disjoint verification output and existing source/input required')
 cp=load(root/'checkpoint.json')
 if mode=='municode':
  if cp.get('schema_version')!=1 or cp.get('phase')!='finished' or len(cp.get('publications',{}))!=1:raise ValueError('One finished Municode HTML publication required')
  cfg=cp['binding'];prefix=''
 elif mode=='american-legal':
  run=load(root/'run.json');identity=run['identity'];prefix=''
  if run.get('status')!='acquired' or run.get('strategy')!='native' or run.get('max_items') is not None or identity.get('is_pdf') is not False:raise ValueError('Terminal whole native AL HTML required; PDF/page/limited modes refuse')
  cfg={'source_url':run['source_url'],'publication_selector':run['publication_selector']}
 else:
  cfg=cp['config'];prefix='collectors/encodeplus/'
  if cp.get('phase')!='finished' or cfg.get('mode') or '/regs/' not in cfg.get('base',''):raise ValueError('Finished source-owned enCodePlus HTML required; native/page modes refuse')
 out.mkdir(parents=True);before=tree(root);codes=tree(familyroot);rt=runtime();adapter_hash=sha(Path(__file__).resolve());start=datetime.datetime.now(datetime.timezone.utc).isoformat();calls=[]
 def no(*args,**kwargs):calls.append('forbidden_network_or_image');raise AssertionError('Offline corpus verification forbids network/image operations')
 try:
  # Guard modules are loaded before any selected collector import. Missing guard
  # dependencies fail closed rather than silently omitting a known image API.
  import pdfplumber,pypdfium2
  from PIL import Image
  from pypdf._page import PageObject
  with contextlib.ExitStack() as guard:
   for obj,names in [(socket,['create_connection']),(socket.socket,['connect']),(Image,['open']),(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image'])]:
    for name in names:
     if hasattr(obj,name):guard.enter_context(patch.object(obj,name,no))
   guard.enter_context(patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=no))
   if mode=='american-legal':
    import fitz
    from pdfminer.pdftypes import PDFStream,resolve1
    stream_data=PDFStream.get_data
    def guarded_stream(stream):
     if str(resolve1(stream.attrs.get('Subtype'))) in ["/'Image'",'Image','/Image']:return no()
     return stream_data(stream)
    guard.enter_context(patch.object(PDFStream,'get_data',guarded_stream))
    for obj,names in [(fitz.Document,['extract_image']),(fitz.Page,['get_pixmap','get_svg_image'])]:
     for name in names:
      if hasattr(obj,name):guard.enter_context(patch.object(obj,name,no))
   if mode in ['municode','american-legal']:
    sys.path.insert(0,str(familyroot));module=importlib.import_module('verify')
   else:
    name='_corpus_explicit_encodeplus';pkg=types.ModuleType(name);pkg.__path__=[str(familyroot)];sys.modules[name]=pkg;module=importlib.import_module(name+'.verify')
   if Path(module.__file__).resolve()!=familyroot/'verify.py':raise ValueError('Wrong standard verifier imported')
   result=module.verify(root)
  after=tree(root);ca=tree(familyroot);ra=runtime()
  if before!=after or codes!=ca or rt!=ra or sha(Path(__file__).resolve())!=adapter_hash or calls:raise ValueError('Input/source/runtime changed or forbidden operation attempted')
  # Preserve actual report, including false/missing coverage dimensions. The
  # reader independently checks family-specific reconstruction success and IR.
  report=encode(result);(out/'family-verification.json').write_bytes(report)
  proof={'schema':'offline-family-readonly-proof-1','family':mode,'reader':a.reader,'publication_id':a.publication_id,'publication_id_origin':'Caller-assigned corpus namespace; source product/client/job/config independently bound below','registry_mapping_verified':False,'family_verification_path':'family-verification.json','selected_config':cfg,'evidence_read_only':True,'publisher_requests':0,'source_changed_during_run':False,'runtime_changed_during_run':False,'evidence_sha256_before':before,'evidence_sha256_after':after,'collector_sources_before':{prefix+k:v for k,v in codes.items()},'collector_sources_after':{prefix+k:v for k,v in ca.items()},'verification':{'method':'Actual standard explicitly selected family verify() raw reconstruction/output comparison; no acquisition or upgrade','captured_runtime_root':str(familyroot),'adapter_source_sha256':adapter_hash,'adapter_source_name':Path(__file__).name,'source_revision_selection':'Explicit caller source tree; no current/acquisition-runtime equivalence inferred','started_at':start,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'module_file':str(Path(module.__file__).resolve()),'module_sha256':sha(Path(module.__file__).resolve()),'forbidden_calls':calls,'family_report_sha256':hashlib.sha256(report).hexdigest(),'runtime_before':rt,'runtime_after':ra},'scope':'Read-only validation of one existing HTML publication under explicitly selected collector code and this recorded Python environment. All original source/config/version/coverage limitations remain; no native segmentation, current legal edition, or jurisdiction closure added.'}
  (out/'read-only-proof.json').write_bytes(encode(proof));print(json.dumps({'verification_adapter_complete':True,'family_report_status':result.get('status',result.get('passed')),'publication_acceptance_added':False,'family':mode,'publication_id':a.publication_id,'input_files':len(before),'collector_files':len(codes),'forbidden_calls':calls}));return 0
 except BaseException as e:
  failure={'verified':False,'error':type(e).__name__+': '+str(e),'forbidden_calls':calls,'evidence_unchanged':tree(root)==before,'collector_sources_unchanged':tree(familyroot)==codes,'runtime_unchanged':runtime()==rt}
  (out/'verification-failure.json').write_bytes(encode(failure));print(json.dumps(failure));return 1
if __name__=='__main__':sys.exit(main())
