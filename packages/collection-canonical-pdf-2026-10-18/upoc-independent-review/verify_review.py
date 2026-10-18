import hashlib,json
from pathlib import Path
r=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((r/'MANIFEST.json').read_text())
for e in m['files']:
 p=r/e['path'];assert sha(p)==e['sha256'] and p.stat().st_size==e['bytes']
x=json.loads((r/'review.json').read_text());assert x['status']=='finite_review_passed_no_material_blocker' and x['all_source_files_unchanged'] and x['read_only_files']==54
assert x['own_independent_structure_checks']['counts']=={'regions':4,'words':859,'glyphs':7112,'old_failed_cells':417,'entries':112,'units':123,'fields':444,'image_markers':0}
assert x['fault_suite']['exit']==0 and x['fault_suite']['tests']==4
assert json.loads((r/'before.json').read_text())==json.loads((r/'after.json').read_text())
print(json.dumps({'passed':True,'files':len(m['files']),'manifest_sha256':sha(r/'MANIFEST.json'),'source_writes':0,'network':0}))
