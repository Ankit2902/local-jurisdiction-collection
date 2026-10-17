"""Offline normalize an independently acquired observed API node, pinned to primary TOC/job."""
import argparse,json
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from normalize import normalize
p=argparse.ArgumentParser();p.add_argument('primary',type=Path);p.add_argument('supplemental',type=Path);a=p.parse_args();acq=json.loads((a.supplemental/'acquisition-receipt.json').read_text());primary=json.loads((a.primary/'receipt.json').read_text());assert acq['status']=='acquired';q=parse_qs(urlparse(acq['api_url']).query);nodeid=q['nodeId'][0];assert q['productId'][0]==str(primary['product']['ProductID']) and q['jobId'][0]==str(primary['job']['Id'])
found=[]
def walk(n,parents=[]):
 if n.get('Id')==nodeid:found.append({**n,'path':parents+[n['Heading']]})
 for c in n.get('Children',[]):walk(c,parents+[n['Heading']])
walk(json.loads((a.primary/'toc-full.json').read_text()));assert len(found)==1
(a.supplemental/'samples.json').write_text(json.dumps([{'node':found[0],'content':json.loads((a.supplemental/'content.json').read_text())}],indent=2));receipt={**primary,'url':primary['url'],'started_at':acq['started_at'],'finished_at':acq['finished_at'],'method':'standalone-headed-chrome-single-observed-legal-node','selected_nodes':[{'id':found[0]['Id'],'heading':found[0]['Heading']}],'acquisition_receipt':'acquisition-receipt.json','script_sha256':acq['script_sha256'],'status':'acquired','publisher_download':{'status':'not_tested','reason':'Supplemental single legal node; primary download tested separately'},'responses':[]};(a.supplemental/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(normalize(a.supplemental),indent=2))
