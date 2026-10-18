"""Acquire actual source-incorporated MRSC Appendix C route; no guessed upgrade/alternate URLs."""
import argparse,io,json,sys
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from bs4 import BeautifulSoup
from pypdf import PdfReader
from source_common import *
URL='http://www.mrsc.org/Publications/pra06.pdf'
def run(source,out):
 source=Path(source).resolve();out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh output required')
 out.mkdir(parents=True,exist_ok=True);state=load(source/'checkpoint.json');proof=[]
 for a in state['artifacts']:
  if a['role']!='content':continue
  raw=(source/a['path']).read_bytes()
  if sha(raw)!=a['sha256']:raise ValueError('Corrupt retained source')
  # Avoid opening unrelated documents; only source actually containing exact href qualifies.
  if URL.encode() not in raw:continue
  s=BeautifulSoup(decode(raw)[0],'html.parser')
  for link in s.find_all('a',href=URL):
   context=clean(link.parent.get_text(' ',strip=True))
   if 'incorporated in this chapter by reference' in context:proof.append({'source_url':a['source_url'],'source_sha256':a['sha256'],'context':context,'href':URL})
 if len(proof)!=1:raise ValueError('Exact incorporated source route not uniquely qualified')
 # The source explicitly uses HTTP. Request that exact public URL (no credentials),
 # while checking the same stopped-host/image prohibition without changing its request URL.
 p=urlsplit(URL);forbid(urlunsplit(('https',p.netloc,p.path,p.query,p.fragment)))
 fp=source_snapshot(out,['king_dependency.py','source_common.py','shared_transport.py']);raw,r=transport.fetch(URL);transport.atomic(out/'native.bin',raw);report={'source_binding':proof,'receipt':r,'path':'native.bin','complete':False,'images_extracted':False,'code_fingerprint':fp}
 if r['status']==200 and not r.get('access_stop') and raw.startswith(b'%PDF-'):
  pdf=PdfReader(io.BytesIO(raw),strict=True);text='\n'.join(page.extract_text() or '' for page in pdf.pages);report.update(pdf_pages=len(pdf.pages),appendix_c_label_found=bool(re.search(r'APPENDIX\s+C',text,re.I)),native_text_sha256=sha(text.encode()));report['complete']=report['appendix_c_label_found'];report['edition_complete']=False;report['limitation']='Source says most-recent statute list; edition identity must be established independently, no date/currentness inferred from200response'
 else:report['error']='Actual source-incorporated native document unavailable/unqualified; no alternate guessed URL or retry'
 save(out/'receipt.json',report);return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.source,a.out);print(json.dumps(r,indent=2));sys.exit(0 if r['complete'] and r.get('edition_complete') else 2)
