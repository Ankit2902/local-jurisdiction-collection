"""Read-only offline evidence integrity + byte-identical parse replay. No network."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,tempfile,runpy
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from normalize import normalize
from government_pdfs import parse as parse_pdf
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(b,msg):
 if not b:raise AssertionError(msg)
def main():
 checks=[];records=pages=0
 for group in ['http','browser','supplemental']:
  for d in sorted((ROOT/group).glob('*')):
   if not (d/'receipt.json').exists():continue
   r=json.loads((d/'receipt.json').read_text())
   if r.get('product') and r.get('job'):
    check(str(r['job']['ProductId'])==str(r['product']['ProductID']),'Job/product mismatch')
    if (d/'organization.json').exists():
     org=json.loads((d/'organization.json').read_text());check(str(org['ClientID'])==str(r['product']['Client']['ClientID']),'Organization/client mismatch')
    expected=r.get('expected_identity')
    if expected:
     client=r['product']['Client'];check(client['State']['StateAbbreviation']==expected['state'],'State mismatch');check(client['ClientName'].lower() in [n.lower() for n in expected['client_names']],'Client mismatch')
   for raw in r.get('responses',[]):check(sha(d/raw['file'])==raw['sha256'],'Raw response changed '+str(d/raw['file']))
   for key,fn in [('script_sha256','executed-collect_browser.cjs'),('gate_script_sha256','executed-gate_cli.py')]:
    if (d/fn).exists() and r.get(key):check(sha(d/fn)==r[key],'Executed script hash mismatch '+str(d))
   if (d/'samples.json').exists():
    if r.get('status') not in ['acquired','sample_acquired_driver_stopped'] or r.get('access_stop'):
     checks.append({'folder':str(d.relative_to(ROOT)),'failed_or_stopped_acquisition':True,'raw_hashes_verified':True,'normalized_pass_claimed':False});continue
    samples=json.loads((d/'samples.json').read_text())
    for sample in samples:
     nid=sample['node']['Id']; source=[]
     for rr in r.get('responses',[]):
      query=parse_qs(urlparse(rr['url']).query)
      if '/api/CodesContent' in rr['url'] and query.get('nodeId')==[nid]:source.append(rr)
     if group!='supplemental':
      check(bool(source),'Missing legal source response '+nid)
      check(any(json.loads((d/rr['file']).read_text())==sample['content'] for rr in source),'Sample changed from raw response '+nid)
     else:
      ar=json.loads((d/'acquisition-receipt.json').read_text());check(ar['status']=='acquired' and not ar.get('access_stop'),'Supplemental acquisition failed/stopped');aq=parse_qs(urlparse(ar['api_url']).query);check(urlparse(ar['api_url']).hostname=='library.municode.com' and urlparse(ar['api_url']).path=='/api/CodesContent','Unexpected supplemental API source');check(aq['nodeId']==[nid] and aq['productId']==[str(r['product']['ProductID'])] and aq['jobId']==[str(r['job']['Id'])],'Supplemental query publication binding');check(urlparse(ar['root_url']).path==urlparse(r['url']).path,'Supplemental root mismatch')
      candidates=[]
      for primary in (ROOT/'browser').glob('*/receipt.json'):
       pr=json.loads(primary.read_text())
       if pr.get('status')=='acquired' and pr['url']==ar['root_url'] and pr['product']['ProductID']==r['product']['ProductID'] and pr['job']['Id']==r['job']['Id']:candidates.append(primary.parent)
      check(len(candidates)==1,'Supplemental has no unique acquired primary provenance');toc=json.loads((candidates[0]/'toc-full.json').read_text());nodes=[]
      def walk(n):
       if n['Id']==nid:nodes.append(n)
       for child in n.get('Children',[]):walk(child)
      walk(toc);check(len(nodes)==1 and nodes[0]['Heading']==sample['node']['Heading'],'Supplemental not present in pinned primary TOC')
      check(sha(d/'content.json')==ar['response']['sha256'],'Supplemental raw source changed');check(json.loads((d/'content.json').read_text())==sample['content'],'Supplemental sample changed')
    with tempfile.TemporaryDirectory(prefix='complisolv-replay-') as td:
     parser=normalize
     if r.get('status')=='sample_acquired_driver_stopped':
      old=ROOT/'script-versions/aab179e5137c925ab30942242c02243c1f253db0252eac6c51c74f5f54ca8a67-normalize.py'
      check(sha(old)=='aab179e5137c925ab30942242c02243c1f253db0252eac6c51c74f5f54ca8a67','Historical parser changed');check(all(rr['status']==200 for rr in r['responses']),'Historical response was not200');parser=runpy.run_path(str(old))['normalize']
     v=parser(d,td)
     for fn in ['sections.jsonl','sections.csv']:check(sha(Path(td)/fn)==sha(d/'normalized'/fn),'Replay differs '+str(d/fn))
    records+=v['record_count'];checks.append({'folder':str(d.relative_to(ROOT)),'records':v['record_count'],'tables':v['table_count'],'byte_identical_jsonl_csv':True,'raw_hashes_verified':True})
   pp=d/'publisher-export.pdf'
   if pp.exists():
    pr=json.loads((d/'publisher-export.receipt.json').read_text());check(sha(pp)==pr['sha256'],'Publisher PDF hash');check(pp.read_bytes()[:5]==b'%PDF-','Publisher PDF magic')
 for d in sorted((ROOT/'native').glob('*')):
  if not (d/'source-config.json').exists():continue
  cfg=json.loads((d/'source-config.json').read_text())
  with tempfile.TemporaryDirectory(prefix='complisolv-native-replay-') as td:
   v=parse_pdf(cfg,d,td)
   for fn in ['pages.jsonl','pages.csv']:check(sha(Path(td)/fn)==sha(d/'normalized'/fn),'Native replay differs '+str(d/fn))
  pages+=v['record_count'];checks.append({'folder':str(d.relative_to(ROOT)),'pdf_page_records':v['record_count'],'byte_identical_jsonl_csv':True,'source_pdf_sha_verified':True})
 for qap in ROOT.glob('**/table-dom-qa.json'):
  if any(x in qap.parts for x in ['.venv','node_modules']):continue
  qa=json.loads(qap.read_text());check(qa['network_requests_sent']==0,'QA unexpectedly live');check(qa['passed'] and all(not c['mismatches'] for c in qa['checks']),'Recorded table DOM QA failed')
 if (ROOT/'manifest.json').exists():
  manifest=json.loads((ROOT/'manifest.json').read_text())
  for row in manifest['files']:check(sha(ROOT/row['path'])==row['sha256'],'Manifest changed '+row['path'])
 results=json.loads((ROOT/'results.json').read_text());assignment=json.loads((ROOT/'assignment.json').read_text());check({r['sequence'] for r in results}=={a['sequence'] for a in assignment},'Assignment/result mismatch');check(all(r['complete_corpus'] is False for r in results),'Unproven complete corpus')
 for r in results:
  for field in ['evidence_paths','script_paths']:
   for p in r[field]:check(not Path(p).is_absolute() and (ROOT/p).exists(),'Missing/nonrelative '+p)
 print(json.dumps({'offline':True,'read_only':True,'network_requests_sent':0,'targets':len(results),'replayed_legal_provisions_including_retained_attempts':records,'supplemental_pdf_page_records':pages,'checks':checks,'manifest_verified':(ROOT/'manifest.json').exists(),'passed':True},indent=2))
if __name__=='__main__':main()
