#!/usr/bin/env python3
"""Stdlib-only portable packet verification; no source normalization or images."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,socket,importlib.abc
from unittest.mock import patch
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def files(root):
 result={}
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink(),'Symlink in frozen proof packet'
  if p.is_file():result[p.relative_to(root).as_posix()]=sha(p)
 return result
class BlockNative(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'PIL','pypdfium2','pdfplumber','pdfminer','pypdf','fitz','cv2','requests','playwright'}:raise AssertionError('No native/image/network dependency during packet verify: '+fullname)
sys.meta_path.insert(0,BlockNative());sys.path.insert(0,str(R/'source'))
def no(*a,**k):raise AssertionError('No network during packet verify')
before=files(R);manifest=json.loads((R/'MANIFEST.json').read_text());assert {k:v for k,v in before.items() if k!='MANIFEST.json'}==manifest['files']
freeze=json.loads((R/'proofs/SOURCE-FREEZE.json').read_text());assert all(sha(R/'source'/n)==h for n,h in freeze['files'].items())
with patch.object(socket.socket,'connect',no),patch.object(socket,'create_connection',no):
 import package
 import audit_export
 results={}
 for name in ['henderson','charter']:
  root=R/'fixtures/packages'/name;p=package.verify(root);assert p['package_verified'] and p['serialization_complete'] and not p['complete']
  c=audit_export.audit(root);assert c['passed'];results[name]={'package_verified':True,'downstream_ready':p['downstream_ready'],'counts':c['counts']}
  proof=json.loads((R/'fixtures'/(name+'-proof')/'read-only-proof.json').read_text());assert proof['verification']['adapter_source_sha256']==sha(R/'source/verify_input.py');assert proof['registry_mapping_verified'] is False
assert files(R)==before
print(json.dumps({'passed':True,'packet_files':len(before),'read_only':True,'publisher_requests':0,'native_or_image_modules_imported':[],'source_normalizers_rerun':False,'actual':results},indent=2))
