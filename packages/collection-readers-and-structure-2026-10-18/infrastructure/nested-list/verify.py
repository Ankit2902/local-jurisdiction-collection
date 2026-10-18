#!/usr/bin/env python3
"""Portable read-only finite proof/exports replay. No PDF/image/network access."""
import contextlib,csv,hashlib,io,json,pathlib,socket,sys
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'candidate'));sys.dont_write_bytecode=True

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def main():
 manifest=json.loads((ROOT/'MANIFEST.json').read_text())
 for name,h in manifest['files'].items():assert sha(ROOT/name)==h,('Manifest drift',name)
 from collectors.encodeplus import infrastructure_nested_list as m,native_document as native
 import pypdf,pdfplumber,pypdfium2
 calls=[]
 def deny(name):
  def stop(*a,**k):calls.append(name);raise AssertionError('Forbidden '+name)
  return stop
 with contextlib.ExitStack() as stack:
  for obj,name in [(socket,'socket'),(pypdf,'PdfReader'),(pdfplumber,'open'),(pypdfium2,'PdfDocument')]:stack.enter_context(patch.object(obj,name,deny(name)))
  base=rows(ROOT/'source/baseline172.jsonl');w=json.loads((ROOT/'source/native-page26-glyph-witness.json').read_text());actual=rows(ROOT/'actual-default172/records.jsonl');expected=[m.project(r,w) for r in base];expected[54]['source_nested_list_native_witness']=w
  assert expected==actual
  mixedbase=rows(ROOT/'source/baseline828.jsonl');mixed=[expected[54] if r['id']==m.ID else r for r in mixedbase]
  assert mixed==rows(ROOT/'mixed828/records.jsonl')
  for name,data in native.outputs(actual).items():assert (ROOT/'actual-default172'/name).read_bytes()==data,('Default exports',name)
  for name,data in native.outputs(mixed).items():assert (ROOT/'mixed828'/name).read_bytes()==data,('Mixed exports',name)
  # Literal source markers and legal words agree across canonical structure/HTML/CSV.
  for dirname,data in [('actual-default172',actual),('mixed828',mixed)]:
   csvrows=list(csv.DictReader(io.StringIO((ROOT/dirname/'records.csv').read_text())))
   assert len(csvrows)==len(data)
   for r,c in zip(data,csvrows):assert r['id']==c['id'] and r['text']==c['text'] and r.get('html','')==c['html']
  assert sum(a!=b for a,b in zip(base,actual))==1 and sum(a!=b for a,b in zip(mixedbase,mixed))==1
  assert sum(r['text'].count('[IMAGE]') for r in mixed)==201
  assert actual[0]['source_document_evidence']['nested_list_hierarchy_qualified'] is False
  assert actual[54]['qualification']['nested_list_hierarchy_qualified'] is True
  assert actual[54]['qualification']['whole_publication_complete'] is False
 for name,h in manifest['files'].items():assert sha(ROOT/name)==h,('Readonly drift',name)
 assert not calls
 print(json.dumps({'status':'PASS','manifest_files':len(manifest['files']),'records':172,'unchanged':171,'mixed_records':828,'mixed_unchanged':827,'selected_list_outer':2,'selected_list_children':4,'source_glyphs':516,'source_words':105,'image_placeholders':201,'forbidden_calls':calls,'native_parse':False}))
if __name__=='__main__':main()
