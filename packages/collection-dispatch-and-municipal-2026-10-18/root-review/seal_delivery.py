from pathlib import Path
import json,hashlib
r=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
name='collection-dispatch-and-municipal-2026-10-18';b=r/'packages'/name
excluded={'.venv','.review-venv','.browsers','node_modules','__pycache__','.pytest_cache','.DS_Store','.git'}
def files(root):return [p for p in sorted(root.rglob('*')) if p.is_file() and not any(x in excluded for x in p.relative_to(root).parts) and p.suffix not in {'.pyc','.pyo'}]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def row(p,root):return {'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)}
assert not (b/'BUNDLE-MANIFEST.json').exists(),'Do not overwrite a sealed bundle'
rows=[row(p,b) for p in files(b)]
bm={'schema_version':1,'scope':'Reviewed Clark dispatch, historical UPOC full native replay with corrected inline image guards, municipal canonical export and original-source peers, and Boston routing evidence; all source and legal completeness limits retained','files':rows,'file_count':len(rows),'bytes':sum(x['bytes'] for x in rows)}
(b/'BUNDLE-MANIFEST.json').write_text(json.dumps(bm,indent=2)+'\n')
proof=r/'collectors/qa/followup-proof-receipts/dispatch-and-municipal-2026-10-18/summary.json';s=json.loads(proof.read_text());s['source_evidence_manifest_sha256']=sha(b/'BUNDLE-MANIFEST.json');proof.write_text(json.dumps(s,indent=2)+'\n')
dp=r/'DELIVERY-MANIFEST.json';d=json.loads(dp.read_text());old=[x for x in d['files'] if not x['path'].startswith('collectors/') and x['path']!='collect.py' and not x['path'].startswith('packages/'+name+'/')]
new=[]
for p in files(r/'collectors')+[r/'collect.py']+files(b):
 x=row(p,r);x['source']='dispatch/municipal/native-image reviewed checkpoint 2026-10-18';new.append(x)
d['files']=old+new;assert len({x['path'] for x in d['files']})==len(d['files']);d['file_count']=len(d['files']);d['bytes']=sum(x['bytes'] for x in d['files'])
if name not in d['source_packages']:d['source_packages'].append(name)
dp.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({'bundle_manifest_sha256':sha(b/'BUNDLE-MANIFEST.json'),'bundle_files_with_manifest':len(rows)+1,'bundle_payload_bytes':bm['bytes'],'delivery_files':d['file_count'],'delivery_bytes':d['bytes']},indent=2))
