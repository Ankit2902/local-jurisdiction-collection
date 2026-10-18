"""Image-free guarded ordinary official collector; exact runtime beside this file."""
import argparse,contextlib,hashlib,io,json,os,pathlib,sys,traceback
from unittest.mock import patch,PropertyMock
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'runtime'))
import collect
sys.path.insert(0,str(HERE.parent/'scripts'))
from fetch_observed import preflight
EXPECTED={'Subdivision and Site Plan Review Regulations','Zoning Ordinance'}
def native_source(data,item):
 pins=json.loads((HERE/'native-pins.json').read_text())['documents']
 if item['url']not in pins:raise ValueError('Native source URL not in observed edition inventory')
 p=pins[item['url']]
 if item['heading']!=p['heading']or len(data)!=p['bytes']or hashlib.sha256(data).hexdigest()!=p['sha256']:raise ValueError('Native source edition/hash/identity differs before parsing')
 return p
def selected(items):
 if len(items)!=2 or len({x['url']for x in items})!=2 or {x['heading']for x in items}!=EXPECTED:raise ValueError('Both exact distinct current source-published zoning/subdivision files are required')
 if any(not x['url'].startswith('https://www.manchesternh.gov/Portals/2/Departments/pcd/')for x in items):raise ValueError('Observed native document host/path changed')
 return items
@contextlib.contextmanager
def guards(calls,offline=False):
 import pypdfium2 as pdfium,pdfplumber,urllib.request,socket
 from pypdf.generic import EncodedStreamObject,DecodedStreamObject
 from pypdf._page import PageObject
 from pdfminer.pdftypes import PDFStream
 from PIL import Image
 def deny(*a,**k):calls.append('forbidden_image_or_offline_network_operation');raise AssertionError(calls[-1])
 def wrap(original):
  def check(stream,*a,**k):
   attrs=getattr(stream,'attrs',None);d=attrs if attrs is not None else stream
   subtype=d.get('Subtype',d.get('/Subtype'))
   if str(subtype).strip("/'").lower()=='image' or any(k in d for k in ['W','Width','/W','/Width'])and any(k in d for k in ['H','Height','/H','/Height']):return deny()
   return original(stream,*a,**k)
  return check
 with contextlib.ExitStack()as s:
  for cls in [PDFStream,EncodedStreamObject,DecodedStreamObject]:s.enter_context(patch.object(cls,'get_data',wrap(cls.get_data)))
  s.enter_context(patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=deny))
  for obj,names in [(pdfium.PdfPage,['render','get_objects']),(pdfium.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open','frombytes','fromarray','frombuffer'])]:
   for name in names:
    if hasattr(obj,name):s.enter_context(patch.object(obj,name,deny))
  for name in ['FPDFImageObj_GetBitmap','FPDFImageObj_GetRenderedBitmap','FPDFImageObj_GetImageDataDecoded','FPDFImageObj_GetImageDataRaw']:
   if hasattr(pdfium.raw,name):s.enter_context(patch.object(pdfium.raw,name,deny))
  if offline:
   s.enter_context(patch.object(socket,'socket',deny));s.enter_context(patch.object(urllib.request,'urlopen',deny));s.enter_context(patch.object(collect.transport,'fetch',deny))
  yield
  if calls:raise AssertionError('Forbidden operation attempted')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['capture','collect','verify']);p.add_argument('--job',type=pathlib.Path,required=True);p.add_argument('--resume',action='store_true');a=p.parse_args();job=a.job.resolve();cfg=json.loads((HERE/'config.json').read_text());job.mkdir(parents=True,exist_ok=True)
 original=collect.transport.reserve
 def reserve(url):preflight(url);return original(url)
 collect.transport.reserve=reserve
 old_discover=collect.discover
 def discover(*args,**kwargs):
  items,identity=old_discover(*args,**kwargs);selected(items);return items,identity
 collect.discover=discover
 original_parse=collect.parse_item
 def parse(data,item,config):
  pin=native_source(data,item);rows,dispositions=original_parse(data,item,config)
  if len(rows)!=pin['physical_pages']:raise ValueError('Pinned native physical page coverage changed')
  return rows,dispositions
 collect.parse_item=parse
 calls=[];status={'stage':a.stage,'pid':os.getpid(),'started_at':collect.transport.now(),'forbidden_calls':calls,'runtime':collect.runtime_scripts(),'driver_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'native_pins_sha256':hashlib.sha256((HERE/'native-pins.json').read_bytes()).hexdigest()}
 def save():collect.save(job/(a.stage+'-status.json'),status)
 save()
 try:
  with guards(calls,offline=a.stage=='verify'):
   if a.stage=='capture':
    from pypdf import PdfReader
    import pypdfium2 as pdfium
    cap=job/'capture';cap.mkdir(exist_ok=True);items,identity=collect.discover(cap,cfg);meta=[]
    for i in items:
     b,m,ref=collect.fetch_raw(cap,'item:'+i['id'],i['url'],cfg,kind='pdf');assert b.startswith(b'%PDF-')and m['headers'].get('Content-Type','').split(';')[0]=='application/pdf'
     reader=PdfReader(io.BytesIO(b),strict=True);count=len(reader.pages);doc=pdfium.PdfDocument(b);assert count==len(doc)
     text=[]
     for k in range(min(3,count)):
      page=doc[k];tp=page.get_textpage();text.append(tp.get_text_range());tp.close();page.close()
     doc.close();meta.append({'url':i['url'],'heading':i['heading'],'raw_ref':ref,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'physical_pages':count,'first_three_text_pages':text,'metadata':{str(k):str(v)for k,v in(reader.metadata or {}).items()}})
    collect.save(cap/'config.json',cfg);collect.save(cap/'checkpoint.json',{'scripts':collect.runtime_scripts(),'phase':'capture-only','capture_complete':True,'items':items,'identity':identity,'finished_at':collect.transport.now()});collect.save(job/'opening-native-metadata.json',meta);status.update(native_documents=len(meta),physical_pages=sum(x['physical_pages']for x in meta));result=0
   elif a.stage=='collect':
    assert (job/'capture/checkpoint.json').exists(),'Capture/inspect all native source page counts first'
    result=collect.collect(HERE/'config.json',job/'run',resume=a.resume,from_cache=None if a.resume else job/'capture')
   else:
    from verify import verify
    result=verify(job/'run');collect.save(job/'readonly-report.json',result);result=0 if result.get('requested_coverage_complete')else 3
  status.update(terminal_exit=result,finished_at=collect.transport.now());save();return result
 except BaseException as e:
  status.update(error=repr(e),finished_at=collect.transport.now(),terminal_exit=3);save();traceback.print_exc();return 3
if __name__=='__main__':raise SystemExit(main())
