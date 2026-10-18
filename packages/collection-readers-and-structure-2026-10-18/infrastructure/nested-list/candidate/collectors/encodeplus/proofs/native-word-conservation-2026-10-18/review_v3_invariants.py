"""Retained-IR differential plus five bounded native cell queries; no fullPDF reparse."""
import collections,contextlib,hashlib,json,socket
from pathlib import Path
from unittest.mock import patch
import pypdfium2
root=Path(__file__).resolve().parent;project=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');parent=project/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59';v2=parent/'overland-five-required-v2';v3=parent/'overland-five-required-v3'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for directory in (v2,v3):
 for line in (directory/'MANIFEST.sha256').read_text().splitlines():
  digest,rel=line.split('  ',1);assert sha(directory/rel)==digest,rel
manifest_receipts={'v2_manifest_sha256':sha(v2/'MANIFEST.sha256'),'v3_manifest_sha256':sha(v3/'MANIFEST.sha256'),'v3_parser_sha256':sha(v3/'collectors/encodeplus/pdf_structure.py'),'full6248_direct_query_report_sha256':sha(parent/'OVERLAND-FIVE-EXACT-BOUNDS-FULL6248-REPLAY.json')}
counts=collections.Counter();images=collections.defaultdict(list);selected={}
with (v2/'records.jsonl').open() as old,(v3/'records.jsonl').open() as new:
 for raw_old,raw_new in __import__('itertools').zip_longest(old,new):
  assert raw_old is not None and raw_new is not None
  before=json.loads(raw_old);after=json.loads(raw_new);counts['pages']+=1
  for t in after['tables']:
   for c in t['cells']:
    precise=c.pop('extraction_bbox');assert [round(v,3) for v in precise]==c['bbox'];c['extraction_bbox']=precise
    counts['cells']+=1;counts['cell_disagreements']+=not c['independent_character_agreement']
  stripped=json.loads(raw_new)
  for t in stripped['tables']:
   for c in t['cells']:c.pop('extraction_bbox')
  assert before==stripped,after['id']
  q=after['pdf_qualification'];assert q['source_word_ownership_complete'] and q['normalized_source_word_characters_agree'] and q['source_words_cover_deduplicated_glyph_characters']
  owned=[w for b in after['ordered_blocks'] for w in b['word_ids']];assert len(owned)==len(set(owned))==q['source_word_count']
  counts['source_words']+=len(owned);counts['engine_disagreement_pages']+=not q['independent_text_engine_characters_agree'];counts['cid_literal_pages']+=bool(q['undecoded_cid_literals'])
  image_blocks=[b for b in after['ordered_blocks'] if b['kind']=='image_placeholder'];assert len(image_blocks)==after['image_placeholder_count']
  assert all(b['text']=='[IMAGE]' and not b.get('word_ids') and b['pixel_extraction'] is False for b in image_blocks)
  counts['image_placeholders']+=len(image_blocks)
  images[after['document_id']].extend({'page':after['physical_page'],'id':b['id'],'source_name':b.get('source_name'),'bbox':b['bbox'],'vector':bool(b.get('source_vector_object_count'))} for b in image_blocks)
  if after['physical_page']==169 and after['document_id'] in ('overland-required-c15031ba3373','overland-required-48e085dea510'):selected[after['document_id']]=after
assert counts['pages']==636 and counts['cells']==6248 and counts['cell_disagreements']==795
inventory=json.loads((v3/'inventory.json').read_text());items={i['id']:i for i in inventory['items']};calls=[];queries=[]
def forbidden(*args,**kwargs):calls.append('forbidden_native_image_or_network');raise AssertionError(calls[-1])
with contextlib.ExitStack() as stack:
 for obj,names in [(socket,['socket']),(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['extract','get_bitmap','get_data'])]:
  for name in names:
   if hasattr(obj,name):stack.enter_context(patch.object(obj,name,forbidden))
 for ident,row in selected.items():
  item=items[ident];data=(v3/item['raw_ref']).read_bytes();assert hashlib.sha256(data).hexdigest()==item['expected_sha256'];doc=pypdfium2.PdfDocument(data)
  try:
   page=doc[168];tp=page.get_textpage()
   try:
    for cell in row['tables'][0]['cells']:
     number=int(cell['id'].rsplit(':',1)[1])
     if number not in ([91,95] if 'c15031' in ident else [59,91,95]):continue
     b=cell['extraction_bbox'];exact=tp.get_text_bounded(b[0],row['height']-b[3],b[2],row['height']-b[1]);r=cell['bbox'];rounded=tp.get_text_bounded(r[0],row['height']-r[3],r[2],row['height']-r[1]);assert exact==cell['independent_pdfium_text'];queries.append({'cell_id':cell['id'],'raw_source_sha256':item['expected_sha256'],'extraction_bbox':b,'exact_query':exact,'rounded_query':rounded,'existing_cell_agreement':cell['independent_character_agreement']})
   finally:tp.close();page.close()
  finally:doc.close()
assert len(queries)==5 and not calls
report={'passed':True,'scope':'Independent retainedIR all636invariants plus onlytwo actualnativepages/fivequeries, not repeatedfull636parse','source_bindings':manifest_receipts,'counts':dict(counts),'all_original_v2_fields_identical_excluding_only_extraction_bbox':True,'all_image_markers_ids_ownership_geometry_unchanged':True,'fullprecision_native_queries':queries,'source_image_names':dict(images),'forbidden_calls':calls,'no_semantic_promotion':True}
(root/'v3-independent-invariants.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('source_image_names','fullprecision_native_queries')},indent=2))
