#!/usr/bin/env python3
"""Read-only, network-free exact-scope/configuration audit. Not corpus verification."""
import hashlib,json,sys,zipfile
import re
sys.dont_write_bytecode=True
from collections import Counter
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit
from dispatch import ROOT,qualified,command,Unsupported
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
@lru_cache(maxsize=None)
def source_bytes(path):
 manifest=read(HERE/'source-evidence-manifest.json');expected=next(x for x in manifest['files'] if x['path']==path)
 with zipfile.ZipFile(HERE/'source-evidence.zip') as z:data=z.read(path)
 if len(data)!=expected['bytes'] or hashlib.sha256(data).hexdigest()!=expected['sha256']:raise ValueError('Bundled raw identity/inventory source corrupt '+path)
 original=ROOT/path
 # Packages/index are immutable evidence. Current collector configs are mutable
 # implementation inputs; the bundled prior config remains historical proof.
 if (path.startswith('packages/') or path=='expanded-scope-index.json') and original.is_file() and original.read_bytes()!=data:raise ValueError('Repository source differs from bundled frozen identity proof '+path)
 return data
def source_read(path):return json.loads(source_bytes(path))
def audit(targets=None,publications=None):
 ts=targets if targets is not None else read(HERE/'targets.json')['targets'];ps=publications if publications is not None else read(HERE/'publications.json')['publications'];index=source_read('expanded-scope-index.json')['jurisdictions'];expected={str(x['sequence']):x for x in index};errors=[]
 def check(ok,why):
  if not ok:errors.append(why)
 check(hashlib.sha256((HERE/'source-evidence.zip').read_bytes()).hexdigest()==read(HERE/'source-evidence-manifest.json')['archive_sha256'],'Raw identity source bundle hash mismatch')
 ids=[t['id'] for t in ts];pids=[p['id'] for p in ps];check(len(ts)==100 and set(ids)==set(expected) and len(ids)==len(set(ids)),'Exact 100 unique target IDs required');check(len(pids)==len(set(pids)),'Duplicate publication IDs');pb={p['id']:p for p in ps};tb={t['id']:t for t in ts}
 for t in ts:
  ref=expected.get(t['id']);check(ref is not None and t['sequence']==ref['sequence'] and t['jurisdiction']==ref['jurisdiction'] and t['state']==ref['state'],'Assignment identity mismatch '+t['id']);p=pb.get(t['primary_publication_id']);check(p is not None and p['target_id']==t['id'] and p['role']=='primary','Exactly owned primary required '+t['id'])
  if p:check(t['primary_publication']==p and t['source_url']==p['source_url'] and t['runnable']==p['runnable'],'Embedded primary/config drift '+t['id'])
  required=t['required_publication_ids'];check(len(required)==len(set(required)) and all(x in pb and pb[x]['target_id']==t['id'] for x in required),'Required publication IDs duplicated/foreign '+t['id']);check(any(x['relationship']=='unresolved_required_scope' and x['required_for_jurisdiction'] for x in t['known_publications']),'Pending jurisdiction scope missing '+t['id']);check(t['prior_validation']['kind']=='bounded_sample_only' and not t['prior_validation']['complete_corpus'],'Historical bounded scope relabeled '+t['id']);check(not t['jurisdiction_complete'] and not t['jurisdiction_inventory_complete'],'Unproven jurisdiction complete '+t['id'])
 for p in ps:
  t=tb.get(p['target_id']);check(t is not None,'Orphan publication '+p['id']);check(p['validation_level']=='mapped_only' and not p['full_live_verified'],'Base mapping must not inherit live pass '+p['id']);check(bool(p['title']),'Missing publication title '+p['id'])
  for e in p['evidence_paths']:
   try:source_bytes(e);valid=not Path(e).is_absolute() and '..' not in Path(e).parts
   except (ValueError,KeyError,StopIteration):valid=False
   check(valid,'Missing/nonportable/corrupt source proof '+str(e))
  if not t:continue
  if p['runnable']:
   try:plan=command(p,t,'{OUT}',python='python3');check(plan['jurisdiction_complete'] is False,'Dispatch incorrectly closes jurisdiction')
   except (Unsupported,KeyError,ValueError) as exc:errors.append('Runnable config not dispatchable '+p['id']+': '+str(exc));continue
  else:check(bool(p.get('unsupported_reason')),'Unsupported config lacks reason '+p['id'])
  if p['publisher']=='municode':
   ident=p['expected_identity'];check(bool(p.get('publisher_product_id')) and bool(ident.get('publisher_client_id')) and ident.get('state')==t['state'],'Municode identity/product absent '+p['id'])
   source=ident.get('evidence_path')
   if source:
    receipt=source_read(source);product=receipt['product'];check(product['Client']['ClientID']==ident['publisher_client_id'] and product['Client']['ClientName'] in ident['client_names'],'Municode client binding '+p['id']);observed={product['ProductID']}|{x['productId'] for x in receipt.get('publications',[])};check(p['publisher_product_id'] in observed,'Unobserved Municode product '+p['id']);old=urlsplit(receipt['url']);expected_route=old.scheme+'://'+old.netloc+'/'.join(old.path.split('/')[:5]);check(p['source_url'].rstrip('/')==expected_route.rstrip('/'),'Municode source route differs from exact client context evidence '+p['id'])
  if p['source_family']=='ecode360':check(not urlsplit(p['source_url']).path.strip('/').isdigit() and urlsplit(p['source_url']).path.strip('/')==p['expected_identity'].get('customer_id'),'eCode whole-publication alias/customer mismatch '+p['id'])
  if p['publisher']=='american-legal' and p['runnable']:
   ep=p['expected_identity'].get('evidence_path');raw=source_bytes(ep).decode() if ep else '';match=re.search(r'window\._redux_state\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")',raw);check(bool(match),'AL retained publisher identity absent '+p['id'])
   if match:
    codes=json.loads(json.loads(match[1]))['codes'];parts=urlsplit(p['source_url']).path.split('/');selector=p.get('selector',{}).get('publication');check(parts[2]==codes['currClient']['slug'] and selector in {x['slug'] for x in codes['selectedVersion']['toc']},'AL observed client/publication selector mismatch '+p['id'])
  if p['source_family']=='municipal.codes':check(len(urlsplit(p['source_url']).path.strip('/').split('/'))==1,'Municipal sample subtree mislabeled publication '+p['id'])
 check(tb.get('70',{}).get('source_url')=='https://library.municode.com/nv/reno/codes/administrative_code','Reno Administrative Code correction lost');check(sum(p['role']=='primary' for p in ps)==100,'Primary denominator !=100')
 return {'schema_version':1,'network_requests_sent':0,'read_only':True,'passed':not errors,'errors':errors,'target_count':len(ts),'primary_runnable':sum(t['runnable'] for t in ts),'primary_unsupported':sum(not t['runnable'] for t in ts),'primary_adapter_counts':dict(sorted(Counter(t['publisher'] for t in ts).items())),'publication_candidates':len(ps),'secondary_runnable':sum(p['runnable'] and p['role']=='secondary' for p in ps),'secondary_unsupported':sum(not p['runnable'] and p['role']=='secondary' for p in ps),'base_full_live_verified':sum(p['full_live_verified'] for p in ps),'jurisdiction_complete':sum(t['jurisdiction_complete'] for t in ts),'scope_note':'Runnable means a qualified dispatch configuration. Publication candidates, historical alternatives and external references are not a count of independently current municipal publications. Prior bounded passes remain historical.'}
def main():
 r=audit();r['registry_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'targets.json',HERE/'publications.json']};print(json.dumps(r,indent=2));return 0 if r['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
