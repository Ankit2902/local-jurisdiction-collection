"""Read-only whole cached-source replay and independent HTML/CSV consumer. Stdlib only."""
import sys
sys.dont_write_bytecode=True
import collections,gzip,hashlib,json,socket
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'runtime'))
from collectors.encodeplus import infrastructure_logical as logical
from consumer import compare

def check():
 manifest=H/'MANIFEST.json'
 if manifest.exists():
  m=json.loads(manifest.read_text());known={x['path']:x for x in m['files']};actual={p.relative_to(H).as_posix():p for p in H.rglob('*')if p.is_file()and p!=manifest}
  assert set(actual)==set(known),'Packet file inventory changed'
  assert all(hashlib.sha256(actual[n].read_bytes()).hexdigest()==v['sha256']for n,v in known.items()),'Packet bytes changed'
 rt=H/'runtime/collectors/encodeplus';f=json.loads(gzip.decompress((rt/'fixtures/infrastructure-printed-native/source-ir-and-native-inventory.json.gz').read_bytes()));cfg=json.loads((rt/'configs/native-82-0c6b3dc40877.json').read_text());w=json.loads((rt/'fixtures/infrastructure-printed-native/native-page26-list-witness.json').read_text())
 source=gzip.decompress((H/'evidence/baseline-records.jsonl.gz').read_bytes());assert hashlib.sha256(source).hexdigest()=='8bf0cf6e1d319d900fbdafff16dd8f051e945f39a6102aaad035fe3a4001afe9'
 before={p.relative_to(H).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in H.rglob('*')if p.is_file()}
 def no(*a,**k):raise AssertionError('No network/native/image operation permitted')
 with patch.object(socket,'socket',no):
  rows,dim=logical.project_records(f['source_pages'],f['native_inventory'],cfg,'raw/start.pdf',logical.SOURCE_METADATA,w);out=logical.outputs(rows)
  assert all((H/'actual'/name).read_bytes()==data for name,data in out.items()),'Primary/sidecar replay differs'
  old=[json.loads(l)for l in source.decode().split('\n')if l];result=compare(old,rows,out['records.csv'])
 assert before=={p.relative_to(H).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in H.rglob('*')if p.is_file()},'Read-only replay modified packet'
 return {k:v for k,v in result.items()if k!='records'}|{'cached_collector_replay':True,'native_parse_performed':False,'whole_publication_qualified':False,'scope':'All62 cached source pages /172 units; previously queried four-page text-only geometry capsule is hash-bound, not newly queried.'}
if __name__=='__main__':print(json.dumps(check(),indent=2))
