from pathlib import Path
import json,hashlib,datetime,sys,collections
from bs4 import BeautifulSoup
from urllib.parse import urljoin
P=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');B=P/'outputs/collection-readiness-next-2026-10-17/originals-integration';O=B/'flagstaff-common-live-recovery-v1';D=B/'flagstaff-common-live-recovery-v1-proof';S=O/'source';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=lambda p:json.loads(p.read_text());cp=j(S/'checkpoint.json');term=j(D/'terminal.json');initial=j(D/'observed-before-sigint.json');resume=j(D/'resume-started.json');arts=cp['artifacts']
rows=[]
for a in arts:
 assert a['status']==200 and a['final_url']==a['source_url'] and h(S/a['path'])==a['sha256']
 rows.append({k:a[k] for k in ['role','source_url','path','sha256','started_at','finished_at','bytes']})
counts=dict(collections.Counter(x['role'] for x in rows));readers=cp['observed_readers'];assert len(readers)==18
assert counts['content']==361 and len({a['source_url'] for a in arts if a['role']=='content'})==361
assert counts['root-toc-start']==counts['root-toc-end']==counts['currency-start']==counts['currency-end']==counts['root-resume-validation']==counts['currency-resume-validation']==1
assert counts['toc-start']==counts['toc-end']==18
resumetoc=[a for a in arts if a['role'].startswith('toc-resume-validation-')];assert len(resumetoc)==18
clean=lambda s:' '.join(s.split())
def native_projection(a):
 bs=BeautifulSoup((S/a['path']).read_bytes(),'html.parser');rows=[]
 for p in bs.select('p'):
  box=p.select_one('input[name=code]');anchor=p.find('a',href=True)
  if box and anchor:rows.append({'value':box['value'],'href':anchor['href'],'id':anchor.get('id'),'label':clean(anchor.get_text(' ',strip=True))})
 return rows
triples=[]
for r in readers:
 phases=[]
 for choices in [[a for a in arts if a['role']=='toc-start'],resumetoc,[a for a in arts if a['role']=='toc-end']]:
  matches=[a for a in choices if a['source_url']==r['url']];assert len(matches)==1;phases.append(matches[0])
 projections=[native_projection(a) for a in phases];assert projections[0]==projections[1]==projections[2]
 triples.append({'source_url':r['url'],'opening':phases[0]['sha256'],'resumed':phases[1]['sha256'],'closing':phases[2]['sha256'],'source_control_projection_equal':True,'source_controls':len(projections[0])})
assert term['cached_body_hashes_unchanged'] and term['cached_body_refetches_after_resume']==[] and term['source_runtime_config_binding_unchanged'] and not cp['errors'] and not cp['blocked']
for a in resume['cached_content']:
 matches=[r for r in arts if r['role']=='content' and r['source_url']==a['source_url']];assert len(matches)==1 and matches[0]==a
assert len(resume['cached_content'])==3
out={'schema':'flagstaff-real-live-phase-binding-1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'acquisition':'Actual ordinary headed Chrome v7 common-launcher acquisition with genuine SIGINT at3cachedbodies and same-command resume; not recorded backend.','source_checkpoint_sha256':h(S/'checkpoint.json'),'terminal_receipt_sha256':h(D/'terminal.json'),'phase_counts':counts,'all421_transport_raw_hashes_valid':True,'reader_opening_resumed_closing_projections':triples,'reader_projections_equal':True,'roots_and_currency_equal':all(cp.get(k) for k in ['closing_roots_equal','closing_currency_equal','closing_inventory_equal']),'three_cached_raw_receipts_entirely_unchanged':True,'cached_body_refetches_after_resume':0,'source_errors':[],'source_blocks':[],'acquired_unique_bodies':361,'literal_browser_fragment_health':False,'whole_jurisdiction_accepted':False,'raw_receipts':rows,'source_mutated':False,'new_publisher_requests':0}
path=B/'flagstaff-common-live-recovery-v1-phase-binding.json';assert not path.exists();path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'path':str(path),'sha256':h(path),'counts':counts,'readers':len(triples)},indent=2))
