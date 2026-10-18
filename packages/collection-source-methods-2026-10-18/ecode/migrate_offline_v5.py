import sys
sys.dont_write_bytecode=True
import argparse,types,importlib,json,hashlib,socket,subprocess,base64
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import pypdf
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();B=Path(__file__).resolve().parent;source=a.source.resolve();out=a.out.resolve();before={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()};pkg=types.ModuleType('_offline_candidate');pkg.__path__=[str(B/'candidate-v5')];sys.modules['_offline_candidate']=pkg;calls=[]
def no(*a,**k):calls.append('forbidden');raise AssertionError('Offline citation classification forbids network/image/nativePDF decoding')
with patch.object(socket.socket,'connect',no),patch.object(socket,'create_connection',no),patch.object(subprocess,'Popen',no),patch.object(base64,'b64decode',no),patch.object(Image,'open',no),patch.object(pypdf,'PdfReader',no):
 E=importlib.import_module('_offline_candidate.engine');state=json.loads((source/'checkpoint.json').read_text());result=E.adopt(source,out,state['config'],True);(out/'previous-classification-coverage.json').write_bytes((source/'coverage.json').read_bytes())
after={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()};assert before==after and not calls
(B/'migration-receipt-v5.json').write_text(json.dumps({'source_files':before,'source_unchanged':True,'new_requests':0,'forbidden_calls':calls,'nativePDF_parses':0,'new_classification_coverage':result,'scope':'New explicit offline source-classification derivative; original acquisition/sourceversion/accessstop preserved, no freshclosing'},indent=2)+'\n');print(json.dumps({'source_files':len(before),'unresolved_links':len(result['unresolved_links']),'required_assets':result['required_assets'],'complete':result['complete']}))
