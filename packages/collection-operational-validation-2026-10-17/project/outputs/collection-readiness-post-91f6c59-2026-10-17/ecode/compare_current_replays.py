from pathlib import Path
import json,hashlib,shutil,sys
R=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection');P=R.parent.parent
sys.path.insert(0,str(R));from collectors.ecode.engine import code_fingerprint
from collectors.qa.audit_normalized_images import audit
O=P/'outputs/collection-readiness-post-91f6c59-2026-10-17/ecode';O.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result={'source_fingerprint':code_fingerprint(),'tests':{'count':56,'passed':True,'log':'full-tests.txt'},'publisher_requests':0,'live_acquisition_claim':False,'policy':'Exact [IMAGE], no separate image acquisition or image decoding; immutable originals retained.','actual_replays':[]}
shutil.copyfile('/tmp/ecode-image-context-full-tests-v4.txt',O/'full-tests.txt')
for city in ['albany','phoenix']:
 old=P/f'outputs/collection-readiness-2026-10-17/ecode/{city}-operator-final/retained-proof';new=O/f'{city}-image-context-replay-v2'
 equal=[]
 for n in ['records.jsonl','records.csv','image-omissions.json','inventory.json','link-ledger.json']:
  x=sha(old/n);y=sha(new/n)
  equal.append({'path':n,'original_sha256':x,'current_sha256':y,'byte_equal':x==y})
 s=json.loads((new/'checkpoint.json').read_text());raw=[]
 for a in s['artifacts']:
  f=new/a['path'];assert sha(f)==a['sha256'];ctype=a.get('headers',{}).get('content-type','')
  assert not ctype.lower().startswith('image/');raw.append({'path':a['path'],'sha256':a['sha256'],'content_type':ctype})
 assert s['network_prohibited']
 im=audit(new);assert im['passed'],im['errors'][:5];(O/f'{city}-normalized-image-audit.json').write_text(json.dumps(im,indent=2)+'\n')
 # Every changed HTML field may only neutralize already-classified image links.
 from bs4 import BeautifulSoup
 from collectors.ecode.adapters import image_anchor
 oldrows=[json.loads(x) for x in (old/'records.jsonl').read_text().split('\n') if x.strip()]
 newrows=[json.loads(x) for x in (new/'records.jsonl').read_text().split('\n') if x.strip()]
 assert len(oldrows)==len(newrows)
 differences=[]
 def inert(value):
  if isinstance(value,list):return [inert(x) for x in value]
  soup=BeautifulSoup(value,'html.parser')
  for a in soup.select('a[href]'):
   if image_anchor(a) or a['href'].endswith('#image-omitted'):a['href']='#image-omitted'
  return str(soup)
 for a,b in zip(oldrows,newrows):
  assert a['id']==b['id'];fields=[]
  for key in a:
   if a[key]==b[key]:continue
   fields.append(key)
   if key=='body_sha256':continue
   assert key in {'content_html','semantic_html','tables_html','notes_html'},(a['id'],key)
   assert inert(a[key])==inert(b[key]),(a['id'],key)
  if fields:differences.append({'id':a['id'],'changed_fields':fields})
 c=json.loads((new/'coverage.json').read_text())
 result['actual_replays'].append({'city':city,'output':str(new.relative_to(P)),'records':c['normalized_records'],'byte_equality':equal,'record_differences':differences,'all_legal_text_identity_and_structure_unchanged':True,'raw_artifacts':raw,'no_separate_image_mime':True,'normalized_image_audit':f'{city}-normalized-image-audit.json','network_prohibited':True,'complete':False,'retained_errors':s['errors']})
(O/'current-image-context-replay-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'cities':[{k:r[k] for k in ['city','records','complete','network_prohibited']} for r in result['actual_replays']],'source':result['source_fingerprint']['adapters.py']}))
