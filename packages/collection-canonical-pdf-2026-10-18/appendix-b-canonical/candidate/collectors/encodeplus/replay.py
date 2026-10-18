"""Create a current-parser derivative without changing sealed source evidence or accessing the network."""
import argparse,datetime,pathlib,shutil,sys,platform
from .collect import HERE,code_hashes,assemble,runtime_info
from .model import inventory,decode,parse_document,outputs
from .util import read_json,atomic_bytes,atomic_json,digest,validate_file
from .verify import verify

def replay(source,out):
 source=pathlib.Path(source).resolve();out=pathlib.Path(out).resolve()
 assert source!=out and not out.exists(),'Derivative output must be a new directory'
 original=(source/'checkpoint.json').read_bytes();s=read_json(source/'checkpoint.json')
 # Check the retained source graph before copying; normalization may differ under a stronger parser.
 for p in source.rglob('*.receipt.json'):
  m=read_json(p);raw=p.with_name(p.name[:-len('.receipt.json')]);assert digest(raw.read_bytes())==m['sha256'],'Corrupt retained raw evidence'
 for name,h in s['code_hashes'].items():validate_file(source,'script-versions/'+h+pathlib.Path(name).suffix,h)
 shutil.copytree(source,out,ignore=shutil.ignore_patterns('__pycache__','.venv','*.log'))
 old=digest(original);atomic_bytes(out/'checkpoint-history'/(old+'.json'),original);current=code_hashes()
 for name,h in current.items():atomic_bytes(out/'script-versions'/(h+pathlib.Path(name).suffix),(HERE/name).read_bytes())
 s.setdefault('code_upgrades',[]).append({'prior_checkpoint_sha256':old,'prior_code_hashes':s['code_hashes'],'current_code_hashes':current,'command':sys.argv,'reason':'Offline current-parser derivative; original evidence immutable, no requests or refreshed source closing checks'})
 s['code_hashes']=current;s['derivative_replay']={'source_checkpoint_sha256':old,'source_inventory_sha256':s['inventory_sha256'],'network_requests':0,'runtime':runtime_info(),'command':sys.argv,'kind':'Retained-evidence replay; not a fresh live run'}
 raw=validate_file(out,s['inventory_raw']['path'],s['inventory_raw']['sha256']);meta=read_json(raw.with_name(raw.name+'.receipt.json'));inv=inventory(decode(raw.read_bytes(),meta['headers']),s['config']);known={n['id']:n for n in inv['nodes']}
 for block in s['blocks']:
  p=validate_file(out,block['path'],block['sha256']);m=read_json(p.with_name(p.name+'.receipt.json'));block['record_ids']=[r['id'] for r in parse_document(decode(p.read_bytes(),m['headers']),block['requested'],s['config'],known,s.get('image_skips',{}))]
 records,_=assemble(out,s,inv)
 for name,data in outputs(list(records.values())).items():atomic_bytes(out/name,data)
 atomic_json(out/'checkpoint.json',s);report=verify(out);atomic_json(out/'coverage.json',report);return report
if __name__=='__main__':
 import json
 p=argparse.ArgumentParser();p.add_argument('source',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=replay(a.source,a.out);print(json.dumps(r,indent=2));raise SystemExit(0 if r['publication_text_complete'] and r['attachments_complete'] else 2)
