"""Bounded additional provision for substantive table/list/cross-reference quality QA."""
import json,sys,hashlib,shutil
from pathlib import Path
from municode_shared import fetch,api
from normalize import normalize
ROOT=Path(__file__).resolve().parents[1]
def run(name,index=0):
 c=next(x for x in json.loads((ROOT/'quality-candidates.json').read_text()) if x['jurisdiction'].lower().replace(' ','-')==name);n=c['candidates'][index];d=ROOT/c['folder'];r=json.loads((d/'receipt.json').read_text());samples=json.loads((d/'samples.json').read_text())
 if any(x['node']['Id']==n['id'] for x in samples):print('already retained',name,n['id']);return
 url=api('CodesContent',productId=r['product']['ProductID'],jobId=r['job']['Id'],nodeId=n['id'],groupChunks='false');b,rc=fetch(url,d/'quality-section.json');content=json.loads(b)
 if not (d/'samples-base.json').exists():shutil.copyfile(d/'samples.json',d/'samples-base.json')
 samples.append({'node':{'Id':n['id'],'Heading':n['heading'],'path':n['path']},'content':content});(d/'samples.json').write_text(json.dumps(samples,indent=2));r.setdefault('responses',[]).append({'url':url,'status':rc['http_status'],'file':'quality-section.json','sha256':rc['sha256']});r['quality_supplement']={'script':'scripts/quality_sample.py','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'node':n,'reason':'Substantive table/list/crossreference parser quality probe'};(d/'receipt.json').write_text(json.dumps(r,indent=2));print(name,normalize(d),flush=True)
if __name__=='__main__':run(sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 0)
