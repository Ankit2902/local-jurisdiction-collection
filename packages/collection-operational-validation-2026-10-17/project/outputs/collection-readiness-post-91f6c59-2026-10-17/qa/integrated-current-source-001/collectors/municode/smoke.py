"""Explicit single-node live smoke against an observed retained TOC. Never publication-level proof."""
import sys
sys.dont_write_bytecode=True
import argparse,json,base64
from pathlib import Path
from model import atomic,sha,implementation,read_response,flatten,asset_qualification
from collect import Browser,api
from normalize import normalize
p=argparse.ArgumentParser();p.add_argument('--reference-run',type=Path,required=True);p.add_argument('--node-id',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
if a.out.exists() and any(a.out.iterdir()):raise SystemExit('Fresh smoke output required')
a.out.mkdir(parents=True,exist_ok=True);cp=json.loads((a.reference_run/'checkpoint.json').read_text())
if len(cp['publications'])!=1:raise SystemExit('One reference publication required')
pid,pub=next(iter(cp['publications'].items()));nodes=flatten(read_response(a.reference_run,cp['units'][pub['toc_unit']]));node=next(n for n in nodes if n['id']==a.node_id)
product=read_response(a.reference_run,cp['units'][pub['product_unit']])['Model'];browser=Browser(cp['source_url'],a.out);responses=[]
try:
 def fetch(name,url):
  r=browser.request(url);response=r['response'];body=base64.b64decode(response.pop('body'));atomic(a.out/(name+'.json'),body);responses.append({'name':name,'request_url':url,'status':response['status'],'access_stop':r.get('access_stop'),'sha256':sha(body),'bytes':len(body),'headers':response['headers']})
  if response['status']!=200 or r.get('access_stop'):raise ValueError('Live smoke access failure')
  return json.loads(body)
 from urllib.parse import urlparse
 parts=urlparse(cp['source_url']).path.split('/');org=fetch('organization','https://library.municode.com/localapi/Organizations/GetByUrlEncodedNames/'+parts[1]+'/'+parts[2]);assert org['ClientID']==cp['client_id'] and org['ClientName'] in cp['expected_identity']['client_names'] and org['State']['StateAbbreviation']==cp['expected_identity']['state']
 job=fetch('job',api('Jobs/latest/'+pid));assert job['ProductId']==int(pid) and job['Id']==pub['job_id']
 content=fetch('content',api('CodesContent',productId=pid,jobId=job['Id'],nodeId=a.node_id,groupChunks='false'));assert len([d for d in content.get('Docs',[]) if d.get('Id')==a.node_id])==1
 atomic(a.out/'samples.json',[{'node':{'Id':node['id'],'Heading':node['heading'],'path':node['path']},'content':content}]);atomic(a.out/'receipt.json',{'status':'acquired','access_stop':None,'product':product,'job':job,'url':cp['source_url']});report=normalize(a.out)
 hashes=implementation();hashes['smoke.py']=sha(Path(__file__).read_bytes())
 for name,h in hashes.items():atomic(a.out/'executed-sources'/h/name,(Path(__file__).parent/name).read_bytes())
 result={'passed':True,'scope':'single observed legal node; not full-publication live proof','complete_corpus':False,'node_id':a.node_id,'product_id':int(pid),'job_id':job['Id'],'current_implementation':hashes,'normalization':report,'responses':responses,'binary_acquisition_requests':0,'PDF_prefix_rejected':asset_qualification('https://example.test/required.pdf',b'%PDF-1.4',{'content-type':'application/pdf'})[0]=='failed','PDF_spoof_rejected':asset_qualification('https://example.test/required.pdf',b'%PDF-1.4\nnot parsed\n%%EOF',{'content-type':'application/pdf'})[0]=='failed'};assert result['PDF_prefix_rejected'] and result['PDF_spoof_rejected'];atomic(a.out/'smoke-result.json',result);print(json.dumps(result,indent=2))
finally:browser.close()
