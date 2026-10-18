"""Observed official PDF alternatives for exact legacy-symbol evidence; no image APIs or rendering."""
import argparse,io,re,sys,unicodedata
from pathlib import Path
from pypdf import PdfReader
from source_common import *
from king_acquire import inventory,URL
PAT=re.compile(r'\[SYMBOL ([0-9A-Fa-f]+)\]')
def run(source,pairs,out):
 src=Path(source).resolve();out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh output required; no automatic retries')
 out.mkdir(parents=True,exist_ok=True);base=load(src/'checkpoint.json');pair_raw=Path(pairs).read_bytes();pair=load(pairs);ids={r['source_document_id'] for r in pair['rows']};state={'schema':'king-source-pdf-symbol-check-1','source_url':URL,'started_at':stamp(),'source_inventory_sha256':sha(canon(base['inventory'])),'pair_proof_sha256':sha(pair_raw),'code_fingerprint':source_snapshot(out,['king_symbol_pdf.py','king_acquire.py','source_common.py','shared_transport.py']),'artifacts':[],'errors':[],'complete':False,'scope':'Source-offered alternate PDFs for actual symbol-bearing documents only; no primary full-Code acquisition claim','images_extracted':False,'image_apis_called':False};save(out/'checkpoint.json',state)
 try:
  raw,a=acquire(out,state,'index-start',URL)
  if inventory(raw)!=base['inventory']:raise ValueError('Current official index edition differs; no PDF acquisition')
  for d in base['inventory']:
   if d['id'] not in ids:continue
   observed=[x for x in d['native_alternatives'] if x['url'].lower().endswith('.pdf')]
   if len(observed)!=1:raise ValueError('Native PDF source absent/nonunique')
   raw,a=acquire(out,state,'native-symbol-pdf',observed[0]['url']);a['document_id']=d['id'];a['index_updated']=d['updated'];save(out/'checkpoint.json',state)
   if not raw.startswith(b'%PDF-') or not raw.strip().endswith(b'%%EOF'):raise ValueError('Native bytes are not a complete PDF')
   reader=PdfReader(io.BytesIO(raw),strict=True)
   if reader.is_encrypted or not reader.pages:raise ValueError('Unqualified encrypted/empty PDF')
   pages=[];fonts={}
   for pi,page in enumerate(reader.pages):
    text=page.extract_text(extraction_mode='plain') or '';pages.append({'page':pi+1,'text':text})
    fontmap=(page.get('/Resources') or {}).get('/Font')
    if fontmap:
     for name,obj in fontmap.get_object().items():
      font=obj.get_object();tu=font.get('/ToUnicode');data=tu.get_object().get_data() if tu else None;fid=sha(canon({'base':str(font.get('/BaseFont')),'encoding':str(font.get('/Encoding')),'cmap_sha':sha(data) if data else None}))
      if fid not in fonts:fonts[fid]={'base_font':str(font.get('/BaseFont')),'encoding':str(font.get('/Encoding')),'subtype':str(font.get('/Subtype')),'to_unicode_cmap_sha256':sha(data) if data else None,'to_unicode_cmap_text':data.decode('latin1') if data else None,'pages':[]}
      fonts[fid]['pages'].append(pi+1)
   full=clean(' '.join(p['text'] for p in pages));comparisons=[]
   for row in pair['rows']:
    if row['source_document_id']!=d['id']:continue
    chunks=PAT.split(row['word_literal']);expression=''.join(re.escape(v) if i%2==0 else '(.)' for i,v in enumerate(chunks));matches=list(re.finditer(expression,full,re.S));entry={'record_id':row['record_id'],'word_literal':row['word_literal'],'matches':len(matches),'variants':[],'qualified':False}
    if len(matches)==1:
     chars=matches[0].groups();entry['variants']=[{'word_code':chunks[2*i+1],'pdf_literal':char,'pdf_unicode':'U+'+format(ord(char),'04X'),'unicode_name':unicodedata.name(char,None),'private_or_control':unicodedata.category(char) in ['Co','Cc','Cs','Cn']} for i,char in enumerate(chars)];entry['matched_pdf_literal']=matches[0].group(0);entry['qualified']=False;entry['note']='Exact literal match retained; glyph/font encoding binding must be audited before semantic promotion'
    comparisons.append(entry)
   save(out/(d['heading'].split(':')[0].replace(' ','-')+'-pdf-text-fonts.json'),{'document_id':d['id'],'source_pdf_url':observed[0]['url'],'source_pdf_sha256':a['sha256'],'pages':pages,'fonts':fonts,'comparisons':comparisons,'image_apis_called':False})
   a.update(pdf_pages=len(pages),symbol_records=len(comparisons),exact_literal_matches=sum(c['matches']==1 for c in comparisons),pdf_fonts=len(fonts));save(out/'checkpoint.json',state);print(json.dumps({'heading':d['heading'],'bytes':len(raw),'pages':len(pages),'exact_literal_matches':a['exact_literal_matches'],'symbol_records':len(comparisons)}),flush=True)
  raw,a=acquire(out,state,'index-end',URL)
  if inventory(raw)!=base['inventory']:raise ValueError('PDF investigation closing index drift')
  state['opening_closing_inventory_equal']=True
 except Exception as e:state['errors'].append({'type':type(e).__name__,'message':str(e),'at':stamp()})
 state['finished_at']=stamp();save(out/'checkpoint.json',state);return state
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--pairs',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.source,a.pairs,a.out);print(json.dumps({'errors':r['errors'],'complete':False,'scope':r['scope']},indent=2));sys.exit(2 if not r['errors'] else 3)
