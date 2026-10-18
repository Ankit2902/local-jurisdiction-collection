"""Whole actual package copy, shipped CLI, and source/destination hash equality."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,shutil,subprocess,tempfile,time
from pathlib import Path
B=Path(__file__).resolve().parent;source=B/'package'
def files(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}
before=files(source);start=time.time()
with tempfile.TemporaryDirectory(prefix='al-cleveland-corpus-relocation-') as d:
 dest=Path(d)/'portable';shutil.copytree(source,dest);assert files(dest)==before
 cmd=[sys.executable,'-S',str(B/'guarded_verify.py'),str(dest)];run=subprocess.run(cmd,cwd=d,capture_output=True,text=True);assert run.returncode==0,(run.stdout,run.stderr)
 assert files(dest)==before and files(source)==before
 result=json.loads(next(l for l in run.stdout.splitlines() if l.startswith('GUARDED_RESULT ')).removeprefix('GUARDED_RESULT '));receipt={'passed':True,'guarded_result':result,'argv':cmd,'relocated_outside_project':True,'source_files':len(before),'source_destination_before_after_equal':True,'files':before,'stdout':run.stdout,'stderr':run.stderr,'seconds':time.time()-start,'guarded_script_sha256':hashlib.sha256((B/'guarded_verify.py').read_bytes()).hexdigest(),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(B/'relocation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ['files','stdout','stderr']},indent=2))
