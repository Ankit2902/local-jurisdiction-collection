"""Targeted official native Charter alternative check for an HTML/Word empty source unit."""
import argparse,io,json,re,sys
from pathlib import Path
from pypdf import PdfReader
from source_common import *
from king_acquire import URL

def run(source,out):
 src=Path(source).resolve();out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh output required')
 out.mkdir(parents=True,exist_ok=True);base=load(src/'checkpoint.json')
 if base['source_url']!=URL:raise ValueError('Wrong official source identity')
 docs=[d for d in base['inventory'] if d['kind']=='charter']
 if len(docs)!=1:raise ValueError('Official Charter identity absent/nonunique')
 routes=[a for a in docs[0]['native_alternatives'] if a['url'].endswith('.pdf')]
 if len(routes)!=1:raise ValueError('Native PDF alternative absent/nonunique')
 state={'source_url':routes[0]['url'],'source_binding':docs[0],'source_inventory_sha256':base['inventory_sha256'],'artifacts':[],'errors':[],'complete':False,'scope':'Targeted alternate-format identity/body check for Charter650.40, not complete County Code or PDF table/text qualification','code_fingerprint':source_snapshot(out,['king_charter_pdf.py','king_acquire.py','source_common.py','shared_transport.py'])};save(out/'checkpoint.json',state)
 try:
  raw,a=acquire(out,state,'native-charter-pdf',routes[0]['url'])
  if not raw.startswith(b'%PDF-'):raise ValueError('Original publisher alternative is not PDF')
  pdf=PdfReader(io.BytesIO(raw),strict=True);contexts=[];alltext=[]
  for no,page in enumerate(pdf.pages,1):
   text=page.extract_text() or '';alltext.append(text)
   for m in re.finditer(r'650\s*\.\s*40',text):contexts.append({'page':no,'offset':m.start(),'context':text[max(0,m.start()-180):m.start()+1800]})
  state.update(pdf_pages=len(pdf.pages),target_contexts=contexts,text_sha256=sha('\n'.join(alltext).encode()),images_extracted=False,native_transport_qualified=True)
 except Exception as e:state['errors'].append({'type':type(e).__name__,'message':str(e)})
 save(out/'checkpoint.json',state);return state
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.source,a.out);print(json.dumps(r,indent=2));sys.exit(2)
