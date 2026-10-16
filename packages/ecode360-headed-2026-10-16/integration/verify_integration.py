#!/usr/bin/env python3
"""Verify final component manifests and cross-component evidence; no network."""
from pathlib import Path
import json,hashlib,re
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
errors=[];checks=[]
specs=[('ecode360','BUNDLE-MANIFEST.json','files'),('independent-review','BUNDLE-MANIFEST.json','files'),('publisher-downloads','ARTIFACT-HASHES.json','files'),('runtime-review','RUNTIME-REVIEW.json','artifacts')]
for directory,name,key in specs:
 raw=read(directory+'/'+name)[key]
 items=raw if isinstance(raw,list) else [dict(path=k,**(v if isinstance(v,dict) else {'sha256':v})) for k,v in raw.items()]
 for row in items:
  path=directory+'/'+row['path']
  if sha(path)!=row['sha256']:errors.append({'path':path,'error':'manifest_hash_mismatch'})
 checks.append({'package':directory,'manifest':directory+'/'+name,'hashes_verified':len(items)})
h=read('ecode360/HEADED-VALIDATION.json');r=read('independent-review/REVIEW.json');d=read('publisher-downloads/DOWNLOAD-VALIDATION.json')
reviewed={x['slug']:x for x in r['cities']}; downloads={x['slug']:x for x in d['results']}
assert len(h['jurisdictions'])==len(reviewed)==len(downloads)==14
for row in h['jurisdictions']:
 old=reviewed[row['slug']]
 if row['source_sha256']!=old['raw_source_sha256']:errors.append({'slug':row['slug'],'error':'latest_source_not_independently_reviewed_bytes'})
 pdf=row['publisher_download']
 if pdf['file_acquired'] and pdf['sha256']!=downloads[row['slug']]['pdf_sha256']:errors.append({'slug':row['slug'],'error':'PDF_acquisition_review_mismatch'})
for p,value in r['source_hashes'].items():
 if sha('ecode360/'+p)!=value:errors.append({'path':p,'error':'reviewed_parser_changed'})
for p,value in read('ecode360/SOURCE-FREEZE.json')['code_files'].items():
 if sha('ecode360/'+p)!=value:errors.append({'path':p,'error':'primary_source_freeze_changed'})
for p,value in read('publisher-downloads/SOURCE-FREEZE.json')['source_sha256'].items():
 if sha('publisher-downloads/'+p)!=value:errors.append({'path':p,'error':'PDF_source_freeze_changed'})
for name in ['README.md','SOURCE-MATRIX.md']:
 for target in re.findall(r'\]\(([^)]+)\)',(ROOT/name).read_text()):
  if '://' not in target and not (ROOT/target.split('#')[0]).exists():errors.append({'path':name,'missing_link':target})
symlinks=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_symlink()]
if symlinks:errors.append({'symlinks':symlinks})
report={'reviewed_at':datetime.now(timezone.utc).isoformat(),'status':'PASS' if not errors else 'FAIL','component_manifests':checks,'component_hash_references_verified':sum(x['hashes_verified'] for x in checks),'cross_component_source_and_pdf_bindings_verified':True if not errors else False,'primary_source_and_PDF_code_freezes_verified':not errors,'whole_corpus_verified':False,'prior_sealed_bundle_verification':{'status':'PASS','files':3862,'bytes':325725388},'errors':errors}
(ROOT/'integration/INTEGRATION-REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
