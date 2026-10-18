import pathlib,sys,json,hashlib,os,contextlib,traceback
from unittest.mock import patch,PropertyMock
OUT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(OUT/'runtime'))
import collect
from bs4 import BeautifulSoup
import pdfplumber,pypdfium2 as pdfium
from pypdf._page import PageObject
from pdfminer.pdftypes import PDFStream
from PIL import Image
c=json.loads((OUT/'config.json').read_text());capture=OUT/'capture';capture.mkdir(exist_ok=True)
def save(name,x):collect.save(OUT/name,x)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
status={'pid':os.getpid(),'started_at':collect.transport.now(),'stage':'opening','publisher_requests':'ordinary shared official transport; no retries/failover/gate changes','image_calls':[]}
save('status.json',status)
def image_forbidden(*args,**kwargs):status['image_calls'].append('forbidden_image_api');save('status.json',status);raise AssertionError('Image access/render/pixels forbidden')
orig=PDFStream.get_data
def stream_guard(stream,*args,**kwargs):
 if getattr(stream.attrs.get('Subtype'),'name',None)=='Image' or ('W' in stream.attrs and 'H' in stream.attrs):return image_forbidden()
 return orig(stream,*args,**kwargs)
try:
 with contextlib.ExitStack() as stack:
  stack.enter_context(patch.object(PDFStream,'get_data',stream_guard))
  stack.enter_context(patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=image_forbidden))
  for obj,names in [(pdfium.PdfPage,['render','get_objects']),(pdfium.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open'])]:
   for n in names:
    if hasattr(obj,n):stack.enter_context(patch.object(obj,n,image_forbidden))
  page,meta,ref=collect.fetch_raw(capture,'discovery',c['source_url'],c)
  soup=BeautifulSoup(page,'html.parser');groups=soup.select(c['source_currency_selector']);assert len(groups)==1,'Current source group missing or nonunique'
  items,identity=collect.discover(capture,c)
  prior=json.loads((OUT.parent/'clark-title30-discovery-v1/current-inventory.json').read_text())['current_documents']
  assert [(x['url'],x['heading']) for x in items]==[(x['url'],x['label']) for x in prior],'Current source inventory differs; no adjustment/retry'
  save('opening-identity.json',{'identity':identity,'items':items,'source_sha256':hashlib.sha256(page).hexdigest(),'prior_same_bytes':hashlib.sha256(page).hexdigest()==prior[0]['source_page_sha256']})
  collect.save(capture/'config.json',c)
  collect.save(capture/'checkpoint.json',{'scripts':collect.runtime_scripts(),'stage':'capture-only','capture_complete':False,'pid':os.getpid()})
  for index,i in enumerate(items):
   status.update(stage='capture',next_document=index+1,total_documents=len(items));save('status.json',status)
   b,m,r=collect.fetch_raw(capture,'item:'+i['id'],i['url'],c,kind='pdf')
   assert b.startswith(b'%PDF-'),'Expected original native PDF; no normalization/failover'
   assert not m.get('policy_omitted_image'),'Image MIME deliberately omitted; invalid PDF capture'
   print(json.dumps({'capture_document':index+1,'label':i['heading'],'bytes':len(b),'sha256':m['sha256']}),flush=True)
  collect.save(capture/'checkpoint.json',{'scripts':collect.runtime_scripts(),'stage':'capture-only','capture_complete':True,'pid':os.getpid(),'finished_at':collect.transport.now()})
  status.update(stage='capture_terminal_all30_then_standard_collection',capture_finished_at=collect.transport.now());save('status.json',status)
  # Standard collector imports only authentic source-bound successful native files;
  # performs fresh discovery, all-page parse, and actual later page/file responses.
  result=collect.collect(OUT/'config.json',OUT/'run',from_cache=capture)
  status.update(stage='collection_terminal',collection_exit=result,finished_at=collect.transport.now());save('status.json',status)
  raise SystemExit(result)
except BaseException as e:
 if isinstance(e,SystemExit):raise
 status.update(stage='stopped',error=repr(e),traceback=traceback.format_exc(),finished_at=collect.transport.now());save('status.json',status);traceback.print_exc();raise SystemExit(3)
