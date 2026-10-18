#!/usr/bin/env python3
"""Exact frozen collector/strict verifier with fail-closed image/network tripwires."""
import argparse,base64,contextlib,hashlib,json,pathlib,shutil,socket,subprocess,sys,traceback,datetime
p=argparse.ArgumentParser();p.add_argument('mode',choices=['replay','verify']);p.add_argument('--config',type=pathlib.Path);p.add_argument('--source',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args();sys.dont_write_bytecode=True;BASE=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(BASE));import collect,replay,verify,transport,pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
sha=lambda b:hashlib.sha256(b).hexdigest();calls=[];guards=[];old_get_data=PDFStream.get_data;started=datetime.datetime.now(datetime.timezone.utc).isoformat();result=None;status=3;error=None
expected=json.loads((BASE/'SOURCE-HASHES.json').read_text());assert all(sha((BASE/n).read_bytes())==h for n,h in expected.items())
def forbid(name):
 def fail(*args,**kwargs):calls.append(name);raise AssertionError('Forbidden image/network API: '+name)
 return fail
def stream_guard(stream):
 attrs=stream.attrs
 if getattr(attrs.get('Subtype'),'name',None)=='Image'or('W'in attrs and'H'in attrs):return forbid('PDFStream.image.get_data')()
 return old_get_data(stream)
with contextlib.ExitStack()as stack:
 stack.enter_context(__import__('unittest.mock',fromlist=['patch']).patch.object(PDFStream,'get_data',stream_guard));guards.append('PDFStream.get_data image-only; content/font text streams permitted')
 from unittest.mock import patch
 for obj,names in [(pypdfium2.PdfPage,['render']),(pypdfium2.PdfImage,['get_bitmap','extract','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open']),(socket,['socket']),(subprocess,['run','Popen']),(base64,['b64decode']),(transport,['fetch'])]:
  for name in names:
   if hasattr(obj,name):stack.enter_context(patch.object(obj,name,forbid(str(obj)+'.'+name)));guards.append(str(obj)+'.'+name)
 try:
  if a.mode=='replay':
   if a.config is None or a.source is None:raise ValueError('replay requires config/source')
   if a.out.exists():raise ValueError('Fresh guarded output required')
   c,state=replay.initialize(a.config,a.out,a.source)
   shutil.copyfile(__file__,a.out/'executed/run_guarded.py');shutil.copyfile(BASE/'SOURCE-HASHES.json',a.out/'executed/GUARDED-SOURCE-HASHES.json')
   state['guard_driver']={'sha256':sha(pathlib.Path(__file__).read_bytes()),'raw_ref':'executed/run_guarded.py','policy':'Fail-closed image/network/inline decoder APIs; no collector/verification qualification bypass'};collect.save(a.out/'checkpoint.json',state)
   status=replay.run(a.config,a.out,resume=True)
  else:
   state=collect.load(a.out/'checkpoint.json');driver=state.get('guard_driver')
   if driver and sha((a.out/driver['raw_ref']).read_bytes())!=driver['sha256']:raise ValueError('Guarded driver source changed')
   result=verify.verify(a.out);print(json.dumps({'offline':True,'read_only':True,'coverage':collect.brief(result)},indent=2));status=0 if result['requested_coverage_complete']else 3
 except BaseException as exc:
  error={'type':type(exc).__name__,'message':str(exc)[:500]};traceback.print_exc();status=3
 if calls:status=3
receipt={'schema':1,'mode':a.mode,'started_at':started,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'error':error,'guard_driver_sha256':sha(pathlib.Path(__file__).read_bytes()),'runtime_source_hashes':expected,'guards':guards,'forbidden_calls':calls,'network_requests':0if not calls else None,'image_bytes_read':0if not calls else None,'source_provenance':str(a.source)if a.source else None,'output_provenance':str(a.out),'claim':'Exact frozen standard collector/reconcile/verify functions under additional fail-closed API tripwires; no cache checks or semantic flags patched.'};a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');raise SystemExit(status)
