"""Source-bound lightweight rebase replay: reuse retained geometry; native text only."""
import sys;sys.dont_write_bytecode=True
import json,hashlib,copy,socket
from pathlib import Path
from unittest.mock import patch
import pypdfium2
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];REPO=ROOT/'github/local-jurisdiction-collection';sys.path.insert(0,str(REPO/'collectors/official'))
import native_labels
BASE=ROOT/'outputs/collection-readiness-next-2026-10-17/pdf-cell-reconciliation-candidate-v1/spokane-native-attachments'
sha=lambda x:hashlib.sha256(x).hexdigest()
def deny(*a,**kw):raise AssertionError('Forbidden network/pixels/vector reparse')
source=json.loads((BASE/'summary.json').read_text());results=[]
for n,a in enumerate(source['attachments'],1):
 path=BASE/f'attachment-{n}/records.jsonl';rawrows=path.read_bytes();rows=[json.loads(x) for x in rawrows.decode().splitlines()];data=(ROOT/a['raw_ref']).read_bytes();assert sha(data)==a['source_sha256']
 for row in rows:
  q=row['attachment_native_text_qualification'];row['pdf_qualification']['source_original_glyph_count']=q['pdfminer_original_glyph_count'];row['pdf_qualification']['source_deduplicated_glyph_count']=q['pdfminer_deduplicated_glyph_count']
 owners=[]
 for o in a['required_by']:
  owner=dict(o,owner_record_id=o['owner_id'],owner_document_id=o['owner_item'],owner_source_sha256=o['owner_raw_sha256'],reference_url=a['source_url']);owners.append(owner)
  original=ROOT/o['owner_item_receipt'];assert sha(original.read_bytes())==o['owner_item_receipt_sha256']
 row=rows[0];item={'id':row['document_id'],'url':a['source_url'],'heading':row['heading'],'raw_ref':a['raw_ref']};config={k:row[k] for k in ('jurisdiction','state','publication')};config['native_label_attachment_rules']=[{'url':a['source_url'],'sha256':a['source_sha256'],'source_kind':'image-document' if n==3 else 'map'}]
 with patch.object(socket.socket,'connect',deny),patch.object(pypdfium2.PdfPage,'render',deny),patch.object(pypdfium2.PdfPage,'get_objects',deny),patch.object(pypdfium2.PdfImage,'extract',deny),patch.object(pypdfium2.PdfImage,'get_bitmap',deny),patch('pdfplumber.open',side_effect=deny):
  projected,q=native_labels.project(data,item,config,owners,rows)
 out=HERE/'spokane-native-label-rebase'/f'attachment-{n}';out.mkdir(parents=True,exist_ok=True)
 (out/'records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=True)+'\n' for r in projected));(out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n')
 old=[json.loads(x) for x in (BASE/f'native-label-derivative-v3/attachment-{n}/records.jsonl').read_text().splitlines()]
 for before,after in zip(old,projected):
  assert before['native_label_text']==after['native_label_text'];assert before['native_label_runs']==after['native_label_runs'];assert before['native_label_glyph_geometry']==after['native_label_glyph_geometry'];assert before['text']==after['text'];assert before['id']==after['id'];assert before['image_placeholder_count']==after['image_placeholder_count']
 assert sha(path.read_bytes())==sha(rawrows);assert sha((ROOT/a['raw_ref']).read_bytes())==a['source_sha256']
 result={'source_url':a['source_url'],'source_sha256':a['source_sha256'],'historical_base_geometry_sha256':sha(rawrows),'base_geometry_parser_scope':'Previously executed isolated9eb-derived coordinate parser; counts copied only from exact bound original/dedup source-count receipt. Not a new complete coordinate reparse.','pages':len(projected),'runs':sum(len(r['native_label_runs']) for r in projected),'glyphs':sum(len(r['native_label_glyph_geometry']) for r in projected),'qualified':q['attachment_text_normalization_qualified'],'source_no_glyph_pages':q['source_proven_no_glyph_pages'],'same_native_labels_order_geometry_text_image_placeholders_as_proven_v3':True,'sources_unchanged':True};results.append(result);print(json.dumps(result),flush=True)
report={'schema_version':1,'network_requests':0,'pixel_operations':0,'PDFminer_or_vector_reparses':0,'production_helper_sha256':sha((REPO/'collectors/official/native_labels.py').read_bytes()),'driver_sha256':sha(Path(__file__).read_bytes()),'attachments':results,'total_pages':sum(r['pages'] for r in results),'total_runs':sum(r['runs'] for r in results),'total_glyphs':sum(r['glyphs'] for r in results),'publication_complete':False}
(HERE/'spokane-native-label-rebase/summary.json').write_text(json.dumps(report,indent=2)+'\n')
