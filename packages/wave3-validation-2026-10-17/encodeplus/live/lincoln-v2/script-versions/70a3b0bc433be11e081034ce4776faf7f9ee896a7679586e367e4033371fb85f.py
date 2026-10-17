#!/usr/bin/env python3
"""Three provision sample (two general provisions + one observed operative table); not full ingestion."""
import argparse,pathlib,json,sys,platform,datetime,shutil,hashlib
from urllib.parse import urlencode
from transport import fetch
from parse import decode,inventory,parse_section,write_outputs,sha
ROOT=pathlib.Path(__file__).resolve().parents[1]
CONFIG={'lincoln':{'identity':'Lincoln, NE Municipal Code','jurisdiction':'Lincoln, NE','base':'https://online.encodeplus.com/regs/lincoln-ne/','nodes':['6288','6289','12858']},'overland':{'identity':'Overland Park, Kansas Municipal Code','jurisdiction':'Overland Park, KS','base':'https://codes.opkansas.org/municipal-code/','nodes':['3','4','6155']}}
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def run(key,out,offline=False):
 cfg=CONFIG[key];records=[];checks=[]
 if not offline:
  if out.exists() and any(out.iterdir()):raise ValueError('Fresh live output directory must be unpopulated')
  out.mkdir(parents=True,exist_ok=True);snap=out/'script-versions';snap.mkdir();versions={}
  for name in ['acquire.py','parse.py','html_semantics.py','transport.py']:
   p=ROOT/'scripts'/name;h=sha(p.read_bytes());shutil.copy2(p,snap/(h+p.suffix));versions[name]=h
  report={'jurisdiction':cfg['jurisdiction'],'source_url':cfg['base'],'method':'standalone-python-public-server-rendered-enCodePlus-HTML','started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':sys.argv,'runtime':platform.python_version(),'os':platform.platform(),'script_versions':versions,'complete_corpus':False,'publisher_download':{'status':'not_tested','format':'PDF','reason':'Acquisition not yet reached export step'}}
 else:report=json.loads((out/'run.json').read_text())
 try:
  if not offline:fetch(cfg['base']+'doc-view.aspx',out/'toc.html')
  tr=json.loads((out/'toc.html.receipt.json').read_text());toc=inventory(decode((out/'toc.html').read_bytes(),tr['headers']),cfg['base'],cfg['identity']);dump(out/'inventory.json',toc)
  nodes={n['section_id']:n for n in toc['nodes']};tocid=None
  for nodeid in cfg['nodes']:
   assert nodeid in nodes,'Selected node not observed in independent TOC';url=cfg['base']+'doc-view.aspx?'+urlencode({'secid':nodeid,'ajax':0});raw=out/('section-'+nodeid+'.html')
   if not offline:fetch(url,raw)
   meta=json.loads(raw.with_name(raw.name+'.receipt.json').read_text());assert sha(raw.read_bytes())==meta['sha256'];r,c,tid=parse_section(decode(raw.read_bytes(),meta['headers']),nodes[nodeid],url,cfg['jurisdiction'],meta['sha256']);records.append(r);checks.append(c);tocid=tid
  assert records[-1]['tables'],'Observed operative table sample did not contain a table'
  validation=write_outputs(records,checks,out/'normalized');report.update(validation,status='standalone_e2e_pass',selected_nodes=cfg['nodes'],inventory_nodes=toc['node_count'])
  if not offline:
   pdfurl=cfg['base']+'export2doc.aspx?'+urlencode({'pdf':1,'tocid':tocid})
   try:
    data,pr=fetch(pdfurl,out/'publisher-table-export.pdf')
    assert data.startswith(b'%PDF-'),'Publisher export response is not PDF'
    report['publisher_download']={'status':'passed','format':'PDF','url':pdfurl,'reason':'Visible publisher Export PDF function; server-generated original PDF for the selected table provision, not browser print','scope':'Only '+records[-1]['heading'],'bytes':len(data),'sha256':pr['sha256']}
   except Exception as e:report['publisher_download']={'status':'blocked','format':'PDF','url':pdfurl,'reason':str(e),'scope':'Selected table provision only'}
 except Exception as e:
  if offline:raise
  report.update(status='blocked',error=str(e),record_count=len(records),table_count=sum(len(r['tables']) for r in records))
 if not offline:report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(out/'run.json',report)
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('target',choices=CONFIG);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--offline',action='store_true');a=p.parse_args();print(json.dumps(run(a.target,a.out,a.offline),indent=2))
