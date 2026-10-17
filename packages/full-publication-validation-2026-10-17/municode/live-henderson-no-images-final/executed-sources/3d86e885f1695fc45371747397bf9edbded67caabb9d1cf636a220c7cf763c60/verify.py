"""Read-only offline verifier: raw hashes, identity binding, inventory/ownership/assets and deterministic outputs."""
import sys
sys.dont_write_bytecode=True
import argparse,json,tempfile
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from model import sha,digest,canonical,read_response,reconcile_publication,write_outputs

def verify(folder,allow_incomplete=False):
 folder=Path(folder);cp=json.loads((folder/'checkpoint.json').read_text());checks=0
 def check(ok,message):
  nonlocal checks
  if not ok:raise ValueError(message)
  checks+=1
 check(cp['schema_version']==1,'Unsupported checkpoint schema')
 for name,h in cp['binding']['implementation'].items():check(sha((folder/'executed-sources'/h/name).read_bytes())==h,'Executed source snapshot mismatch '+name)
 for entry in cp['responses']:
  receipt=json.loads((folder/entry['receipt']).read_text());body=(folder/receipt['body_file']).read_bytes();check(sha(body)==entry['sha256']==receipt['sha256'],'Raw response corruption');check(receipt['request']==entry['request'],'Receipt/request mismatch')
 for name,entry in cp['units'].items():
  receipt=json.loads((folder/entry['receipt']).read_text());check(receipt['status']==200 and not receipt.get('access_stop'),'Failed response accepted as committed source')
 for pid,pub in cp['publications'].items():
  checks_before=checks;product=read_response(folder,cp['units'][pub['product_unit']])['Model'];job=read_response(folder,cp['units'][pub['job_unit']]);q=parse_qs(urlparse(cp['units'][pub['product_unit']]['request']['url']).query);check(q.get('clientId')==[str(cp['client_id'])],'Product request client mismatch');check(product['ProductID']==int(pid) and job['ProductId']==int(pid) and job['Id']==pub['job_id'],'Product/job identity mismatch');check(product['Client']['ClientName'] in cp['expected_identity']['client_names'] and product['Client']['State']['StateAbbreviation']==cp['expected_identity']['state'],'Jurisdiction mismatch');check(not product.get('ExternalCodeLink'),'External migration cannot pass');tq=parse_qs(urlparse(cp['units'][pub['toc_unit']]['request']['url']).query);check(tq.get('productId')==[pid] and tq.get('jobId')==[str(pub['job_id'])],'TOC request edition mismatch')
  records,report=reconcile_publication(folder,cp,pid);stored=json.loads((folder/'publications'/pid/'coverage.json').read_text());check(report==stored,'Coverage recomputation mismatch '+pid);check(not report['duplicate_ids'] and not report['extra_ids'],'Duplicate/extra source ownership');check(not report['errors'],'Publication parse/identity errors')
 with tempfile.TemporaryDirectory() as tmp:
  # Recompute without touching retained evidence. Raw source references are copied via read-only filesystem symlinks.
  temp=Path(tmp);(temp/'raw').symlink_to((folder/'raw').resolve(),target_is_directory=True);overall=write_outputs(temp,cp)
  for pid in cp['publications']:
   for name in ['sections.jsonl','sections.csv','coverage.json']:check((temp/'publications'/pid/name).read_bytes()==(folder/'publications'/pid/name).read_bytes(),'Normalized output differs from replay '+pid+'/'+name)
  check(json.loads((folder/'coverage.json').read_text())==overall,'Overall coverage mismatch')
 check(overall['jurisdiction_complete'] is False,'Unproved jurisdiction completeness')
 if not allow_incomplete:check(overall['publication_complete'],'Full publication scope incomplete')
 return {'passed':True,'checks':checks,'network_requests':0,'package_writes':False,'record_count':overall['record_count'],'publication_complete':overall['publication_complete'],'publication_text_complete':overall['publication_text_complete'],'publication_attachments_complete':overall['publication_attachments_complete'],'jurisdiction_complete':False,'phase':cp['phase']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--offline',action='store_true');p.add_argument('--allow-incomplete',action='store_true',help='Verify retained evidence without claiming completion');a=p.parse_args()
 try:print(json.dumps(verify(a.folder,a.allow_incomplete),indent=2))
 except Exception as e:print(str(e),file=sys.stderr);raise SystemExit(2)
