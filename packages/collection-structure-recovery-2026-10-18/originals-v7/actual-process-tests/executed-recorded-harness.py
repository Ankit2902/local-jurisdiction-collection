"""Run actual collect CLI with strictly offline recorded publisher responses; NOT live transport proof."""
import sys,os,json,base64,socket,shutil,time,hashlib
from pathlib import Path
from types import SimpleNamespace
source=Path(os.environ['ORIGINALS_TEST_SOURCE']);runtime=Path(os.environ['ORIGINALS_TEST_RUNTIME']);proof=Path(os.environ['ORIGINALS_TEST_PROOF']);proof.mkdir(exist_ok=True);sys.path.insert(0,str(runtime))
def forbidden(*a,**kw):raise AssertionError('Actual network forbidden in recorded-source recovery test')
socket.socket.connect=forbidden;socket.create_connection=forbidden
import shared_transport as transport,flagstaff_html,flagstaff_inventory,cli
responses={}
for a in json.loads((source/'checkpoint.json').read_text())['artifacts']:
 responses.setdefault(a['source_url'],((source/a['path']).read_bytes(),dict(a.get('headers',{}))))
for a in json.loads((source/'inventory-origin/network-bodies.json').read_text()):
 if a.get('path'):responses.setdefault(a['url'],((source/'inventory-origin'/a['path']).read_bytes(),dict(a.get('headers',{}))))
events=proof/('resume-transport.jsonl' if '--resume' in sys.argv else 'initial-transport.jsonl')
def record(v):
 with events.open('a') as f:f.write(json.dumps(v)+'\n')
transport.reserve=lambda u:record({'event':'offline_gate_intent','url':u,'actual_publisher_request':False})
class Req:
 def __init__(self,url,kind):self.url=url;self.resource_type=kind
class Route:
 def __init__(self,request):self.request=request;self.allowed=False
 def continue_(self):self.allowed=True
 def abort(self):raise RuntimeError('Recorded request refused by production route')
class Response:
 def __init__(self,url,kind):
  self.url=url;self.request=Req(url,kind);self.status=200;self.raw,self.headers=responses[url];self.headers=dict(self.headers,**{'x-complisolv-test-transport':'offline-retained-source'})
 def body(self):return self.raw
class Page:
 def __init__(self,context):self.context=context
 def request(self,url,kind):
  if url not in responses:raise AssertionError('Unrecorded URL: no network fallback '+url)
  route=Route(Req(url,kind));self.context.handler(route)
  if not route.allowed:raise AssertionError('Production route did not continue recorded request')
  r=Response(url,kind)
  for f in self.context.handlers.get('response',[]):f(r)
  record({'event':'recorded_response','url':url,'sha256':hashlib.sha256(r.raw).hexdigest(),'actual_publisher_request':False})
  if os.environ.get('ORIGINALS_TEST_PAUSE')=='before_currency' and url==flagstaff_html.CURRENCY_URL and '--resume' not in sys.argv:
   (proof/'before-currency-response.marker').write_text(json.dumps({'url':url,'pid':os.getpid(),'response_not_returned_to_collector':True})+'\n')
   while True:time.sleep(.1)
  return r
 def goto(self,url,**kw):return self.request(url,'document')
 def evaluate(self,script,url):
  r=self.request(url,'fetch');return {'url':url,'status':r.status,'headers':r.headers,'data':base64.b64encode(r.raw).decode()}
class Context:
 def __init__(self):self.handlers={}
 def route(self,pattern,handler):self.handler=handler
 def on(self,name,handler):self.handlers.setdefault(name,[]).append(handler)
 def new_page(self):return Page(self)
 def close(self):record({'event':'own_fake_context_closed','real_browser':False})
class Browser:
 version='OFFLINE_RECORDED_TRANSPORT_NOT_LIVE_BROWSER'
 def new_context(self,**kw):return Context()
 def close(self):record({'event':'own_fake_browser_closed','real_browser':False})
class PW:
 def __enter__(self):return SimpleNamespace(chromium=SimpleNamespace(launch=lambda **kw:Browser()))
 def __exit__(self,*args):return False
flagstaff_html.sync_playwright=lambda:PW()
def inventory(out):
 shutil.copytree(source/'inventory-origin',out);meta=json.loads((out/'receipt.json').read_text());record({'event':'historical_inventory_stage_replayed','actual_publisher_request':False});return meta
flagstaff_inventory.run=inventory
sys.exit(cli.main(sys.argv[1:]))
