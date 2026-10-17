#!/usr/bin/env python3
"""Fresh, network-free normalization replay. Never modifies acquisition evidence.

The acquisition scripts and execution history remain unchanged. New parser
snapshots and explicit lineage describe only the retained-evidence replay.
"""
import argparse,datetime,json,shutil,sys
from pathlib import Path
from model import *
from transport import atomic,save
def replay(source,out):
 source=source.resolve();out=out.resolve()
 assert source.is_dir() and not out.exists(),'Existing source and fresh output required'
 assert source not in out.parents and out not in source.parents,'Replay must be outside source'
 meta=json.loads((source/'run.json').read_text());assert meta['status']=='acquired' and meta['strategy']=='native' and not meta['identity']['is_pdf'],'This replay profile requires acquired native HTML'
 shutil.copytree(source,out)
 try:
  parser=Path(__file__).parent;snap=out/'normalization-scripts';snap.mkdir()
  names=['replay.py','model.py','verify.py','pdf_layout.py','pdf_tags.py','pdf_native.py','pdf_grid.py','transport.py','gate.py','audit_native.py','audit_pdf_tags.py','requirements.txt'];hashes={}
  for name in names:
   data=(parser/name).read_bytes();atomic(snap/name,data);hashes[name]=digest(data)
  identity=meta['identity'];inventory=json.loads((out/'inventory.json').read_text());requests=json.loads((out/'requests.json').read_text());entry=requests['native-export'];raw=(out/entry['file']).read_bytes();assert digest(raw)==entry['sha256'],'Corrupt original native file'
  assets=json.loads((out/'assets.json').read_text());ledger={a['url']:a for a in assets};resolved={u for u,a in ledger.items() if a['status']=='image-placeholder'}
  toc={n['document_id']:{'url':requests['start:toc:'+n['document_id']]['requested_url'],'sha256':requests['start:toc:'+n['document_id']]['sha256']} for n in inventory['nodes'] if n['has_children']}
  records=native_records(raw,inventory,identity,entry['requested_url'],entry['sha256'],resolved,inventory_sources=toc);pages=[]
  for url,metadata in normalize_pdf_assets(ledger,pages,lambda a:(out/a['file']).read_bytes()).items():ledger[url].update(metadata)
  bind_reference_graph(records,inventory)
  for name,data in output_bytes(records,pages).items():atomic(out/name,data)
  save(out/'assets.json',list(ledger.values()))
  assert all(digest((parser/name).read_bytes())==value for name,value in hashes.items()),'Parser source changed during replay; execute an immutable snapshot'
  from verify import verify
  coverage=verify(out,compare_report=False);save(out/'coverage.json',coverage)
  save(out/'normalization-replay.json',{'schema_version':1,'kind':'Network-free normalization replay of original immutable acquisition; not a fresh publisher request','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_directory_name':source.name,'original_run_sha256':digest((source/'run.json').read_bytes()),'original_sections_sha256':digest((source/'sections.jsonl').read_bytes()),'native_source_sha256':entry['sha256'],'new_sections_sha256':digest((out/'sections.jsonl').read_bytes()),'parser_sha256':hashes,'python':sys.version,'acquisition_execution_history_unchanged':True})
  return coverage
 except BaseException:
  save(out/'normalization-replay-failed.json',{'kind':'Failed replay, not accepted output'});raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--from',dest='source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(replay(a.source,a.out),indent=2))
