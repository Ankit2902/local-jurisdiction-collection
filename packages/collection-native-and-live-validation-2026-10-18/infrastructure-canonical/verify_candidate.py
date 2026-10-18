#!/usr/bin/env python3
"""Strict read-only cached-source canonical replay; no native PDF reparse."""
import base64,contextlib,copy,hashlib,json,pathlib,socket,sys
from unittest.mock import patch
BASE=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(BASE/'candidate'))
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
from collectors.encodeplus import infrastructure_contents as m
from collectors.encodeplus.native_document import outputs
def sha(b):return hashlib.sha256(b).hexdigest()
for line in (BASE/'MANIFEST.sha256').read_text().splitlines():
 h,n=line.split('  ',1);assert sha((BASE/n).read_bytes())==h,'Sealed file changed '+n
fix=BASE/'candidate/collectors/encodeplus/fixtures/infrastructure-four-region';ir=json.loads((fix/'ir.json').read_text());by_page={d['physical_page']:d for d in ir}
assert sha((fix/'source.pdf').read_bytes())==m.SOURCE_SHA256
out=BASE/'derivative-current';rows=list(map(json.loads,(out/'records.jsonl').open()));assert len(rows)==636
report=json.loads((out/'report.json').read_text());family=BASE/'candidate/collectors/encodeplus'
assert all(sha((family/n).read_bytes())==h for n,h in report['module_sha256'].items())
originals=[];selected=[];calls=[]
def forbid(name):
 def f(*args,**kwargs):calls.append(name);raise AssertionError(name)
 return f
with contextlib.ExitStack()as stack:
 for obj,names in [(pdfplumber,['open']),(pypdfium2,['PdfDocument']),(PDFStream,['get_data']),(Image,['open']),(socket,['socket']),(base64,['b64decode'])]:
  for name in names:stack.enter_context(patch.object(obj,name,forbid(name)))
 for row in rows:
  if row.get('canonical_structure_selection',{}).get('profile')!='infrastructure_contents_or_revision_cover':originals.append(copy.deepcopy(row));continue
  old=copy.deepcopy(row)
  for k,v in row['superseded_detector_diagnostics']['original_record_fields'].items():old[k]=v
  for k in ['canonical_structure_selection','superseded_detector_diagnostics','source_infrastructure_structures']:old.pop(k)
  fresh=copy.deepcopy(old);item={'id':old['document_id'],'url':old['source_url'].split('#page=')[0],'raw_ref':old['raw_ref'],'expected_sha256':m.SOURCE_SHA256}
  assert m.attach_retained_ir(fresh,by_page[old['physical_page']],item,m.SOURCE_SHA256)and fresh==row,'Source-backed canonical replay differs'
  originals.append(old);selected.append(row)
 assert len(selected)==4 and all(not r['tables']for r in selected)
 assert sha(outputs(originals)['records.jsonl'])=='7c2c63a067fc47ceff537266a152c6cef71d0f19c51ed238b6dac33cee4ec0c3','Prior13/source632 records did not restore exactly'
 for name,content in outputs(rows).items():assert(out/name).read_bytes()==content,'Canonical consumer output differs '+name
 assert sum(bool(r.get('canonical_structure_selection'))for r in originals)==13
 assert sum(r['image_placeholder_count']for r in originals)==sum(r['image_placeholder_count']for r in rows)==201
 assert sum(not c['independent_character_agreement']for r in rows for t in r['tables']for c in t['cells'])==0
 assert sum(not c['independent_character_agreement']for r in rows for t in r.get('superseded_detector_diagnostics',{}).get('original_record_fields',{}).get('tables',[])for c in t['cells'])==795
assert not calls
print(json.dumps({'offline':True,'read_only':True,'new_native_parses':0,'records':636,'new_infrastructure_selections':4,'prior13selections_preserved_exact':True,
 'old795failed_cells_retained_diagnostic':True,'image_placeholders':201,'forbidden_calls':calls,'source_dimensions':m.summary(rows),
 'canonical_jsonl_sha256':sha((out/'records.jsonl').read_bytes()),'canonical_csv_sha256':sha((out/'records.csv').read_bytes()),
 'whole_book_semantic_or_table_completeness_qualified':False},indent=2))
