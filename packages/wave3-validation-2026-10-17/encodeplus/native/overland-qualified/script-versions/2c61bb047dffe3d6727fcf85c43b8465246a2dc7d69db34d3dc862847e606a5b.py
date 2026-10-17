#!/usr/bin/env python3
"""Continue the observed enCodePlus Export PDF status page through its public polling flow."""
import argparse,json,pathlib,re,sys,platform,shutil,time,datetime
from urllib.parse import urljoin,urlencode
from transport import fetch
from parse import decode,sha
from pypdf import PdfReader

def run(landing,out):
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh export output must be unpopulated')
 out.mkdir(parents=True,exist_ok=True);snap=out/'script-versions';snap.mkdir();versions={}
 for name in ['native_export.py','parse.py','html_semantics.py','transport.py']:
  p=pathlib.Path(__file__).with_name(name);h=sha(p.read_bytes());shutil.copy2(p,snap/(h+p.suffix));versions[name]=h
 meta=json.loads(landing.with_name(landing.name+'.receipt.json').read_text());raw=landing.read_bytes();assert sha(raw)==meta['sha256'];html=decode(raw,meta['headers']);url=meta['url']
 report={'command':sys.argv,'runtime':platform.python_version(),'os':platform.platform(),'script_versions':versions,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_landing':str(landing),'source_landing_sha256':sha(raw),'source_url':url,'scope':'Selected operative table provision only; not full publication','complete_corpus':False}
 try:
  m=re.search(r"\$\.get\('([^']+)'",html);assert m,'No observed export polling URL';poll=urljoin(url,m.group(1))
  report['polling_url']=poll
  for i in range(3):
   data,rec=fetch(poll,out/('poll-'+str(i)+'.json'));state=json.loads(decode(data,rec['headers']));assert not state.get('Failed'),state.get('Msg')
   if state.get('Ready'):break
   time.sleep(4)
  else:raise ValueError('Native export not ready within three bounded publisher polls')
  download=url+('&' if '?' in url else '?')+urlencode({'file':state['File']});data,rec=fetch(download,out/'publisher.pdf');assert data.startswith(b'%PDF-'),'Non-PDF final response'
  reader=PdfReader(out/'publisher.pdf');text='\n'.join(p.extract_text() for p in reader.pages);(out/'publisher-text.txt').write_text(text)
  report.update(status='passed',url=download,pdf_sha256=sha(data),pdf_bytes=len(data),pages=len(reader.pages),metadata={str(k):str(v) for k,v in reader.metadata.items()},text_sha256=sha(text.encode()))
 except Exception as e:report.update(status='blocked',error=str(e))
 report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(out/'export.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('landing',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();print(json.dumps(run(a.landing,a.out),indent=2))
