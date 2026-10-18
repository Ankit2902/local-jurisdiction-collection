"""Read-only, network-disabled verification by an explicitly approved frozen snapshot.

Only curated source hashes shipped in readiness-parser-revisions.json may execute.
This tool exposes verify only; frozen acquisition cannot be selected.
"""
import argparse,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();out=Path(args.out).resolve();pkg=Path(__file__).resolve().parents[1]
 try:
  state=json.loads((out/'checkpoint.json').read_text());fingerprint=state['code_fingerprint'];revision=sha(canonical(fingerprint));catalog=json.loads((pkg/'readiness-parser-revisions.json').read_text());approved=next((r for r in catalog['revisions'] if r['fingerprint_sha256']==revision and r['source_fingerprint']==fingerprint),None)
  if catalog['schema_version']!=1 or not approved:raise ValueError('Snapshot is not an approved frozen verification revision; use exact current verify or explicit offline replay into a fresh folder')
  snapshot=out/'executed-source';files={p.name:p for p in snapshot.glob('*.py')}
  if set(files)!=set(fingerprint):raise ValueError('Frozen snapshot module set mismatch')
  for name,p in files.items():
   if p.is_symlink() or not p.resolve().is_relative_to(snapshot.resolve()) or sha(p.read_bytes())!=fingerprint[name]:raise ValueError('Frozen snapshot hash/path mismatch: '+name)
  with tempfile.TemporaryDirectory(prefix='ecode-frozen-verify-') as temp:
   root=Path(temp);target=root/'collectors/ecode';target.mkdir(parents=True);(root/'collectors/__init__.py').write_text('')
   for name,p in files.items():(target/name).write_bytes(p.read_bytes())
   (root/'sitecustomize.py').write_text("import sys\ndef no_network(event,args):\n if event.startswith('socket.') or event=='subprocess.Popen':raise RuntimeError('Frozen verification is network/process disabled')\nsys.addaudithook(no_network)\n")
   child_env=dict(os.environ);child_env['PYTHONPATH']=str(root)
   result=subprocess.run([sys.executable,'-m','collectors.ecode.cli','verify','--out',str(out)],cwd=root,env=child_env,capture_output=True,text=True)
   report=json.loads(result.stdout);report['frozen_source_verification']={'source_fingerprint_sha256':revision,'approved':True,'network_disabled':True,'read_only':True,'scope':'Exact approved executed parser snapshot; acquisition-only current guard is tested separately.'};print(json.dumps(report,ensure_ascii=False,indent=2))
   return result.returncode if result.returncode in [0,2] and report.get('verified') is True else 1
 except Exception as error:
  print(json.dumps({'verified':False,'complete':False,'error':type(error).__name__,'message':str(error)}));return 1
if __name__=='__main__':raise SystemExit(main())
