"""Authorized exact ordinary government-page discovery; no resource/image fetches."""
from pathlib import Path
import sys,json,hashlib,shutil,datetime
P=Path(__file__).resolve().parent
R=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
# Snapshot ordinary shared transport before any request; no gate overrides.
shutil.copyfile(R/'collectors/official/transport.py',P/'runtime/transport.py');sys.path.insert(0,str(P/'runtime'));import transport
sys.path.insert(0,str(R/'collectors/registry'));from catalog import load_catalog
ids=['67-b8a8412beb82','96-55b5a35f127a'];cat=load_catalog();rows=[next(p for p in cat['publications']if p['id']==i)for i in ids]
gates={}
for host in ['www.lincoln.ne.gov','lincoln.ne.gov','www.clarkcountynv.gov','clarkcountynv.gov']:
 p=Path('/tmp/compliSolv-official-publication-gate')/hashlib.sha256(host.encode()).hexdigest()[:20]/'state.json';gates[host]={'path':str(p),'before':json.loads(p.read_text())if p.exists()else None}
home=Path.home()/'.local/state/local-jurisdiction-collection/observed-access-stops.json'
binding={'catalog_entries':rows,'transport_sha256':hashlib.sha256((P/'runtime/transport.py').read_bytes()).hexdigest(),'gates_before':gates,'home_stops_before':json.loads(home.read_text())if home.exists()else None,'python':sys.version,'started_at':transport.now(),'policy':'No image resources/native image bytes/render/OCR; originalsourceHTML retained without execution. No publisher route follow/retry.'}
(P/'before.json').write_text(json.dumps(binding,indent=2)+'\n')
for row,name in zip(rows,['lincoln-comprehensive','clark-county-code']):
 b,m=transport.fetch(row['source_url']);transport.atomic(P/(name+'.html'),b);transport.atomic(P/(name+'.receipt.json'),json.dumps(m,indent=2).encode()+b'\n');print(json.dumps({'name':name,'status':m['status'],'bytes':len(b),'sha256':m['sha256'],'access_stop':m.get('access_stop',False),'final_url':m['final_url']}),flush=True)
 # Each assigned government route is independent; no alternate requests/retries.
