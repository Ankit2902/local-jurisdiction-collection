"""Actual source-pinned canonical projection of exactly three native pages. No pixel APIs."""
import json,hashlib,copy,io,sys,contextlib,socket,collections
from pathlib import Path
from unittest.mock import patch
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'candidate'))
from collectors.encodeplus import sto_physical_schedule as scoped
from collectors.encodeplus.native_document import outputs
family=root/'candidate/collectors/encodeplus';fix=family/'fixtures/sto-four-column';config=json.loads((fix/'source.json').read_text());data=(fix/'source.pdf').read_bytes();assert hashlib.sha256(data).hexdigest()==scoped.SOURCE_SHA256
baseline=[json.loads(x) for x in (fix/'baseline-three-pages.jsonl').read_text().split('\n') if x];rows=[];calls=[];original=PDFStream.get_data
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p.relative_to(family)):sha(p) for p in family.rglob('*') if p.is_file()}
def image_stream_guard(stream):
 if getattr(stream.attrs.get('Subtype'),'name',None)=='Image' or ('W' in stream.attrs and 'H' in stream.attrs):calls.append('image_stream');raise AssertionError('Image bytes forbidden')
 return original(stream)
def forbidden(*a,**kw):calls.append('pixel_render_or_network');raise AssertionError('No pixel/render/network')
with contextlib.ExitStack() as guard:
 guard.enter_context(patch.object(PDFStream,'get_data',image_stream_guard))
 for obj,names in [(socket,['socket']),(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open'])]:
  for name in names:
   if hasattr(obj,name):guard.enter_context(patch.object(obj,name,forbidden))
 pdf=pdfplumber.open(io.BytesIO(data));native=pypdfium2.PdfDocument(data)
 try:
  for old in baseline:
   row=copy.deepcopy(old);number=old['physical_page'];page=native[number-1];tp=page.get_textpage()
   try:assert scoped.attach_record(row,pdf.pages[number-1],tp,config['item'],scoped.SOURCE_SHA256)
   finally:tp.close();page.close()
   diagnostic=row['superseded_detector_diagnostics']['original_record_fields'];assert diagnostic=={k:old[k] for k in row['canonical_structure_selection']['authoritative_fields']};restored=copy.deepcopy(row)
   for k,v in diagnostic.items():restored[k]=v
   for k in ['source_physical_schedules','superseded_detector_diagnostics','canonical_structure_selection']:restored.pop(k)
   assert restored==old;rows.append(row)
 finally:pdf.close();native.close()
assert not calls
out=root/'canonical-three-pages';out.mkdir(exist_ok=True)
for name,content in outputs(rows).items():(out/name).write_bytes(content)
summary=scoped.summary(rows);assert summary['complete_physical_cells']==308;assert not summary['whole_pdf_table_semantics_complete'];assert summary['unresolved_statute_only_lines']==7 and summary['source_alignment_anomalies']==1
report={'passed':True,'source_sha256':sha(fix/'source.pdf'),'physical_pages':[r['physical_page'] for r in rows],'helper_sha256':sha(family/'sto_physical_schedule.py'),'canonical_cell_count':sum(len(t['cells']) for r in rows for t in r['tables']),'canonical_false_cells':sum(not c['independent_character_agreement'] for r in rows for t in r['tables'] for c in t['cells']),'superseded_false_cells_exact':sum(not c['independent_character_agreement'] for r in rows for t in r['superseded_detector_diagnostics']['original_record_fields']['tables'] for c in t['cells']),'canonical_source_word_count':sum(len(b['word_ids']) for r in rows for b in r['ordered_blocks']),'canonical_source_glyph_count':sum(len(b['source_glyph_ids']) for r in rows for b in r['ordered_blocks']),'image_placeholders':sum(r['image_placeholder_count'] for r in rows),'all_original_fields_restored_exact_from_diagnostics':True,'selection_profiles':[r['canonical_structure_selection']['profile'] for r in rows],'physical_dimensions':summary,'forbidden_calls':calls,'no_full636_reparse':True,'source_after_unchanged':before=={str(p.relative_to(family)):sha(p) for p in family.rglob('*') if p.is_file()},'output_sha256':{name:sha(out/name) for name in ['records.jsonl','records.csv']},'script_sha256':sha(Path(__file__))};(root/'canonical-three-page-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
