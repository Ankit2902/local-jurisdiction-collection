"""Retained native CLI with byte-identical hardlink source retention; no second large-file copy."""
import sys
sys.dont_write_bytecode=True
import pathlib,argparse,os,hashlib,json,time
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H/'captured'))
from collectors.encodeplus import retained_native as n
p=argparse.ArgumentParser();p.add_argument('--config',required=True,type=pathlib.Path);p.add_argument('--input',required=True,type=pathlib.Path);p.add_argument('--receipt',required=True,type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path);a=p.parse_args();source=a.input.resolve();target=a.out.resolve()/'raw/source.pdf';before=(source.stat().st_ino,hashlib.sha256(source.read_bytes()).hexdigest());ordinary=n.atomic_bytes

def retain(path,data):
 path=pathlib.Path(path)
 if path==target:
  assert hashlib.sha256(data).hexdigest()==before[1];path.parent.mkdir(parents=True,exist_ok=True);os.link(source,path);assert source.stat().st_ino==path.stat().st_ino
 else:ordinary(path,data)
n.atomic_bytes=retain;start=time.monotonic();report=n.extract(json.loads(a.config.read_text()),source,a.receipt,a.out);assert before==(source.stat().st_ino,hashlib.sha256(source.read_bytes()).hexdigest());assert source.stat().st_ino==target.stat().st_ino
(a.out/'shared-source-retention.json').write_text(json.dumps({'method':'read-only byte-identical same-filesystem hardlink; original native bytes not duplicated or rewritten','source_relative_to_output':os.path.relpath(source,a.out),'source_sha256':before[1],'wrapper_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'no_source_mutation':True},indent=2)+'\n');print(json.dumps(report,indent=2))
