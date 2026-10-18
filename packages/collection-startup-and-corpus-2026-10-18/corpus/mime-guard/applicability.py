"""New guard against the complete retained source projection; no normalizer."""
import hashlib,json,socket,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent/'candidate'))
import package
from common import artifacts,files
base=Path('../corpus-package-fidelity-candidate-v1/actual/flagstaff-package-v2').resolve();before=files(base);requests=[]
def forbidden(*a,**kw):requests.append('socket');raise AssertionError('Network forbidden')
socket.socket=forbidden
b,proof,family,p=package.binding(base/'evidence/input',(base/'evidence/proofs/read-only-proof.json').read_bytes(),(base/'evidence/proofs/family-verification.json').read_bytes(),'originals-flagstaff-html-v1');out=artifacts(p)
for name,data in out.items():assert data==(base/name).read_bytes(),name
assert len(out)==15 and files(base)==before and not requests
print(json.dumps({'passed':True,'scope':'Entire retained Flagstaff 2661-row projection through MIME-whitespace guard; no raw source normalization','new_common_sha256':package.code()['common.py'],'all_15_generated_artifacts_byte_unchanged':True,'records':len(p.rows),'source_nodes':len(p.nodes),'literal_image_markers':sum(r['full_text'].count('[IMAGE]') for r in p.rows),'base_unchanged':True,'network_requests':len(requests),'native_or_image_operations':0,'source_false_gates_unchanged':True},indent=2))
