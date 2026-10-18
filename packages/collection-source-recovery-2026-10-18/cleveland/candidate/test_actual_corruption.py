"""Adversarial rehashed canonical omission must fail actual source reconstruction."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,shutil,tempfile,time,socket,base64
from pathlib import Path
from unittest.mock import patch
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B/'candidate'));import package
O=B/'package'
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(p):return {x.relative_to(p).as_posix():sha(x) for x in p.rglob('*') if x.is_file()}
original=files(O);start=time.time();calls=[];results=[]
def no(*a,**k):calls.append('forbidden');raise AssertionError('forbidden')
with tempfile.TemporaryDirectory(prefix='cleveland-attachment-corruption-') as d,patch.object(socket.socket,'connect',no),patch.object(base64,'b64decode',no):
 T=Path(d)/'copy';shutil.copytree(O,T);names=['aggregate-fulltext.json','package-state.json','run-manifest.json'];backup={n:(T/n).read_bytes() for n in names};obj=json.loads(backup[names[0]]);obj['provisions']=[r for r in obj['provisions'] if not(r['section_name']=='Required Frontage Features' and r['source_url'].endswith('13294.pdf'))];assert len(obj['provisions'])==6140;(T/names[0]).write_bytes(encoded(obj));state=json.loads(backup[names[1]]);state['artifacts'][names[0]]=sha(T/names[0]);(T/names[1]).write_bytes(encoded(state));manifest=json.loads(backup[names[2]]);manifest['artifact_hashes'][names[0]]=sha(T/names[0]);manifest['artifact_hashes'][names[1]]=sha(T/names[1]);(T/names[2]).write_bytes(encoded(manifest))
 try:package.verify(T);raise AssertionError('Rehashed missing attachment accepted')
 except ValueError as e:assert 'Package artifact inventory differs from exact source projection' in str(e);results.append({'case':'Whole canonical attachment removed, output/state/manifest rehashed consistently','refused':True,'reason':str(e)})
 for n,data in backup.items():(T/n).write_bytes(data)
 p=T/'evidence/input/raw/f970d64e493f94757a20da17e81619976a77294b0d2b0c5a3712a04193e5c90d.bin';p.write_bytes(p.read_bytes()+b'corrupt')
 try:package.verify(T);raise AssertionError('Corrupt required native bytes accepted')
 except ValueError as e:assert 'missing/extra/corrupt' in str(e);results.append({'case':'Required attachment original binary corrupted','refused':True,'reason':str(e)})
assert files(O)==original and not calls
receipt={'passed':True,'cases':results,'forbidden_calls':calls,'original_package_unchanged':True,'native_parse_or_source_normalization':False,'seconds':time.time()-start,'test_source_sha256':sha(Path(__file__))};(B/'actual-corruption-tests.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
