#!/usr/bin/env python3
"""Bounded current Fairfax County zoning alternative via ordinary server-rendered publisher endpoints."""
import argparse,datetime,hashlib,json,re,shutil,sys
from pathlib import Path
from bs4 import BeautifulSoup
from encodeplus_transport import fetch
from encode_parse import decode,parse_section,write_outputs
ROOT=Path(__file__).resolve().parents[1]
HOST='https://online.encodeplus.com/regs/fairfaxcounty-va/'
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def acquire(out):
 assert not out.exists(),'Use a new output directory';out.mkdir(parents=True);versions=out/'script-versions';versions.mkdir();
 for fn in ['fairfax_encode.py','encodeplus_transport.py','encode_parse.py','html_semantics.py']:
  p=ROOT/'scripts'/fn;shutil.copy2(p,versions/(hashlib.sha256(p.read_bytes()).hexdigest()+p.suffix))
 rec={'jurisdiction':'Fairfax County','state':'VA','publication':'Fairfax County Zoning Ordinance (Chapter112.2)','primary_county_code_scope':False,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'ordinary Python HTTP server-rendered publisher HTML, shared enCodePlus gate','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'runtime':sys.version,'complete_corpus':False,'publisher_download':{'status':'not_tested'}}
 try:
  root,r=fetch(HOST+'doc-view.aspx?ajax=0&secid=2214',out/'root.html');html=decode(root,r['headers']);soup=BeautifulSoup(html,'html.parser');assert 'Fairfax County Zoning Ordinance' in soup.get_text(' ',strip=True),'County/publication identity mismatch';page=soup.select_one('#thePage');assert page and page.get('secid')=='2214';records=[];checks=[]
  for sid in ['2218','2219','2230']:
   section=soup.select_one('section[data-secid="'+sid+'"]');assert section,'Observed node absent';h=section.find(re.compile(r'^h[1-6]$'));heading=' '.join(h.get_text(' ',strip=True).split());node={'section_id':sid,'heading':heading,'path':['Fairfax County Zoning Ordinance']};url=HOST+'doc-view.aspx?ajax=0&secid='+sid;data,rr=fetch(url,out/('section-'+sid+'.html'));record,check,tocid=parse_section(decode(data,rr['headers']),node,url,'Fairfax County',rr['sha256']);records.append(record);checks.append(check)
   if sid=='2230':rec['table_node']={'section_id':sid,'heading':heading,'tocid':tocid}
  rec['selected_nodes']=[{'section_id':r['section_id'],'heading':r['heading'],'source_url':r['source_url']} for r in records];rec['normalization']=write_outputs(records,checks,out/'parsed');assert rec['normalization']['table_count']>0,'No operative HTML table'
  # Native PDF endpoint is the publisher's observed OpenPDF action, not browser print.
  data,r=fetch(HOST+'export2doc.aspx?pdf=1&tocid='+rec['table_node']['tocid'],out/'publisher-section.pdf');rec['publisher_download']={'status':'passed' if data.startswith(b'%PDF-') else 'partial','url':r['final_url'],'bytes':len(data),'sha256':r['sha256'],'scope':rec['table_node'],'reason':'Publisher OpenPDF action; actual bytes retained. PDF parsing/edition comparison recorded separately.'};rec['status']='acquired'
 except Exception as e:rec.update(status='partial',error=str(e))
 rec['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(out/'receipt.json',rec);return rec
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=acquire(a.out);print(json.dumps({'status':r['status'],'error':r.get('error'),'publisher_download':r['publisher_download']},ensure_ascii=False))
