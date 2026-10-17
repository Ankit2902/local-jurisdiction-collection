"""Read-only deterministic offline verification. No network; normalization goes to temp directories."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,hashlib,json,re,tempfile
from urllib.parse import urlparse,parse_qs
from pathlib import Path
from normalize import normalize
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok,message):
 if not ok:raise AssertionError(message)
 return 1
def verify(root):
 count=0;rows=json.loads((root/'results.json').read_text());assigned=json.loads((root/'assignment.json').read_text());count+=check({r['sequence'] for r in rows}=={r['sequence'] for r in assigned} and len(rows)==len(assigned),'Assignment coverage')
 for r in rows:
  ar=next(x for x in assigned if x['sequence']==r['sequence']);count+=check(ar['jurisdiction']==r['jurisdiction'] and ar['state']==r['state'],'Assignment jurisdiction/state')
  count+=check(r['complete_corpus'] is False,'Bounded scope');count+=check(all((root/p).exists() for p in r['evidence_paths']+r['script_paths']),'Evidence/script paths')
  if r['status']!='standalone_e2e_pass':continue
  folder=root/r['primary_path'];receipt=json.loads((folder/'receipt.json').read_text());prod=receipt['product'];job=receipt['job'];target=next(x for x in json.loads((root/'targets.json').read_text()) if x['sequence']==r['sequence']);count+=check(receipt['status']=='acquired' and not receipt.get('access_stop'),'Completed acquisition without access stop');count+=check(prod['Client']['State']['StateAbbreviation']==r['state'] and prod['Client']['ClientName'] in target['expected_client_names'],'Jurisdiction identity');count+=check(job['ProductId']==prod['ProductID'] and not prod.get('ExternalCodeLink'),'Publication/job identity');count+=check(sha(folder/'executed-collect_browser.cjs')==receipt['script_sha256'],'Executed collector bytes');count+=check(sha(folder/'executed-gate_cli.py')==receipt['gate_script_sha256'],'Executed gate bytes')
  for response in receipt['responses']:
   count+=check(sha(folder/response['file'])==response['sha256'],'Raw response hash')
  def retained_json_matches(api_path,value,params=None,model=False):
   for response in receipt['responses']:
    u=urlparse(response['url']);q=parse_qs(u.query)
    if response['status']!=200 or u.path.lower()!=api_path.lower():continue
    if params and any(q.get(k)!=[str(v)] for k,v in params.items()):continue
    payload=json.loads((folder/response['file']).read_text())
    if (payload.get('Model') if model else payload)==value:return True
   return False
  count+=check(retained_json_matches('/api/Products/name',prod,{'clientId':prod['Client']['ClientID']},True),'Product metadata raw response binding')
  count+=check(retained_json_matches('/api/Jobs/latest/'+str(prod['ProductID']),job),'Latest-job raw response binding')
  count+=check(retained_json_matches('/api/codesToc/fullTree',json.loads((folder/'toc-full.json').read_text()),{'productId':prod['ProductID'],'jobId':job['Id']}),'Pinned TOC raw response binding')
  samples=json.loads((folder/'samples.json').read_text())
  for sample in samples:
   matches=[]
   for response in receipt['responses']:
    u=urlparse(response['url']);q=parse_qs(u.query)
    if u.path.lower()=='/api/codescontent' and q.get('productId')==[str(prod['ProductID'])] and q.get('jobId')==[str(job['Id'])] and q.get('nodeId')==[sample['node']['Id']] and response['status']==200:matches.append(response)
   count+=check(any(json.loads((folder/m['file']).read_text())==sample['content'] for m in matches),'Samples bound to exact retained live API response')
  cc=json.loads((folder/'client-content.json').read_text());count+=check(retained_json_matches('/api/ClientContent/'+str(prod['Client']['ClientID']),cc),'ClientContent raw response binding');count+=check(any(c['productId']==prod['ProductID'] and not c.get('hideInLibrary') for c in cc['codes']),'Visible publication')
  replayed_records=0;replayed_tables=0
  for d in [folder]+[root/p for p in r.get('supplemental_paths',[])]:
   if d!=folder:
    acq=json.loads((d/'acquisition-receipt.json').read_text());content=json.loads((d/'content.json').read_text());ss=json.loads((d/'samples.json').read_text());q=parse_qs(urlparse(acq['api_url']).query)
    count+=check(acq['status']=='acquired' and not acq.get('access_stop') and acq['response']['status']==200,'Supplemental live acquisition success')
    count+=check(sha(d/'content.json')==acq['response']['sha256'] and len(ss)==1 and ss[0]['content']==content,'Supplemental raw content binding')
    count+=check(q.get('productId')==[str(prod['ProductID'])] and q.get('jobId')==[str(job['Id'])] and q.get('nodeId')==[ss[0]['node']['Id']],'Supplemental publication/job/node binding')
    count+=check(sha(d/'executed-acquire_node.cjs')==acq['script_sha256'],'Supplemental executed source')
    found=[]
    def walk(n):
     if n.get('Id')==ss[0]['node']['Id']:found.append(n)
     for c in n.get('Children',[]):walk(c)
    walk(json.loads((folder/'toc-full.json').read_text()));count+=check(len(found)==1 and found[0]['Heading']==ss[0]['node']['Heading'],'Supplemental observed TOC membership')
   with tempfile.TemporaryDirectory() as tmp:
    report=normalize(d,Path(tmp));replayed_records+=report['record_count'];replayed_tables+=report['table_count'];count+=check(report['record_count']>0,'Nonempty legal sample')
    for name in ['sections.jsonl','sections.csv','verification.json']:count+=check((Path(tmp)/name).read_bytes()==(d/'normalized'/name).read_bytes(),'Deterministic normalization '+str(d.relative_to(root))+'/'+name)
   records=[json.loads(x) for x in (d/'normalized/sections.jsonl').read_text().splitlines()];count+=check(all(x['product_id']==prod['ProductID'] and x['job_id']==job['Id'] and x['heading'] and x['text'] for x in records),'Legal records pinned')
   with (d/'normalized/sections.csv').open(newline='') as f:count+=check(len(list(csv.DictReader(f)))==len(records),'CSV record count')
  count+=check(replayed_records==r['record_count'] and replayed_tables==r['table_count'],'Reported record/table counts')
  if (folder/'publisher-export.pdf').exists():
   binary=folder/'publisher-export.pdf';p=json.loads((folder/'publisher-export.receipt.json').read_text());ins=json.loads((folder/'publisher-pdf-inspection.json').read_text());count+=check(binary.read_bytes().startswith(b'%PDF-') and sha(binary)==p['sha256']==ins['sha256'],'Native PDF bytes');count+=check(ins['pages']>0,'PDF structure')
   edition=json.loads((folder/'edition-check.json').read_text());count+=check(edition['pdf_sha256']==p['sha256'],'Edition report source PDF binding')
   if r['publisher_download']['status']=='passed':count+=check(edition['pdf_identity_match'] and edition['pdf_edition_match'],'PDF identity/edition match')
 for rp in root.glob('evidence/official-routes/*/receipt.json'):
  rr=json.loads(rp.read_text());source=rp.parent/'source.html'
  if source.exists() and rr.get('sha256'):count+=check(sha(source)==rr['sha256'],'Official routing source hash')
  if rr.get('method')=='ordinary-headed-browser-government-route-only':count+=check(rr['publisher_requests_issued']==0,'Government browser did not issue publisher requests')
 for qa in root.glob('supplemental/*/table-qa/table-dom-qa.json'):
  j=json.loads(qa.read_text());record_file=qa.parent.parent/'normalized/sections.jsonl';count+=check(sha(record_file)==j['normalized_jsonl_sha256'],'DOM QA normalized source binding');count+=check(sha(root/'scripts/verify_table.cjs')==j['script_sha256'],'DOM QA exact executed script');count+=check(j['passed'] and not j['mismatches'] and not j.get('link_mismatches') and j['cell_count']>0 and j['network_requests_sent']==0,'Independent table DOM QA')
 for rp in root.glob('supplemental/*/cross-reference-qa.json'):
  rr=json.loads(rp.read_text());count+=check(rr['internal_target_count']==rr['targets_in_same_toc'] and not rr['unresolved_targets'] and rr['source_attributes_preserved'] and rr['same_product_attributes'],'Cross reference source targets')
 manifest=root/'manifest-sha256.json'
 if manifest.exists():
  for name,digest in json.loads(manifest.read_text()).items():count+=check(sha(root/name)==digest,'Manifest '+name)
 return {'passed':True,'checks':count,'assignment_rows':len(rows),'e2e_passes':sum(r['status']=='standalone_e2e_pass' for r in rows),'publisher_download_passes':sum(r['publisher_download']['status']=='passed' for r in rows),'normalized_record_count':sum(r['record_count'] for r in rows),'network_requests':0,'writes_to_package':False,'complete_corpus':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--offline',action='store_true');a=p.parse_args();print(json.dumps(verify(a.root),indent=2))
