"""Recompute four native index regions; compose exact supplied STO outputs in retained636IR."""
import argparse,collections,contextlib,copy,hashlib,io,json,socket,sys
from pathlib import Path
from unittest.mock import patch
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'candidate'))
from collectors.encodeplus import upoc_printed_index as scoped
from collectors.encodeplus.native_document import outputs
P=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');V=P/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/overland-five-required-v3'
sha=lambda b:hashlib.sha256(b).hexdigest();csha=lambda v:sha(json.dumps(v,sort_keys=True).encode())
a=argparse.ArgumentParser();a.add_argument('--sto-records',type=Path,required=True);args=a.parse_args();sto=[json.loads(l) for l in args.sto_records.read_text().splitlines()];assert len(sto)==3;sto_by={r['id']:r for r in sto};inv=json.loads((V/'inventory.json').read_text());items={x['id']:x for x in inv['items']};base=[json.loads(l) for l in (V/'records.jsonl').read_text().splitlines()];counts=collections.Counter();proofs=[];changed=[];combined=[];calls=[];sources={};final=[]
original=PDFStream.get_data

def noimage(stream):
 if getattr(stream.attrs.get('Subtype'),'name',None)=='Image' or ('W' in stream.attrs and 'H' in stream.attrs):calls.append('image_stream.get_data');raise AssertionError('No images')
 return original(stream)
def no(*args,**kwargs):calls.append('image_or_network');raise AssertionError('No image/decode/render/OCR/network')
with contextlib.ExitStack() as stack:
 stack.enter_context(patch.object(PDFStream,'get_data',noimage))
 for obj,names in [(socket,['socket']),(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open'])]:
  for name in names:
   if hasattr(obj,name):stack.enter_context(patch.object(obj,name,no))
 try:
  for b in base:
   prior=copy.deepcopy(sto_by.get(b['id'],b));r=copy.deepcopy(prior);it=items[r['document_id']];h=it['expected_sha256'];eligible=h in scoped.PROFILES and r['physical_page'] in [1,169]
   if eligible:
    if h not in sources:
     data=(V/it['raw_ref']).read_bytes();assert sha(data)==h;sources[h]=(pdfplumber.open(io.BytesIO(data)),pypdfium2.PdfDocument(data))
    pdf,native=sources[h];n=r['physical_page'];pg=native[n-1];tp=pg.get_textpage()
    try:assert scoped.attach_record(r,pdf.pages[n-1],tp,it,h)
    finally:tp.close();pg.close()
    fields=r['superseded_detector_diagnostics']['original_record_fields'];assert fields=={k:prior[k] for k in ['tables','ordered_blocks','text','ordering','pdf_qualification']}
    outside=copy.deepcopy(r)
    for k,v in fields.items():outside[k]=v
    for k in ['superseded_detector_diagnostics','canonical_structure_selection','source_printed_indexes']:outside.pop(k)
    assert outside==prior
    assert r['tables']==[] and [x['text'] for x in r['ordered_blocks']]==[u['canonical_printed_text'] for u in r['source_printed_indexes'][0]['units']]
    changed.append(r)
   else:assert not scoped.attach_record(r,None,None,it,h);assert r==prior
   assert [x for x in r['ordered_blocks'] if x['kind']=='image_placeholder']==[x for x in b['ordered_blocks'] if x['kind']=='image_placeholder']
   original_fields=r.get('superseded_detector_diagnostics',{}).get('original_record_fields')
   original_tables=original_fields['tables'] if original_fields else r['tables']
   assert original_tables==b['tables'],'Original diagnostic table lineage changed'
   counts['original_false_cell_payloads_preserved']+=sum(not c['independent_character_agreement'] for t in original_tables for c in t['cells'])
   counts['image_placeholders_preserved']+=r['image_placeholder_count'];counts['records']+=1;counts['new_UPOC_canonical_selections']+=eligible;counts['prior_STO_canonical_selections_preserved']+=b['id'] in sto_by
   if eligible or b['id'] in sto_by:combined.append(r)
   proofs.append({'id':r['id'],'before_UPOC_canonical_sha256':csha(prior),'after_sha256':csha(r),'new_UPOC_selection':eligible,'prior_STO_selection_preserved':b['id'] in sto_by,'nonselected_record_exact':not eligible and r==prior,'original_detector_tables_sha256':csha(b['tables']),'preserved_detector_tables_sha256':csha(original_tables)})
   final.append(r)
 finally:
  for pdf,native in sources.values():pdf.close();native.close()
assert counts==dict(records=636,new_UPOC_canonical_selections=4,prior_STO_canonical_selections_preserved=3,image_placeholders_preserved=201,original_false_cell_payloads_preserved=795)
assert not calls
for name,rs in [('changed-four-pages.jsonl',changed),('combined-changed-seven-pages.jsonl',combined)]:
 (R/name).write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rs))
# Assert the operational CSV serializer consumes authoritative canonical text.
import csv
csvrows=list(csv.DictReader(io.StringIO(outputs(changed)['records.csv'].decode())));assert [r['text'] for r in csvrows]==[r['text'] for r in changed]
for name,body in outputs(final).items():(R/('derived-'+name)).write_bytes(body)
assert [json.loads(line) for line in (R/'derived-records.jsonl').read_text().splitlines()]==final
assert [r['text'] for r in csv.DictReader(io.StringIO((R/'derived-records.csv').read_text()))]==[r['text'] for r in final]
report={'passed':True,'scope':'636retainedIR comparison, only4nativepages recomputed; supplied3STOcanonicalrecords retained exact','input_records_sha256':sha((V/'records.jsonl').read_bytes()),'supplied_STO_records_sha256':sha(args.sto_records.read_bytes()),'helper_sha256':sha((R/'candidate/collectors/encodeplus/upoc_printed_index.py').read_bytes()),'counts':dict(counts),'unchanged_by_UPOC':632,'original_noop_records':629,'derived_jsonl_sha256':sha((R/'derived-records.jsonl').read_bytes()),'derived_csv_sha256':sha((R/'derived-records.csv').read_bytes()),'dimensions':scoped.summary(changed),'canonical_CSV_text_matches':True,'forbidden_calls':calls,'original_table_diagnostic_lineage_unchanged':True,'image_markers_position_ownership_unchanged':True,'per_record_proof':proofs,'changed_four_sha256':sha((R/'changed-four-pages.jsonl').read_bytes()),'combined_seven_sha256':sha((R/'combined-changed-seven-pages.jsonl').read_bytes())}
(R/'actual-canonical-differential.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='per_record_proof'},indent=2))
