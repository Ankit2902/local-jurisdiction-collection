"""Own guarded ordinary no-B, -S shipped verifier from unrelated directory."""
import hashlib,json,pathlib,shutil,subprocess,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parents[5];O=pathlib.Path(__file__).resolve().parent;B=P/'outputs/collection-readiness-post9ef7220-2026-10-17/municipal-corpus-reader-v1';Q=B/'package-v3'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tree(p):return {str(f.relative_to(p)):h(f) for f in p.rglob('*') if f.is_file()}
before=tree(Q);t=time.monotonic()
code="""import sys,runpy,socket,subprocess,base64,builtins,json
forbidden=[]
def no(*a,**k):forbidden.append('forbidden_call');raise AssertionError('network/process/image decoder forbidden')
socket.create_connection=no;socket.socket.connect=no;subprocess.Popen=no;base64.b64decode=no
original=builtins.__import__
def imports(name,*a,**k):
 if name.split('.')[0] in ['PIL','fitz','pdfplumber','pypdfium2','requests','playwright']:forbidden.append('import:'+name);raise AssertionError('Unexpected image/transport/native import')
 return original(name,*a,**k)
builtins.__import__=imports
src=sys.argv[1];out=sys.argv[2];sys.path.insert(0,src);sys.argv=[src+'/package.py','verify','--out',out]
try:runpy.run_path(src+'/package.py',run_name='__main__')
except SystemExit as e:
 print('PEER_GUARDS='+json.dumps({'forbidden_calls':forbidden,'no_site':'site' not in sys.modules,'dont_write_bytecode':sys.dont_write_bytecode}));raise
"""
with tempfile.TemporaryDirectory(prefix='municipal-peer-relocated-') as td:
 dest=pathlib.Path(td)/'copied';shutil.copytree(Q,dest);assert tree(dest)==before
 argv=[sys.executable,'-S','-c',code,str(dest/'packager-source'),str(dest)]
 r=subprocess.run(argv,cwd=td,capture_output=True,text=True,timeout=30)
 assert r.returncode==2,(r.returncode,r.stdout,r.stderr)
 reporttext,guardtext=r.stdout.split('PEER_GUARDS=');report=json.loads(reporttext);guards=json.loads(guardtext)
 assert report['package_verified'] is True and report['complete'] is False and report['selected_publication_ready'] is False and report['downstream_ready'] is False
 assert guards['forbidden_calls']==[] and guards['no_site'] and guards['dont_write_bytecode']
 assert tree(dest)==before and not list(dest.rglob('__pycache__'))
 assert tree(Q)==before
 (O/'relocated-child.log').write_text(r.stdout+r.stderr)
 result={'passed':True,'command':'shared-python -S -c guard-wrapper SHIPPED/packager-source RELOCATED_PACKAGE; ordinary no-B entrypoint from unrelated temporary cwd','child_exit':r.returncode,'package_verified':True,'complete':False,'selected_publication_ready':False,'downstream_ready':False,'guards':guards,'files_before_after_copied_equal':len(before),'original_package_unchanged':True,'package_manifest_sha256':h(Q/'run-manifest.json'),'guard_wrapper_sha256':hashlib.sha256(code.encode()).hexdigest(),'executed_source_sha256':h(pathlib.Path(__file__)),'seconds':time.monotonic()-t,'whole_source_normalization_native_parse_calls':0}
 (O/'relocated-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
