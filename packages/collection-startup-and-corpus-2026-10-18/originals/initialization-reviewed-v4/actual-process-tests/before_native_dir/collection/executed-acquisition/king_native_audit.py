"""Read-only native Word ZIP/HTML visible-body parity and independent edition audit."""
import argparse,collections,io,json,re,sys,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup
from source_common import *
from king_normalize import datevalue
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def fold(t):return re.sub(r'\s+|\u00ad|\u200b|\ufeff','',t).casefold()
def run(html_source,native_source):
 h=Path(html_source);n=Path(native_source);hs=load(h/'checkpoint.json');ns=load(n/'checkpoint.json');results=[];errors=[]
 if ns['errors'] or not ns.get('opening_closing_equal'):errors.append('Native acquisition failed/no equal closing')
 for d in hs['inventory']:
  ha=[a for a in hs['artifacts'] if a['role']=='content' and a['source_url']==d['url'] and a['status']==200];na=[a for a in ns['artifacts'] if a['role']=='native-word' and a.get('document_id')==d['id'] and a['status']==200]
  if len(ha)!=1 or len(na)!=1:errors.append('Missing/duplicate paired native source '+d['url']);continue
  hb=(h/ha[0]['path']).read_bytes();nb=(n/na[0]['path']).read_bytes()
  if sha(hb)!=ha[0]['sha256'] or sha(nb)!=na[0]['sha256']:raise ValueError('Corrupt retained paired source')
  with zipfile.ZipFile(io.BytesIO(nb)) as z:
   if z.testzip():raise ValueError('Native Word CRC failure')
   tree=ET.fromstring(z.read('word/document.xml'));native_text=''.join(x.text or '' for x in tree.findall('.//w:t',NS));native_tables=len(tree.findall('.//w:tbl',NS));paragraphs=[clean(''.join(x.text or '' for x in p.findall('.//w:t',NS))) for p in tree.findall('.//w:p',NS)]
  text,encoding=decode(hb);bs=BeautifulSoup(text,'html.parser');body=bs.body
  for x in body.select('script,style'):x.decompose()
  html_text=body.get_text();nf=fold(native_text);hf=fold(html_text);same=nf==hf
  # Difference counts do not waive exact parity. Keep compact diagnostic token multisets.
  nc=collections.Counter(re.findall(r'\w+',native_text.casefold()));hc=collections.Counter(re.findall(r'\w+',html_text.casefold()))
  updated=[p for p in paragraphs if p.upper().startswith('UPDATED')];dates=[datevalue(p) for p in updated];index_date=datevalue(d['updated']);conflict=bool(dates and index_date not in dates)
  result={'document_id':d['id'],'heading':d['heading'],'html_url':d['url'],'native_url':na[0]['source_url'],'html_sha256':sha(hb),'native_sha256':sha(nb),'html_fold_sha256':sha(hf.encode()),'native_fold_sha256':sha(nf.encode()),'exact_visible_body_parity':same,'html_characters':len(hf),'native_characters':len(nf),'html_tables':len(body.find_all('table')),'native_tables':native_tables,'native_updated_markers':updated,'index_updated':d['updated'],'index_native_date_conflict':conflict,'native_extra_tokens':list((nc-hc).items())[:40],'html_extra_tokens':list((hc-nc).items())[:40]};results.append(result)
  if not same:errors.append('HTML/native body parity mismatch '+d['url'])
  if len(body.find_all('table'))!=native_tables:errors.append('HTML/native table count mismatch '+d['url'])
  if conflict:errors.append('Index/native date conflict '+d['url'])
 return {'schema':'king-paired-source-audit-1','complete':not errors,'html_documents':len(hs['inventory']),'paired_documents':len(results),'exact_visible_body_parity_documents':sum(x['exact_visible_body_parity'] for x in results),'index_native_date_conflicts':sum(x['index_native_date_conflict'] for x in results),'documents':results,'errors':errors,'images_extracted':False,'scope':'Source Word document.xml text/table parity; native image binaries remain inside original publisher ZIP, never extracted/read'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--html-source',required=True);p.add_argument('--native-source',required=True);p.add_argument('--out');a=p.parse_args();r=run(a.html_source,a.native_source)
 if a.out:save(Path(a.out),r)
 print(json.dumps({k:v for k,v in r.items() if k!='documents'},indent=2));sys.exit(0 if r['complete'] else 2)
