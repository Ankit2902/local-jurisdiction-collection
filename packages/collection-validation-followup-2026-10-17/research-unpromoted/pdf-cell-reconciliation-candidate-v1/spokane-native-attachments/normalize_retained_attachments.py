"""Source-bound required attachment labels/[IMAGE] only; never pixels/OCR/network."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,io,socket,re
from pathlib import Path
from unittest.mock import patch
import pdfplumber,pypdfium2
base=Path(__file__).resolve().parent;sys.path.insert(0,str(base.parent));import pdf_structure
project=base.parents[3];source=project/'outputs/collection-readiness-2026-10-17/official/spokane-full-bulk-v10';ledger_path=project/'outputs/collection-readiness-next-2026-10-17/spokane-required-native-pdf-attachment-ledger.json'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def deny(*a,**k):raise AssertionError('Forbidden network/image operation')
socket.socket.connect=deny;socket.create_connection=deny
ledger=json.loads(ledger_path.read_text());metadata_sources={};owners={};downloads={}
for path in (source/'items').glob('*.json'):
 raw=path.read_bytes()
 if not any(a['url'].encode() in raw for a in ledger['required_native_attachments']):continue
 item=json.loads(raw);metadata_sources[str(path.relative_to(project))]=sha(raw)
 for asset in item.get('asset_downloads',[]):
  if asset.get('status')=='acquired':downloads[asset['url']]=asset
 for record in item['records']:
  for asset in record.get('assets',[]):
   if asset['url'] not in {a['url'] for a in ledger['required_native_attachments']}:continue
   link=next((l for l in record.get('links',[]) if l.get('url')==asset['url']),{})
   owners.setdefault(asset['url'],[]).append({'owner_id':record['id'],'owner_heading':record['heading'],'owner_source_url':record['source_url'],'owner_raw_ref':record['raw_ref'],'owner_raw_sha256':record['raw_sha256'],'owner_item':item['item']['id'],'owner_item_receipt':str(path.relative_to(project)),'owner_item_receipt_sha256':sha(raw),'reference_label':link.get('text'),'reference_context':asset.get('context'),'required':asset.get('required'),'classification':asset.get('classification')})
results=[];record_count=0
runtime={p.name:sha(p.read_bytes()) for p in [base.parent/'pdf_structure.py',base.parent/'bounded_decoder.py']}
for index,asset in enumerate(ledger['required_native_attachments'],1):
 url=asset['url'];path=project/asset['raw_ref'];raw=path.read_bytes();assert sha(raw)==asset['sha256'] and len(raw)==asset['bytes'];assert owners.get(url);download=downloads[url];assert download['sha256']==asset['sha256'] and source/download['raw_ref']==path
 filename=url.rsplit('/',1)[-1];dest=base/('attachment-'+str(index));dest.mkdir(exist_ok=True)
 reference_owners=owners[url];label=reference_owners[0].get('reference_label') or filename
 print('Normalize original attachment '+str(index)+' '+filename,flush=True)
 item={'id':url,'url':url,'heading':label,'raw_ref':asset['raw_ref']};config={'publication':'Spokane Municipal Code required native attachment','jurisdiction':'Spokane','state':'WA'}
 with patch.object(pypdfium2.PdfPage,'render',side_effect=deny),patch.object(pypdfium2.PdfPage,'get_objects',side_effect=deny),patch.object(pypdfium2.PdfImage,'extract',side_effect=deny),patch.object(pypdfium2.PdfImage,'get_bitmap',side_effect=deny):rows,_=pdf_structure.pages(raw,item,config)
 native=pypdfium2.PdfDocument(raw);miner=pdfplumber.open(io.BytesIO(raw));assert len(rows)==len(native)==len(miner.pages)==asset['current_integrity']['page_count']
 qualifications=[]
 for physical,(record,page) in enumerate(zip(rows,miner.pages),1):
  dedup=page.dedupe_chars(tolerance=.5);words=dedup.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size']);native_page=native[physical-1];tp=native_page.get_textpage()
  original_glyph_text=''.join(c['text'] for c in page.chars);dedup_glyph_text=''.join(c['text'] for c in dedup.chars);iumtext=tp.get_text_range()
  glyph_present=bool(pdf_structure.chars(original_glyph_text));ium_glyph_present=any(pypdfium2.raw.FPDFText_GetUnicode(tp,ci)>32 for ci in range(tp.count_chars()))
  no_glyph=not glyph_present and not ium_glyph_present and not iumtext.strip()
  assert glyph_present==ium_glyph_present,'Native text applicability disagreement'
  if no_glyph:assert not words and not dedup.chars,'No-glyph exemption has actual source glyphs'
  record['required_by']=reference_owners
  record['native_label_units']=[{'id':url+'::page:'+str(physical)+'::label:'+str(i+1),'text':w['text'],'bbox':pdf_structure.box(w),'fontname':w['fontname'],'font_size':w['size'],'source_order':i+1} for i,w in enumerate(words)]
  # The source owner explicitly identifies maps. Preserve whole graphic as a
  # placeholder even if it is vector-only; no label/color/polygon inference.
  explicit_map=any(re.search(r'\bmap\b',(o.get('reference_context') or '')+' '+(o.get('reference_label') or ''),re.I) for o in reference_owners)
  vector_count=len(page.curves)+len(page.lines)+len(page.rects)
  if explicit_map and vector_count and not any(b.get('id','').endswith('::vector-illustration') for b in record['ordered_blocks']):
   marker={'id':record['id']+'::source-explicit-map','kind':'image_placeholder','text':'[IMAGE]','bbox':[0,0,float(page.width),float(page.height)],'word_ids':[],'source_vector_object_count':vector_count,'source_qualification':'Required source reference explicitly identifies this graphic as a map; graphic interpretation omitted, extractable labels retained separately.','pixel_extraction':False}
   record['ordered_blocks'].append(marker);record['text']+=('\n' if record['text'] else '')+'[IMAGE]';record['image_placeholder_count']+=1
  q=record['pdf_qualification'];qualification={'physical_page':physical,'pdfium_native_character_count':tp.count_chars(),'pdfminer_original_glyph_count':len(page.chars),'pdfminer_deduplicated_glyph_count':len(dedup.chars),'native_label_word_count':len(words),'extractable_text_applicability':'not_applicable_both_independent_engines_source_has_no_text_glyphs' if no_glyph else 'applicable_native_text_labels_present','source_no_glyph_NA_qualified':no_glyph,'source_text_sha256_pdfium':sha(iumtext.encode()),'source_deduplicated_glyph_text_sha256':sha(dedup_glyph_text.encode()),'source_word_to_glyph_conservation':q['source_words_cover_deduplicated_glyph_characters'],'normalized_source_word_conservation':q['normalized_source_word_characters_agree'],'word_ownership_complete':q['source_word_ownership_complete'],'independent_native_text_engines_agree':q['independent_text_engine_characters_agree'],'label_units_match_source_words':len(record['native_label_units'])==len(words),'image_placeholders':record['image_placeholder_count'],'source_raster_image_metadata_count':len(page.images),'source_vector_object_count':vector_count,'source_explicit_map_reference':explicit_map,'legal_or_map_reading_order_qualified':False,'image_interpretation_requested':False,'review_conditions':q['review_conditions']}
  record['attachment_native_text_qualification']=qualification;qualifications.append(qualification)
  assert record['image_placeholder_count']>0 or glyph_present,'Source blank/image page has no policy representation'
  assert not re.search(r'data:image/',json.dumps(record),re.I),'Normalized image payload present'
  tp.close();native_page.close();dedup.close();page.close()
 native.close();miner.close()
 with (dest/'records.jsonl').open('w') as f:
  for row in rows:f.write(json.dumps(row,ensure_ascii=False).replace('\u2028','\\u2028').replace('\u2029','\\u2029').replace('\x85','\\u0085')+'\n')
 summary={'source_url':url,'raw_ref':asset['raw_ref'],'source_sha256':asset['sha256'],'pages':len(rows),'required_by':reference_owners,'available_native_label_pages':sum(not q['source_no_glyph_NA_qualified'] for q in qualifications),'source_proven_no_glyph_pages':sum(q['source_no_glyph_NA_qualified'] for q in qualifications),'native_label_words':sum(q['native_label_word_count'] for q in qualifications),'all_native_text_conservation_checks_passed':all(q['source_word_to_glyph_conservation'] and q['normalized_source_word_conservation'] and q['word_ownership_complete'] and q['independent_native_text_engines_agree'] for q in qualifications),'image_placeholders':sum(q['image_placeholders'] for q in qualifications),'normalization_covers_all_native_pages':True,'new_image_operations':0,'source_file_unchanged':sha(path.read_bytes())==asset['sha256'],'legal_semantic_complete':False,'acquisition_ledger_modified':False,'page_qualification':qualifications}
 (dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');results.append(summary);record_count+=len(rows);print(json.dumps({k:v for k,v in summary.items() if k not in ['page_qualification','required_by']}),flush=True)
assert all(sha((project/name).read_bytes())==expected for name,expected in metadata_sources.items());assert runtime=={p.name:sha(p.read_bytes()) for p in [base.parent/'pdf_structure.py',base.parent/'bounded_decoder.py']}
(base/'summary.json').write_text(json.dumps({'kind':'isolated source-bound normalization of four already acquired required native PDFs','network_requests':0,'image_operations':0,'runtime':runtime,'original_attachment_ledger_sha256':sha(ledger_path.read_bytes()),'source_owner_item_sha256':metadata_sources,'source_owner_and_native_files_unchanged':True,'attachment_count':4,'page_records':record_count,'attachments':results,'scope_note':'Available native labels retained; no-glyph text N/A requires both independent native engines. Images deliberately [IMAGE], not OCR/transcribed. Legal/map semantics and global publication completeness remain separate; original acquisition ledger unchanged.'},indent=2)+'\n')
