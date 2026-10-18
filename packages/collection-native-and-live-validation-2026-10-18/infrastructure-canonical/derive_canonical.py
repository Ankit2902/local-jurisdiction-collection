#!/usr/bin/env python3
"""Four actual source pages +636 retained-record composition, no fullbook parse."""
import argparse,copy,contextlib,csv,hashlib,io,json,pathlib,socket,sys,base64
from unittest.mock import patch
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
BASE=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(BASE/'candidate'))
from collectors.encodeplus import infrastructure_contents as scoped
from collectors.encodeplus.native_document import outputs
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert not a.out.exists();a.out.mkdir()
 assert sha(a.baseline.read_bytes())=='7c2c63a067fc47ceff537266a152c6cef71d0f19c51ed238b6dac33cee4ec0c3'
 family=BASE/'candidate/collectors/encodeplus';fix=family/'fixtures/infrastructure-four-region';ir=json.loads((fix/'ir.json').read_text());data=(fix/'source.pdf').read_bytes();assert sha(data)==scoped.SOURCE_SHA256
 originals=list(map(json.loads,a.baseline.open()));assert len(originals)==636
 by_page={d['physical_page']:d for d in ir};selected=[];native_results=[];calls=[];stream_get=PDFStream.get_data
 def forbid(n):
  def fail(*args,**kwargs):calls.append(n);raise AssertionError('Forbidden API '+n)
  return fail
 def stream_guard(stream):
  attrs=stream.attrs
  if getattr(attrs.get('Subtype'),'name',None)=='Image'or('W'in attrs and'H'in attrs):return forbid('image_stream_decode')()
  return stream_get(stream)
 with contextlib.ExitStack()as guard:
  guard.enter_context(patch.object(PDFStream,'get_data',stream_guard))
  for obj,names in [(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['get_bitmap','get_data','extract']),
                    (pdfplumber.page.Page,['to_image']),(Image,['open']),(socket,['socket']),(base64,['b64decode'])]:
   for name in names:
    if hasattr(obj,name):guard.enter_context(patch.object(obj,name,forbid(name)))
  with pdfplumber.open(io.BytesIO(data))as pdf,pypdfium2.PdfDocument(data)as native:
   assert len(pdf.pages)==len(native)==62
   for old in originals:
    if old['raw_sha256']!=scoped.SOURCE_SHA256 or old['physical_page']not in by_page:continue
    row=copy.deepcopy(old);n=old['physical_page'];page=native[n-1];tp=page.get_textpage();item={'id':old['document_id'],'url':old['source_url'].split('#page=')[0],'raw_ref':old['raw_ref'],'expected_sha256':scoped.SOURCE_SHA256}
    try:assert scoped.attach_record(row,pdf.pages[n-1],tp,item,scoped.SOURCE_SHA256)
    finally:tp.close();page.close()
    native_results.append(row);selected.append(n)
  derived=[]
  for old in originals:
   row=copy.deepcopy(old)
   if old['raw_sha256']==scoped.SOURCE_SHA256 and old['physical_page']in by_page:
    item={'id':old['document_id'],'url':old['source_url'].split('#page=')[0],'raw_ref':old['raw_ref'],'expected_sha256':scoped.SOURCE_SHA256}
    assert scoped.attach_retained_ir(row,by_page[old['physical_page']],item,scoped.SOURCE_SHA256)
    assert row==next(x for x in native_results if x['physical_page']==old['physical_page']),'Actual-native and retained-IR canonical outputs differ'
    restored=copy.deepcopy(row)
    for k,v in row['superseded_detector_diagnostics']['original_record_fields'].items():restored[k]=v
    for k in ['canonical_structure_selection','superseded_detector_diagnostics','source_infrastructure_structures']:restored.pop(k)
    assert restored==old,'Original record does not restore exactly'
   else:assert row==old
   derived.append(row)
 assert not calls and sorted(selected)==[2,3,6,46]
 for name,content in outputs(derived).items():(a.out/name).write_bytes(content)
 native_dir=a.out/'selected-four';native_dir.mkdir()
 for name,content in outputs(native_results).items():(native_dir/name).write_bytes(content)
 csv_rows=list(csv.DictReader(io.StringIO((a.out/'records.csv').read_text())));assert len(csv_rows)==636
 assert all(c['text']==r['text']for c,r in zip(csv_rows,derived)),'CSV does not use canonical text'
 remaining=sum(not c['independent_character_agreement']for r in derived for t in r['tables']for c in t['cells'])
 superseded=sum(not c['independent_character_agreement']for r in derived for t in r.get('superseded_detector_diagnostics',{}).get('original_record_fields',{}).get('tables',[])for c in t['cells'])
 assert remaining==0 and superseded==795 and remaining+superseded==795
 report={'passed':True,'script_sha256':sha(pathlib.Path(__file__).read_bytes()),'module_sha256':{f.name:sha(f.read_bytes())for f in family.glob('*.py')},
         'source_sha256':scoped.SOURCE_SHA256,'new_actual_native_pages':sorted(selected),'no_full62or636_native_reparse':True,
         'baseline_records':636,'changed_records':4,'unchanged_records':632,'all_original_fields_restore_exact':True,
         'source_dimensions':scoped.summary(derived),'canonical_selected_tables':sum(len(r['tables'])for r in native_results),
         'superseded_old_infrastructure_cells':sum(len(t['cells'])for r in native_results for t in r['superseded_detector_diagnostics']['original_record_fields']['tables']),
         'whole636_remaining_false_cells':remaining,'whole636_superseded_false_cells':superseded,'all795old_failures_retained':True,
         'prior_canonical_selections_preserved_exact':sum(bool(r.get('canonical_structure_selection'))for r in originals),
         'canonical_selections_after':sum(bool(r.get('canonical_structure_selection'))for r in derived),
         'image_placeholders_before':sum(r['image_placeholder_count']for r in originals),'image_placeholders_after':sum(r['image_placeholder_count']for r in derived),
         'forbidden_calls':calls,'csv_uses_canonical_text':True,'canonical_jsonl_sha256':sha((a.out/'records.jsonl').read_bytes()),'canonical_csv_sha256':sha((a.out/'records.csv').read_bytes()),
         'scope':'Four exact-source contents/revision-cover pages. 632retained records unchanged. No wholebook semantic/legal/edition/table-detection promotion; No old795faileddetector cells remain canonical; exactold795payloads persist in superseded diagnostics. Existing CID/adoption/reference and universal table-detection/semantics gaps remain.'}
 assert report['image_placeholders_before']==report['image_placeholders_after']==201
 (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
