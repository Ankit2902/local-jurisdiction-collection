"""Both shipped CLI forms, original paths inaccessible, no bytecode or writes."""
import hashlib,json,os,platform,shutil,subprocess,sys,tempfile
from pathlib import Path
def tree(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}
root=Path(sys.argv[1]).resolve();before=tree(root);results=[]
program='''import contextlib,io,json,pathlib,runpy,socket,sys
root=pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root/'packager-source'))
original=pathlib.Path.open
denied=[]
def guarded(self,*a,**kw):
    if not self.resolve().is_relative_to(root):
        denied.append(str(self));raise AssertionError('Outside relocated package read')
    mode=a[0] if a else kw.get('mode','r')
    if any(c in mode for c in 'wax+'):raise AssertionError('Verifier attempted write')
    return original(self,*a,**kw)
pathlib.Path.open=guarded
socket.socket=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Network forbidden'))
initial=sys.dont_write_bytecode
sys.argv=[str(root/'packager-source/package.py'),'verify','--out',str(root)]
output=io.StringIO();code=0
with contextlib.redirect_stdout(output):
    try:runpy.run_path(sys.argv[0],run_name='__main__')
    except SystemExit as e:code=e.code
print(json.dumps({'result':json.loads(output.getvalue()),'outside_package_reads':denied,'dont_write_bytecode_before_entrypoint':initial,'dont_write_bytecode_after_entrypoint':sys.dont_write_bytecode,'cli_exit':code}))
sys.exit(code)
'''
environment=dict(os.environ);environment.pop('PYTHONDONTWRITEBYTECODE',None);environment.pop('PYTHONPYCACHEPREFIX',None)
with tempfile.TemporaryDirectory(prefix='corpus-package-no-bytecode-') as temp:
    moved=Path(temp)/'jurisdiction';shutil.copytree(root,moved);assert tree(moved)==before
    for flags in [[],['-B']]:
        result=subprocess.run([sys.executable,*flags,'-c',program,str(moved)],capture_output=True,text=True,cwd=temp,env=environment)
        assert result.returncode==2,(result.stdout,result.stderr)
        details=json.loads(result.stdout);assert details['result']['package_verified'] is True and not details['outside_package_reads'] and details['dont_write_bytecode_after_entrypoint'] is True
        assert details['dont_write_bytecode_before_entrypoint']==bool(flags)
        assert tree(moved)==before and not list(moved.rglob('__pycache__'))
        results.append({'flags':flags,'details':details})
assert tree(root)==before
print(json.dumps({'passed':True,'source_reparsed':False,'original_input_paths_accessible_to_verifier':False,'outside_package_file_reads':0,'network_requests':0,'writes':0,'added_bytecode_files_or_directories':0,'package_before_after_equal':True,'python':sys.version,'platform':platform.platform(),'modes':results},indent=2))
