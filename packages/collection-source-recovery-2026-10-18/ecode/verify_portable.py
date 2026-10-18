import sys
sys.dont_write_bytecode=True
import argparse,json,hashlib,tempfile,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();root=a.package.resolve()
def tree(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(r.rglob('*')) if p.is_file()}
before=tree(root)
with tempfile.TemporaryDirectory(prefix='ecode-corrected-portable-') as t:
 relocated=Path(t)/'package';shutil.copytree(root,relocated);cmd=[sys.executable,'-B','-S',str(relocated/'packager-source/package.py'),'verify','--out',str(relocated)];r=subprocess.run(cmd,cwd='/tmp',text=True,capture_output=True);report=json.loads(r.stdout);assert r.returncode==2 and report['package_verified'] is True and report['complete'] is False;assert before==tree(relocated)
assert before==tree(root)
a.out.write_text(json.dumps({'command_template':'$ECODE_PY -B -S RELOCATED/packager-source/package.py verify --out RELOCATED','cwd':'/tmp','returncode':r.returncode,'report':report,'stderr':r.stderr,'input_files':len(before),'source_and_relocated_evidence_unchanged':True,'source_sha256':before,'scope':'Actual relocated stdlib-only shipped verifier; no source normalization or publisher requests'},indent=2)+'\n')
print(json.dumps({'returncode':r.returncode,'package_verified':True,'complete':False,'input_files':len(before),'unchanged':True}))
