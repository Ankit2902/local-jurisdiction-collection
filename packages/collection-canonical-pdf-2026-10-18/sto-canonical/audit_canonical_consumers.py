"""Independent stored canonical fields/CSV -> original native glyph/word/cell audit.
No collector/parser/helper imports. Exact three pages only; image APIs are forbidden.
"""
import json,csv,io,collections,contextlib,socket,hashlib,re
from pathlib import Path
from unittest.mock import patch
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
root=Path(__file__).resolve().parent;fix=root/'candidate/collectors/encodeplus/fixtures/sto-four-column';raw=(fix/'source.pdf').read_bytes();rows=[json.loads(x) for x in (root/'canonical-three-pages/records.jsonl').read_text().split('\n') if x];csvrows=list(csv.DictReader((root/'canonical-three-pages/records.csv').open(newline='')));baseline={r['id']:r for r in [json.loads(x) for x in (fix/'baseline-three-pages.jsonl').read_text().split('\n') if x]};assert hashlib.sha256(raw).hexdigest()=='594128464bdc6c0dd1336aa00acb93c1ecbfdc5980e4265e63d6e134df98f127';calls=[];checks=[];original=PDFStream.get_data
clean=lambda text:re.sub(r'\s+',' ',text).strip()
def reject(*a,**kw):calls.append('forbidden_image_render_or_network');raise AssertionError('Noimage/render/network')
def noimages(stream):
 if getattr(stream.attrs.get('Subtype'),'name',None)=='Image' or ('W' in stream.attrs and 'H' in stream.attrs):calls.append('image_stream');raise AssertionError('Noimagebytes')
 return original(stream)
with contextlib.ExitStack() as guard:
 guard.enter_context(patch.object(PDFStream,'get_data',noimages))
 for obj,names in [(socket,['socket']),(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open'])]:
  for name in names:
   if hasattr(obj,name):guard.enter_context(patch.object(obj,name,reject))
 pdf=pdfplumber.open(io.BytesIO(raw));native=pypdfium2.PdfDocument(raw)
 try:
  for row,export in zip(rows,csvrows):
   n=row['physical_page'];page=pdf.pages[n-1].dedupe_chars(tolerance=.5);words=page.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size']);glyphs=page.chars;np=native[n-1];tp=np.get_textpage()
   try:
    assert not page.images and row['image_placeholder_count']==0;assert len(row['tables'])==len(row['ordered_blocks'])==1;table=row['tables'][0];block=row['ordered_blocks'][0];cells=table['cells'];assert row['canonical_structure_selection']['canonical_table_ids']==[table['id']] and table['id']==block['id'];assert table['header_rows']==[0]
    word_owners=collections.Counter();glyph_owners=collections.Counter();cell_texts=[]
    for cell in cells:
     box=cell['extraction_bbox'];bounded=tp.get_text_bounded(box[0],float(page.height)-box[3],box[2],float(page.height)-box[1]);assert clean(bounded)==clean(cell['text']) and cell['independent_character_agreement'] and cell['independent_ordered_characters_agree'];assert cell['rowspan']==cell['colspan']==1
     sourcewordindices=[i for i,w in enumerate(words) if box[0]<=(w['x0']+w['x1'])/2<=box[2] and box[1]<=(w['top']+w['bottom'])/2<=box[3]];expectedids=[row['id']+'::word:'+str(i+1) for i in sourcewordindices];assert expectedids==cell['word_ids'];assert cell['text']==' '.join(words[i]['text'] for i in sourcewordindices);word_owners.update(sourcewordindices)
     actualglyphindices=[int(gid.rsplit(':',1)[1])-1 for gid in cell['source_glyph_ids']]
     for i in actualglyphindices:
      g=glyphs[i];assert box[0]<=(g['x0']+g['x1'])/2<=box[2] and box[1]<=(g['top']+g['bottom'])/2<=box[3]
     assert clean(''.join(glyphs[i]['text'] for i in actualglyphindices)).replace(' ','')==clean(cell['text']).replace(' ','');glyph_owners.update(actualglyphindices);cell_texts.append(cell['text'])
    assert word_owners==collections.Counter(range(len(words)));nonspace=[i for i,g in enumerate(glyphs) if g['text'].strip() and g['text'] not in ['\u200b','\u00ad','\ufeff']];assert glyph_owners==collections.Counter(nonspace);assert block['word_ids']==[wid for c in cells for wid in c['word_ids']];assert block['source_glyph_ids']==[gid for c in cells for gid in c['source_glyph_ids']]
    expected='\n'.join('\t'.join(c['text'] for c in cells if c['row']==ri) for ri in range(max(c['row'] for c in cells)+1));assert row['text']==block['text']==export['text']==expected;assert row['pdf_qualification']['detected_table_count']==1 and row['pdf_qualification']['detected_table_cells']==row['pdf_qualification']['independent_table_cells_agree']==len(cells)
    restored=json.loads(json.dumps(row));old=restored['superseded_detector_diagnostics']['original_record_fields'];assert old=={k:baseline[row['id']][k] for k in ['tables','ordered_blocks','text','ordering','pdf_qualification']}
    for key,value in old.items():restored[key]=value
    for key in ['source_physical_schedules','superseded_detector_diagnostics','canonical_structure_selection']:restored.pop(key)
    assert restored==baseline[row['id']];checks.append({'page':n,'canonical_cells':len(cells),'bounded_original_cell_queries_exact':True,'raw_source_word_owners_unique':len(word_owners),'raw_source_glyph_owners_unique':len(glyph_owners),'headers_cells_spans_source_order':True,'canonical_tables_blocks_text_CSV_agree':True,'diagnostics_restore_exact_original':True})
   finally:tp.close();np.close()
 finally:pdf.close();native.close()
assert not calls;assert sum(x['canonical_cells'] for x in checks)==308 and sum(x['raw_source_word_owners_unique'] for x in checks)==550 and sum(x['raw_source_glyph_owners_unique'] for x in checks)==3560
report={'passed':True,'scope':'Independent original3nativepages -> storedcanonicalconsumer fields, no normalization/helper imports','source_sha256':hashlib.sha256(raw).hexdigest(),'records_sha256':hashlib.sha256((root/'canonical-three-pages/records.jsonl').read_bytes()).hexdigest(),'pages':checks,'pixel_render_network_calls':calls,'no_full636_reparse':True,'canonical_cell_total':308,'canonical_word_total':550,'canonical_glyph_total':3560,'no_logical_continuation_or_intended_legal_meaning_inferred':True,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(root/'independent-canonical-consumer-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
