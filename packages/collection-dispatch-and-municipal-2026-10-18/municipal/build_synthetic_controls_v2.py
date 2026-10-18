import sys
sys.dont_write_bytecode=True
import types,importlib,json,socket,subprocess,base64,contextlib
from pathlib import Path
from unittest.mock import patch
from PIL import Image
B=Path(__file__).resolve().parent;src=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/collection-readiness-2026-10-17/ecode/synthetic-standalone-cli-municipal');out=B/'synthetic-controls-v2';m=types.ModuleType('_synthetic');m.__path__=[str(src/'executed-source')];sys.modules['_synthetic']=m;cp=json.loads((src/'checkpoint.json').read_text());responses={}
for art in cp['artifacts']:
 data=(src/art['path']).read_bytes()
 if art['role']=='content':
  raw=data.decode();assert 'Own chapter history.' in raw and 'Complete synthetic section.' in raw
  raw=raw.replace('Own chapter history.','<img src="/synthetic-only-map.png">').replace('<h3>Section 1</h3>','<h3>Section 1<a class="fn" href="1-1#synthetic-note">1</a></h3>').replace('Complete synthetic section.','Table/footnote control.<span class="note" id="synthetic-note">Footnote body.</span>').replace('<td>A</td>','<td><img src="/synthetic-cell.png">Cell caption</td>');data=raw.encode()
 responses[art['url']]=data
class FakeBrowser:
 def __init__(self,*a,**k):pass
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def fetch(self,url):return responses[url],{'url':url,'requested_url':url,'status':200,'headers':{'content-type':'text/html'},'transport':'SYNTHETIC ONLY - IN MEMORY, NO NETWORK','retrieved_at':'2099-01-01'}
 bootstrap=fetch
 def check(self,*a,**k):pass
calls=[]
def no(*a,**k):calls.append('forbidden');raise AssertionError('Synthetic controls forbid network/image decode')
with patch.object(socket.socket,'connect',no),patch.object(socket,'create_connection',no),patch.object(subprocess,'Popen',no),patch.object(base64,'b64decode',no),patch.object(Image,'open',no):
 E=importlib.import_module('_synthetic.engine');browser=importlib.import_module('_synthetic.browser')
 with patch.object(browser,'Browser',FakeBrowser):coverage=E.collect(cp['config'],out)
 verified=E.verify(out);assert verified['verified'] and verified['complete'] and not calls
(B/'synthetic-controls-build-v2.json').write_text(json.dumps({'scope':'Explicitly SYNTHETIC complete source with actual collect/parser/verify against in-memory backend. No realcity/fullproof promotion','coverage':coverage,'verified':verified,'forbidden_calls':calls,'image_bytes_acquired':0},indent=2)+'\n')
