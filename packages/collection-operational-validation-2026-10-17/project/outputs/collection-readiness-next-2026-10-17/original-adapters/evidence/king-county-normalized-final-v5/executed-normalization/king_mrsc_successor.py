"""Source-evidenced current MRSC publication route discovery, no guessed old-path replacement."""
import argparse,io,re,sys
from pathlib import Path
from urllib.parse import urljoin
from pypdf import PdfReader
from source_common import *
INDEX='https://mrsc.org/publications'
def run(out):
 out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh output required')
 out.mkdir(parents=True,exist_ok=True);state={'artifacts':[],'errors':[],'source_url':INDEX,'complete':False,'code_fingerprint':source_snapshot(out,['king_mrsc_successor.py','source_common.py','shared_transport.py'])};save(out/'checkpoint.json',state)
 try:
  raw,a=acquire(out,state,'publisher-index',INDEX);s=BeautifulSoup(decode(raw)[0],'html.parser');heads=[h for h in s.find_all(['h2','h3','h4']) if 'Public Records Act for Washington Cities' in clean(h.get_text(' ',strip=True))]
  if len(heads)!=1:raise ValueError('Current publisher publication title absent/nonunique')
  heading=heads[0];context=[];links=[]
  for sib in heading.next_siblings:
   if getattr(sib,'name',None) in ['h2','h3','h4']:break
   if getattr(sib,'get_text',None):context.append(clean(sib.get_text(' ',strip=True)))
   if getattr(sib,'select',None):links.extend(urljoin(INDEX,x['href']) for x in sib.select('a[href]'))
  candidates=list(dict.fromkeys(u for u in links if '/getmedia/' in u and ('pdf' in u.lower())))
  if len(candidates)!=1:raise ValueError('Actual publisher PDF route absent/nonunique')
  state['publisher_label']=clean(heading.get_text(' ',strip=True));state['publisher_context']=' '.join(context);state['native_url']=candidates[0];raw,a=acquire(out,state,'publisher-native-pdf',candidates[0])
  if not raw.startswith(b'%PDF-'):raise ValueError('Publisher native bytes not PDF')
  pdf=PdfReader(io.BytesIO(raw),strict=True);text='\n'.join(page.extract_text() or '' for page in pdf.pages);state.update(pdf_pages=len(pdf.pages),source_pdf_sha256=sha(raw),appendix_c=bool(re.search(r'Appendix\s+C',text,re.I)),december_2025=bool(re.search(r'DECEMBER\s+2025',text,re.I)),native_text_sha256=sha(text.encode()),images_extracted=False,native_transport_qualified=True,adoption_binding_complete=False,scope='Current MRSC native publication from current publisher list; prior King County incorporation points to a404 oldroute. Dynamic most-recent-list binding requires explicit source-scope reconciliation; new publication is not automatically substituted.')
 except Exception as e:state['errors'].append({'type':type(e).__name__,'message':str(e)})
 save(out/'checkpoint.json',state);return state
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();r=run(a.out);print(json.dumps(r,indent=2));sys.exit(2)
