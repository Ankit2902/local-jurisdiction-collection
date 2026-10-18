"""Pinned whole6-source audit under independent image/network tripwires."""
import contextlib,hashlib,json,subprocess,sys,time
from pathlib import Path
from unittest.mock import patch
P=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/collection-readiness-post-1997ee1-2026-10-17/american-legal/overland-solid-waste-logical-v1');R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();snapshot=lambda:{p.relative_to(P).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
assert sha(P/'MANIFEST.json')=='cce2d60c7285b2610575f914f0aba51bc57076ab77e5f749b9f0141c83bf4e7a'
m=json.loads((P/'MANIFEST.json').read_text())
for e in m['files']:assert sha(P/e['path'])==e['sha256'] and (P/e['path']).stat().st_size==e['bytes']
before=snapshot();(R/'candidate-before.json').write_text(json.dumps(before,indent=2)+'\n');sys.path.insert(0,str(P/'source'))
import independent_audit,pymupdf
from PIL import Image
from pypdf.generic import EncodedStreamObject,DecodedStreamObject
calls=[]
def no(*a,**kw):calls.append('image_or_network');raise AssertionError('No image decode/extract/render/OCR/network')
with contextlib.ExitStack() as s:
 for obj,name in [('socket','socket'),('socket','create_connection'),(Image,'open'),(pymupdf.Document,'extract_image'),(pymupdf.Page,'get_pixmap')]:s.enter_context(patch(obj+'.'+name,side_effect=no) if isinstance(obj,str) else patch.object(obj,name,no))
 for cls in [EncodedStreamObject,DecodedStreamObject]:
  old=cls.get_data
  def guard(self,*a,_old=old,**kw):
   if str(self.get('/Subtype','')).lower()=='/image':return no()
   return _old(self,*a,**kw)
  s.enter_context(patch.object(cls,'get_data',guard))
 t=time.monotonic();result=independent_audit.audit((P/'source.pdf').read_bytes(),P/'canonical-final-v2');elapsed=time.monotonic()-t
assert result['passed'] and calls==[];result.update(independent_review_tripwire_calls=calls,seconds=elapsed)
(R/'whole6-native-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('auditPASS',elapsed,flush=True)
t=time.monotonic();run=subprocess.run([sys.executable,'-B',str(P/'source/test_logical.py')],cwd=P,capture_output=True,text=True);(R/'fault-tests.stdout').write_text(run.stdout);(R/'fault-tests.stderr').write_text(run.stderr);(R/'fault-tests-terminal.json').write_text(json.dumps({'argv':[sys.executable,'-B',str(P/'source/test_logical.py')],'exit':run.returncode,'seconds':time.monotonic()-t},indent=2)+'\n');assert run.returncode==0;print('21faultsPASS',flush=True)
after=snapshot();assert before==after;assert len(before)==96;(R/'candidate-after.json').write_text(json.dumps(after,indent=2)+'\n');print('readonlyPASS96',flush=True)
