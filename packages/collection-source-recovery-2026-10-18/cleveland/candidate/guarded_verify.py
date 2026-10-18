"""Run shipped pure verifier with no outside-input reads, writes, network/images."""
import sys
sys.dont_write_bytecode=True
import base64,builtins,contextlib,hashlib,importlib.abc,io,json,os,runpy,socket,subprocess,sysconfig,time,urllib.request
from pathlib import Path
from unittest.mock import patch
root=Path(sys.argv[1]).resolve();pythonlib=Path(sysconfig.get_path('stdlib')).resolve();executable=Path(sys.executable).resolve();calls=[];reads=[];started=time.time()
def no(*a,**k):calls.append('forbidden_network_image_or_process');raise AssertionError(calls[-1])
def path_allowed(p):return p.is_relative_to(root) or (p.is_relative_to(pythonlib) and 'site-packages' not in p.parts) or p==executable
original_open=builtins.open;original_io=io.open;original_os=os.open
def check(file,mode):
 if isinstance(file,int):return
 p=Path(file).resolve();assert not any(x in str(mode) for x in ['w','a','x','+']),('write',str(p),mode)
 if not path_allowed(p):calls.append('outside_read:'+str(p));raise AssertionError(calls[-1])
 reads.append(str(p))
def guarded_open(file,mode='r',*a,**k):check(file,mode);return original_open(file,mode,*a,**k)
def guarded_io(file,mode='r',*a,**k):check(file,mode);return original_io(file,mode,*a,**k)
def guarded_os(file,flags,*a,**k):
 assert not flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
 check(file,'r');return original_os(file,flags,*a,**k)
class RejectThirdParty(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in ['PIL','bs4','fitz','pymupdf','pdfminer','pypdf','pdfplumber','pypdfium2','playwright','requests']:calls.append('third_party_import:'+fullname);raise AssertionError(calls[-1])
sys.meta_path.insert(0,RejectThirdParty());sys.path.insert(0,str(root/'packager-source'));sys.argv=[str(root/'packager-source/package.py'),'verify','--out',str(root)]
with contextlib.ExitStack() as g:
 for obj,name in [(socket.socket,'connect'),(socket,'create_connection'),(subprocess,'Popen'),(urllib.request,'urlopen'),(base64,'b64decode'),(base64,'decodebytes')]:g.enter_context(patch.object(obj,name,no))
 g.enter_context(patch.object(builtins,'open',guarded_open));g.enter_context(patch.object(io,'open',guarded_io));g.enter_context(patch.object(os,'open',guarded_os))
 try:runpy.run_path(str(root/'packager-source/package.py'),run_name='__main__');exit_code=0
 except SystemExit as e:exit_code=e.code
assert exit_code==2 and not calls
print('GUARDED_RESULT '+json.dumps({'passed':True,'exit_code':exit_code,'forbidden_calls':calls,'unique_read_files':len(set(reads)),'third_party_imports_allowed':False,'seconds':time.time()-started,'shipped_entrypoint':'packager-source/package.py','ordinary_no_B':True}))
