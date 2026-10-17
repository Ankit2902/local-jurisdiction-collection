#!/usr/bin/env python3
"""One observed Des Moines rate schedule provision; native table QA as a separate bounded sample."""
import json,pathlib,hashlib,shutil,argparse,datetime
from municode_shared import get_json,api
from normalize import normalize
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');p.add_argument('--node-id',default='MUCO_CH98SOWA_ARTIIIDIFA_S98-146SCRA');p.add_argument('--output-name',default='des_moines-rate-table');a=p.parse_args();src=ROOT/'direct/des_moines-ia';out=ROOT/'supplemental'/a.output_name;out.mkdir(parents=True,exist_ok=True)
nodeid=a.node_id;tree=json.loads((src/'toc-full.json').read_text());found=[]
def walk(n,path=[]):
 if n.get('Id')==nodeid:found.append({**n,'path':path+[n['Heading']]})
 for c in n.get('Children') or[]:walk(c,path+[n.get('Heading','')])
walk(tree);assert len(found)==1;product=json.loads((src/'product.json').read_text());job=json.loads((src/'job.json').read_text())
raw=out/'content.json';receipt={'url':'https://library.municode.com/ia/des_moines/codes/code_of_ordinances','product':product,'job':job,'status':'acquired','script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'method':'standalone-python-public-api-observed-TOC-table-supplement','complete_corpus':False}
if not a.offline:
 versions=out/'script-versions';versions.mkdir(exist_ok=True)
 for name in ['table_sample.py','normalize.py','municode_shared.py']:
  p=ROOT/'scripts'/name;shutil.copy2(p,versions/(hashlib.sha256(p.read_bytes()).hexdigest()+p.suffix))
 payload=get_json(api('CodesContent',productId=product['ProductID'],jobId=job['Id'],nodeId=nodeid,groupChunks='false'),raw)
 (out/'samples.json').write_text(json.dumps([{'node':found[0],'content':payload}],indent=2));(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
r=normalize(out);rows=[json.loads(x) for x in (out/'normalized/sections.jsonl').read_text().splitlines()];record=rows[0];soup=BeautifulSoup(record['html'],'html.parser');tables=soup.find_all('table');assert len(tables)==len(record['tables']);checks=[]
for source,normalized in zip(tables,record['tables']):
 trs=source.find_all('tr');assert len(trs)==len(normalized)
 for tr,nrow in zip(trs,normalized):
  cells=tr.find_all(['td','th']);assert len(cells)==len(nrow)
  for cell,ncell in zip(cells,nrow):
   assert str(cell.get('rowspan','1'))==ncell['rowspan'];assert str(cell.get('colspan','1'))==ncell['colspan'];assert ' '.join(cell.get_text(' ',strip=True).split())==' '.join(ncell['text'].split())
 checks.append({'rows':len(trs),'cells':sum(len(x) for x in normalized),'spans_and_text_match_independent_html_parser':True})
report={'passed':bool(tables),'record_count':1,'table_count':len(tables),'checks':checks,'scope':'Exactly one observed current job node '+nodeid+'; no broad structural claim','raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest()};(out/'table-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
