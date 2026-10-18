import sys
sys.dont_write_bytecode=True
import json,hashlib,socket,subprocess,base64,types,importlib
from pathlib import Path
from unittest.mock import patch
B=Path(__file__).resolve().parent;source=Path(sys.argv[1]);out=Path(sys.argv[2]);pkg=types.ModuleType('_candidate');pkg.__path__=[str(B/'candidate-v3')];sys.modules['_candidate']=pkg
before={str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in source.rglob('*') if f.is_file()};calls=[]
def no(*a,**k):calls.append('forbidden');raise AssertionError('Offline derivative forbids network/process/image decode')
with patch.object(socket.socket,'connect',no),patch.object(socket,'create_connection',no),patch.object(subprocess,'Popen',no),patch.object(base64,'b64decode',no):
 from PIL import Image
 with patch.object(Image,'open',no):
  E=importlib.import_module('_candidate.engine');state=json.loads((source/'checkpoint.json').read_text());result=E.adopt(source,out,state['config'],True)
  (out/'source-coverage-original.json').write_bytes((source/'coverage.json').read_bytes())
  verified=E.verify(out)
after={str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in source.rglob('*') if f.is_file()};assert before==after and not calls
(B/'actual-derivative-v3-receipt.json').write_text(json.dumps({'source':str(source),'output':str(out),'original_source_files':before,'source_unchanged':True,'forbidden_calls':calls,'new_publisher_requests':0,'original_coverage':json.loads((source/'coverage.json').read_text()),'derived_coverage':result,'standard_verify':verified,'scope':'Explicit fresh offline parser derivative; original raw/version/error/stop provenance retained, no new acquisition or closing evidence.'},indent=2)+'\n');print(json.dumps({'verified':verified['verified'],'complete':verified['complete'],'normalized_records':verified['normalized_records'],'required_assets':verified['required_assets'],'source_unchanged':True,'forbidden_calls':calls}))
