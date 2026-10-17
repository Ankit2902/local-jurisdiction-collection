"""Lightweight JSON/native-text projection; never repeats vector/PDFminer parsing."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,socket,copy
from pathlib import Path
from unittest.mock import patch
import pypdfium2
from native_labels import project_record
base=Path(__file__).resolve().parent;project=base.parents[3]
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def deny(*a,**k):raise AssertionError('Forbidden network/pixel operation')
socket.socket.connect=deny;socket.create_connection=deny
original=json.loads((base/'summary.json').read_text());results=[]
for index,attachment in enumerate(original['attachments'],1):
 src=base/('attachment-'+str(index))/'records.jsonl';source_bytes=src.read_bytes();rows=[json.loads(s) for s in source_bytes.decode().split('\n') if s];out=base/'native-label-derivative-v3'/('attachment-'+str(index));out.mkdir(parents=True,exist_ok=True)
 path=project/attachment['raw_ref'];raw=path.read_bytes();assert sha(raw)==attachment['source_sha256'];doc=None
 if attachment['available_native_label_pages']:doc=pypdfium2.PdfDocument(raw)
 corrected=[]
 with patch.object(pypdfium2.PdfPage,'render',side_effect=deny),patch.object(pypdfium2.PdfPage,'get_objects',side_effect=deny),patch.object(pypdfium2.PdfImage,'extract',side_effect=deny),patch.object(pypdfium2.PdfImage,'get_bitmap',side_effect=deny):
  for row in rows:
   original_row=copy.deepcopy(row);page=None;tp=None
   if not row['attachment_native_text_qualification']['source_no_glyph_NA_qualified']:
    page=doc[row['physical_page']-1];tp=page.get_textpage()
   corrected.append(project_record(row,tp))
   for key in ['id','document_id','physical_page','page_count','raw_sha256','raw_ref','required_by','pdfium_stream_text','pdfium_qualified_comparison_text']:
    assert row[key]==original_row[key],key
   assert not 'data:image/' in json.dumps(row).lower()
   if tp:tp.close()
   if page:page.close()
 if doc:doc.close()
 with (out/'records.jsonl').open('w') as f:
  for row in corrected:f.write(json.dumps(row,ensure_ascii=False).replace('\u2028','\\u2028').replace('\u2029','\\u2029').replace('\x85','\\u0085')+'\n')
 assert sha(src.read_bytes())==sha(source_bytes) and sha(path.read_bytes())==attachment['source_sha256']
 result={'source_url':attachment['source_url'],'native_sha256':attachment['source_sha256'],'historical_generic_normalization_sha256':sha(source_bytes),'pages':len(corrected),'native_label_pages':sum(bool(r['native_label_runs']) for r in corrected),'source_proven_no_glyph_pages':sum(r['requested_scope_qualification']['source_proven_no_glyph_text_NA'] for r in corrected),'native_label_run_count':sum(len(r['native_label_runs']) for r in corrected),'native_label_glyph_geometry_count':sum(len(r['native_label_glyph_geometry']) for r in corrected),'attachment_text_normalization_qualified':all(r['requested_scope_qualification']['attachment_text_normalization_qualified'] for r in corrected),'all_native_label_projection_checks_passed':all(r['requested_scope_qualification']['native_label_projection_complete'] for r in corrected),'image_placeholders':sum(r['image_placeholder_count'] for r in corrected),'source_proven_complex_vector_map_pages':sum(r['requested_scope_qualification']['source_graphic_map_qualification']['whole_map_graphic_placeholder_qualified'] for r in corrected),'source_owned_link_references':attachment['required_by'],'original_files_unchanged':True,'graphic_semantics_excluded_by_user_image_policy_not_required_for_completion':True,'map_reading_order_inferred':False,'publication_complete_not_asserted':True}
 results.append(result);(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='source_owned_link_references'}),flush=True)
 # Actual parcel/street labels must survive as full native strings, not generic
 # font-size splits. These are exact known source tokens, not transcribed pixels.
 if index==1:assert '35202.2115' in corrected[0]['native_label_text'] and '35202.2115' in corrected[0]['text']
 if index==2:assert 'Havana St' in corrected[0]['native_label_text'] and 'Broadway Ave' in corrected[0]['text']
report={'kind':'Lightweight source-bound native-label derivative; no PDFminer/vector reparsing, pixels or network','network_requests':0,'pixel_operations':0,'source_generic_summary_sha256':sha((base/'summary.json').read_bytes()),'native_label_module_sha256':sha((base/'native_labels.py').read_bytes()),'driver_sha256':sha(Path(__file__).read_bytes()),'attachments':results,'total_pages':sum(r['pages'] for r in results),'native_label_pages':sum(r['native_label_pages'] for r in results),'source_proven_no_glyph_pages':sum(r['source_proven_no_glyph_pages'] for r in results),'overall_publication_complete_not_asserted':True}
(base/'native-label-derivative-v3/summary.json').write_text(json.dumps(report,indent=2)+'\n')
