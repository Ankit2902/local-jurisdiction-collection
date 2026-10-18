"""Only four retained pages' text/word geometry for nine cached opaque prose boxes."""
import collections,contextlib,hashlib,io,json,socket,sys
from pathlib import Path
from unittest.mock import patch
import pdfplumber,pypdfium2
from PIL import Image
from inventory import S,inventory
H=Path(__file__).resolve().parent;B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');N=B/'outputs/collection-readiness-post1997ee1-2026-10-17/infrastructure-logical-structure-candidate-v1/source.pdf';data=N.read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest=='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c';records=[json.loads(l)for l in(S/'records.jsonl').read_text().split('\n')if l];target_ids={f['id']for f in inventory(records)['fragments']if f['role']=='body_text_line'and '\n'in f['text']};selected=[(r,f)for r in records for f in r['source_fragments']if r['id']+'::source:'+str(f['page'])+':'+str(f['block_index'])in target_ids];assert len(selected)==9 and sorted({f['page']for r,f in selected})==[11,12,13,14];calls=[]
def no(*a,**k):calls.append('forbidden_image_or_network');raise AssertionError(calls[-1])
results=[]
with contextlib.ExitStack()as guards:
 for obj,key in [(socket,'socket'),(Image,'open'),(pdfplumber.page.Page,'to_image'),(pypdfium2.PdfPage,'render')]:guards.enter_context(patch.object(obj,key,no))
 for key in ['FPDFImageObj_GetBitmap','FPDFImageObj_GetRenderedBitmap','FPDFImageObj_GetImageDataDecoded','FPDFImageObj_GetImageDataRaw']:
  if hasattr(pypdfium2.raw,key):guards.enter_context(patch.object(pypdfium2.raw,key,no))
 with pdfplumber.open(io.BytesIO(data))as pdf:
  native=pypdfium2.PdfDocument(data)
  try:
   pages={}
   for pn in [11,12,13,14]:
    pg=pdf.pages[pn-1].dedupe_chars(tolerance=.5);ws=pg.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size']);pages[pn]=(pg,ws)
   for r,f in selected:
    b=f['block'];pn=f['page'];pg,words=pages[pn];pairs=[(ident,words[int(ident.rsplit(':',1)[1])-1])for ident in b['word_ids']];assert all(w['text']and w['top']>=b['bbox'][1]-.6 and w['bottom']<=b['bbox'][3]+.6 for ident,w in pairs)
    ordered=sorted(pairs,key=lambda pair:(pair[1]['top'],pair[1]['x0']));lines=[]
    for ident,w in ordered:
     if not lines or abs(w['top']-lines[-1]['reference_top'])>3:lines.append({'reference_top':w['top'],'words':[]})
     lines[-1]['words'].append({'id':ident,**{k:w[k]for k in ['text','fontname','size','x0','x1','top','bottom']}})
    tp=native[pn-1].get_textpage()
    try:
     for ln in lines:
      ln['words'].sort(key=lambda w:w['x0']);ln['text']=' '.join(w['text']for w in ln['words']);x0=min(w['x0']for w in ln['words']);x1=max(w['x1']for w in ln['words']);y0=min(w['top']for w in ln['words']);y1=max(w['bottom']for w in ln['words']);ln['bbox']=[x0,y0,x1,y1];ln['native_query_bbox_pdf']=[x0-.01,float(pg.height)-y1-.01,x1+.01,float(pg.height)-y0+.01];ln['independent_native_text']=tp.get_text_bounded(*ln['native_query_bbox_pdf']);ln['independent_nonwhitespace_order_equal']=''.join(ln['text'].split())==''.join(ln['independent_native_text'].split())
    finally:tp.close()
    physical='\n'.join(ln['text']for ln in lines);actualids=[w['id']for ln in lines for w in ln['words']];results.append({'unit_id':r['id'],'source_fragment':r['id']+'::source:'+str(pn)+':'+str(f['block_index']),'page':pn,'block_index':f['block_index'],'original_source_text':b['text'],'source_bbox':b['bbox'],'original_word_ids':b['word_ids'],'physical_text':physical,'source_order_nonwhitespace_equal':' '.join(b['text'].split()).replace(' ','')==''.join(physical.split()),'word_ids_counter_equal':collections.Counter(actualids)==collections.Counter(b['word_ids']),'word_ids_sequence_equal':actualids==b['word_ids'],'lines':lines})
  finally:native.close()
assert not calls and hashlib.sha256(N.read_bytes()).hexdigest()==digest
report={'schema_version':1,'source_sha256':digest,'source_native_path':str(N.relative_to(B)),'target_pages':[11,12,13,14],'target_fragments':9,'physical_lines':sum(len(x['lines'])for x in results),'all_source_word_ID_counters_equal':all(x['word_ids_counter_equal']for x in results),'all_source_word_ID_sequences_equal':all(x['word_ids_sequence_equal']for x in results),'all_source_nonwhitespace_order_equal':all(x['source_order_nonwhitespace_equal']for x in results),'independent_native_line_queries':sum(len(x['lines'])for x in results),'independent_native_line_queries_agree':sum(ln['independent_nonwhitespace_order_equal']for x in results for ln in x['lines']),'forbidden_image_or_network_calls':calls,'whole_document_parse':False,'scope':'Only text/word geometry for four pages, nine previously opaque source fragments; no image pixels/native binary rewriting/render/OCR/guessed semantic corrections.','fragments':results};(H/'multiline-native-geometry.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='fragments'},indent=2))
