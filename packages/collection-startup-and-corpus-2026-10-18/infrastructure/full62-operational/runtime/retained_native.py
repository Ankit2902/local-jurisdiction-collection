#!/usr/bin/env python3
"""Supply only exact retained native witnesses to the unchanged native collector."""
import argparse,contextlib,datetime,hashlib,json,pathlib,shutil,sys,traceback
SHA='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c'
URL='https://online.encodeplus.com/regs/overlandpark-ks/doclibrary.aspx?id=3e3d98cc-890e-4630-9c2b-8f84375b0c67'
def digest(data):return hashlib.sha256(data).hexdigest()
def read(p):return json.loads(p.read_text())
def inspect_source(source,cfg):
 state=read(source/'checkpoint.json')
 if state.get('phase')!='finished':raise ValueError('Retained source acquisition is not terminal')
 if cfg!=state['config'] or cfg['expected_sha256']!=SHA or cfg['url']!=URL or cfg['expected_pages']!=62:raise ValueError('Exact retained Infrastructure config required')
 result={}
 for key in ('start','end'):
  e=state[key];rel=e['path'];raw=source/rel;receipt=raw.with_name(raw.name+'.receipt.json');m=read(receipt);b=raw.read_bytes()
  if rel!='raw/'+key+'.pdf' or e['url']!=URL or m['url']!=URL or m.get('http_status')!=200 or m.get('challenge') or digest(b)!=SHA or e['sha256']!=SHA or m['sha256']!=SHA:raise ValueError('Wrong retained native witness: '+key)
  result[rel]={'sha256':SHA,'receipt_sha256':digest(receipt.read_bytes()),'bytes':len(b),'receipt':m}
 return result
class RetainedTransport:
 def __init__(self,source,cfg):self.source=source;self.cfg=cfg;self.witness=inspect_source(source,cfg);self.calls=[]
 def __call__(self,out,url,rel,timeout=120):
  if url!=URL or rel not in self.witness:raise ValueError('No retained transport witness for requested URL/path')
  raw=self.source/rel;meta_path=raw.with_name(raw.name+'.receipt.json');w=self.witness[rel]
  if digest(raw.read_bytes())!=w['sha256'] or digest(meta_path.read_bytes())!=w['receipt_sha256']:raise ValueError('Retained witness changed after preflight')
  target=pathlib.Path(out)/rel;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists() or target.with_name(target.name+'.receipt.json').exists():raise ValueError('Refuse overwriting retained transport output')
  shutil.copyfile(raw,target);shutil.copyfile(meta_path,target.with_name(target.name+'.receipt.json'));self.calls.append({'url':url,'raw_ref':rel,'sha256':w['sha256'],'acquisition':'retained witness copy; no current HTTP request'})
  return target.read_bytes(),dict(w['receipt'],_retained_path=rel)
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','replay','verify']);p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--config',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path);p.add_argument('--runtime-tree',type=pathlib.Path);p.add_argument('--runtime-manifest',type=pathlib.Path);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args();cfg=read(a.config);started=datetime.datetime.now(datetime.timezone.utc).isoformat();witness=inspect_source(a.source,cfg)
 if a.mode=='preflight':a.receipt.write_text(json.dumps({'mode':'preflight','source_checkpoint_sha256':digest((a.source/'checkpoint.json').read_bytes()),'config_sha256':digest(a.config.read_bytes()),'witnesses':witness,'native_pdf_parse_performed':False,'current_requests':0},indent=2)+'\n');return 0
 if not a.out or not a.runtime_tree or not a.runtime_manifest:p.error('replay/verify require out/runtime-tree/runtime-manifest')
 manifest=read(a.runtime_manifest)
 def bound():
  for name,h in manifest.items():
   if digest((a.runtime_tree/name).read_bytes())!=h:raise ValueError('Frozen runtime changed: '+name)
 bound();a.receipt.with_name(a.receipt.stem+'.origin.json').write_text(json.dumps({'started_at':started,'driver_sha256':digest(pathlib.Path(__file__).read_bytes()),'runtime_source_hashes':manifest,'source_checkpoint_sha256':digest((a.source/'checkpoint.json').read_bytes()),'config_sha256':digest(a.config.read_bytes()),'witnesses':witness,'acquisition_mode':'retained-original; zero current requests'},indent=2)+'\n');sys.path.insert(0,str(a.runtime_tree));sys.dont_write_bytecode=True
 from collectors.encodeplus import native_document as native
 # Populate genuine stdlib platform metadata cache before subprocess tripwires. No parser/native file access.
 native.runtime_info()
 import base64,socket,subprocess,pdfplumber,pypdfium2
 from pdfminer.pdftypes import PDFStream
 from PIL import Image
 from unittest.mock import patch
 calls=[];guards=[];status=3;error=None;report=None;adapter=RetainedTransport(a.source,cfg);original=PDFStream.get_data
 def forbid(name):
  def stop(*args,**kwargs):calls.append(name);raise AssertionError('Forbidden image/network/decoder API: '+name)
  return stop
 def stream_guard(stream):
  attrs=stream.attrs
  if getattr(attrs.get('Subtype'),'name',None)=='Image' or ('W' in attrs and 'H' in attrs):return forbid('PDFStream.image.get_data')()
  return original(stream)
 with contextlib.ExitStack()as stack:
  stack.enter_context(patch.object(PDFStream,'get_data',stream_guard));guards.append('PDFStream image data only; text/font streams allowed')
  for obj,names in [(pypdfium2.PdfPage,['render']),(pypdfium2.PdfImage,['get_bitmap','extract','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open']),(socket,['socket']),(subprocess,['run','Popen']),(base64,['b64decode'])]:
   for name in names:
    if hasattr(obj,name):stack.enter_context(patch.object(obj,name,forbid(str(obj)+'.'+name)));guards.append(str(obj)+'.'+name)
  try:
   if a.mode=='replay':
    if a.out.exists():raise ValueError('Fresh output required')
    stack.enter_context(patch.object(native,'cached',adapter));report=native.collect(cfg,a.out)
   else:report=native.verify(a.out)
   bound();status=0 if report.get('native_document_complete') else 2
  except BaseException as exc:error={'type':type(exc).__name__,'message':str(exc)};traceback.print_exc()
  if calls:status=3
 receipt={'schema_version':1,'mode':a.mode,'started_at':started,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':status,'error':error,'driver_sha256':digest(pathlib.Path(__file__).read_bytes()),'source_checkpoint_sha256':digest((a.source/'checkpoint.json').read_bytes()),'config_sha256':digest(a.config.read_bytes()),'runtime_source_hashes':manifest,'witnesses':witness,'retained_transport_calls':adapter.calls,'forbidden_calls':calls,'current_network_requests':0 if not calls else None,'image_api_accesses':0 if not calls else None,'guards':guards,'coverage':report,'claim':'Unchanged standard native collector/parser/strict verifier with retained start/end transport substitution only; original receipt timestamps preserved. No fresh live/currentness claim.'}
 a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'exit_code':status,'native_document_complete':report.get('native_document_complete') if report else None,'forbidden_calls':calls},indent=2));return status
if __name__=='__main__':raise SystemExit(main())
