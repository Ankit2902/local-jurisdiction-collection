"""Run copied-reader faults and ordinary relocated stdlib-only verifier."""
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
B=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');S=B/'outputs/collection-readiness-poste026685-2026-10-17/ecode-corpus-reader-v1';H=Path(__file__).resolve().parent;PY=B/'github/local-jurisdiction-collection/.collection-runtime/venv/bin/python'
def tree(p):return {str(x.relative_to(p)):hashlib.sha256(x.read_bytes()).hexdigest()for x in p.rglob('*')if x.is_file()}
def execute(command,log,expected,cwd):
 r=subprocess.run([str(x)for x in command],cwd=cwd,text=True,capture_output=True);(H/(log+'.stdout')).write_text(r.stdout);(H/(log+'.stderr')).write_text(r.stderr);assert r.returncode==expected,(command,r.returncode,r.stdout[-500:],r.stderr[-500:]);return r
before=tree(S)
r=execute([PY,'-B',S/'source/test_ecode_html.py',S/'package/evidence/input',S/'actual-standard-proof/read-only-proof.json'],'14-reader-tests',0,H);assert 'Ran 14 tests'in r.stderr and '\nOK\n'in r.stderr
# Both ordinary and -B commands, with -S, must work without site packages and
# create no bytecode. Verifier process has explicit socket/process tripwires.
with tempfile.TemporaryDirectory(prefix='ecode-reader-peer-')as t:
 out=Path(t)/'relocated';shutil.copytree(S/'package',out);tb=tree(out)
 for flags,name in [([], 'ordinary'),(['-B'],'no-bytecode')]:
  wrapper='''import sys,socket,subprocess,runpy,base64\nfrom unittest.mock import patch\nfrom contextlib import ExitStack\ndef no(*a,**k):raise AssertionError("No socket/process/image bytes")\nwith ExitStack()as s:\n for obj,key in [(socket,"create_connection"),(socket.socket,"connect"),(subprocess,"Popen"),(base64,"b64decode")]:s.enter_context(patch.object(obj,key,no))\n sys.argv=[sys.argv[1],"verify","--out",sys.argv[2]]\n runpy.run_path(sys.argv[0],run_name="__main__")\n'''
  env=dict(os.environ);env.pop('PYTHONDONTWRITEBYTECODE',None);env.pop('PYTHONPYCACHEPREFIX',None)
  command=[str(PY),*flags,'-S','-c',wrapper,str(out/'packager-source/package.py'),str(out)];r=subprocess.run(command,cwd='/tmp',text=True,capture_output=True,env=env);(H/(name+'-stdlib-verify.stdout')).write_text(r.stdout);(H/(name+'-stdlib-verify.stderr')).write_text(r.stderr);assert r.returncode==2,(r.returncode,r.stderr,r.stdout);v=json.loads(r.stdout);assert v['package_verified']is True and v['serialization_complete']is True and v['complete']is False and v['downstream_ready']is False;assert tree(out)==tb;assert not list(out.rglob('__pycache__'))
assert tree(S)==before
result={'passed':True,'fault_tests':14,'source_packet_unchanged':True,'ordinary_and_B_stdlib_S_relocated_exit':2,'ordinary_and_B_package_verified':True,'strict_complete_and_downstream_ready':False,'no_bytecode_or_package_writes':True,'subprocess_verifier_guards':'socket.create_connection/socket.connect/subprocess.Popen/base64.b64decode blocked; no site packages/native/image imports','runtime':str(PY)};(H/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
