import sys
sys.dont_write_bytecode=True
import json,types,importlib,hashlib,socket,base64
from pathlib import Path
from unittest.mock import patch
B=Path(__file__).resolve().parent
raw=b'<html><body data-cust-id="ZZ9001" data-code-id="10" data-code-date="2026-01-01" data-current-code-id="10" data-customer-name="Synthetic" data-guid="101"><h1 id="pageTitle">Section1</h1><div id="101_title" data-full-title="Section1" data-code-content-type="section"></div><div id="codeContent"><div id="101_content" class="section_content content">Own law.</div><div class="content contentTitle">Outside mandatory law.</div></div></body></html>'
identity={'family':'ecode360','customer_id':'ZZ9001','code_id':'10','currency_raw':'2026-01-01','current_code_id':'10','name':'Synthetic','state':'ZZ'}
results={}
def no(*a,**k):raise AssertionError('Forbidden network/decoder')
with patch.object(socket.socket,'connect',no),patch.object(socket,'create_connection',no),patch.object(base64,'b64decode',no):
 for rev in ['v2','v3']:
  name='_boundary_'+rev;p=types.ModuleType(name);p.__path__=[str(B/('candidate-'+rev))];sys.modules[name]=p;a=importlib.import_module(name+'.adapters')
  try:
   out=a.parse_ecode(raw,'https://ecode360.com/101',identity);results[rev]={'accepted':True,'record_texts':[r['text'] for r in out['records']]}
  except Exception as e:results[rev]={'accepted':False,'error':type(e).__name__+': '+str(e)}
assert results['v2']['accepted'] and not results['v3']['accepted']
(B/'unknown-content-boundary-before-after.json').write_text(json.dumps({'source_html':raw.decode(),'source_sha256':hashlib.sha256(raw).hexdigest(),'results':results,'publisher_requests':0,'pixel_decodes':0,'scope':'Synthetic failclosed boundary, not an actual Albany exposure'},indent=2)+'\n')
print(json.dumps(results))
