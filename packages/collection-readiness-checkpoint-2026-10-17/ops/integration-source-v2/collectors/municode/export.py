"""Observed enabled native PDF export. Full file qualification, never whole-jurisdiction/text-segmentation proof."""
import sys
sys.dont_write_bytecode=True
import argparse,base64,json,hashlib,re,time
from pathlib import Path
from urllib.parse import urlparse
from collect import Browser,api
from model import atomic,read_response,implementation
from pdf_integrity import qualify_pdf
SOURCES={n:(Path(__file__).parent/n).read_bytes() for n in implementation()};SOURCES['export.py']=Path(__file__).read_bytes()
p=argparse.ArgumentParser();p.add_argument('--reference-run',type=Path,required=True);p.add_argument('--product-id',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
if a.out.exists() and any(a.out.iterdir()):raise SystemExit('Fresh export output required')
a.out.mkdir(parents=True,exist_ok=True);cp=json.loads((a.reference_run/'checkpoint.json').read_text());pub=cp['publications'][a.product_id];source=cp['source_url'];expected=cp['expected_identity'];browser=Browser(source,a.out);responses=[];result={'scope':'whole native publisher PDF file; not legal section completeness or whole jurisdiction','publication_complete':False,'jurisdiction_complete':False,'source_url':source,'product_id':int(a.product_id),'responses':responses,'started_at':time.time()}
try:
 def fetch(name,url,binary=False):
  r=browser.request(url,binary);rr=r['response'];body=base64.b64decode(rr.pop('body'));filename='publisher-export.pdf' if binary else name+'.json';atomic(a.out/filename,body);responses.append({'request_url':url,'binary':binary,'body_file':filename,'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'status':rr['status'],'headers':rr['headers'],'final_url':rr['url'],'redirect_hops':rr.get('redirect_hops'),'access_stop':r.get('access_stop')})
  if rr['status']!=200 or r.get('access_stop'):raise ValueError('Export HTTP/access failure')
  return body if binary else json.loads(body)
 parts=urlparse(source).path.split('/');org=fetch('organization','https://library.municode.com/localapi/Organizations/GetByUrlEncodedNames/'+parts[1]+'/'+parts[2]);assert org['ClientID']==cp['client_id'] and org['ClientName'] in expected['client_names'] and org['State']['StateAbbreviation']==expected['state']
 cc=fetch('inventory',api('ClientContent/'+str(cp['client_id'])));matches=[x for x in cc['codes'] if str(x['productId'])==a.product_id and x.get('hasPdfDownloadEnabled') and x.get('hasPdf')];assert len(matches)==1;publication=matches[0]
 job=fetch('job',api('Jobs/latest/'+a.product_id));assert job['Id']==pub['job_id'] and job['ProductId']==int(a.product_id);result['job']=job;result['native_publication_id']=publication['publicationId']
 resolved=fetch('pdf-url',api('PublicationPdfDownload/'+str(publication['publicationId'])));url=resolved if isinstance(resolved,str) else resolved.get('url',resolved.get('Url'));assert url
 body=fetch('native-file',url,True);qualification=qualify_pdf(body);result['format_qualification']=qualification;result['native_file_complete']=qualification['status']=='acquired'
 if qualification['status']!='acquired':raise ValueError(qualification['reason'])
 from pypdf import PdfReader
 import io
 reader=PdfReader(io.BytesIO(body),strict=True);pages=[]
 for number,page in enumerate(reader.pages,1):
  text=page.extract_text() or '';images=0
  resources=page.get('/Resources')
  seen=set()
  def resource_images(resources):
   total=0
   if not resources:return 0
   xobjects=resources.get_object().get('/XObject')
   if not xobjects:return 0
   for value in xobjects.get_object().values():
    key=(getattr(value,'idnum',id(value)),getattr(value,'generation',0))
    if key in seen:continue
    seen.add(key);obj=value.get_object()
    if obj.get('/Subtype')=='/Image':total+=1
    elif obj.get('/Subtype')=='/Form':total+=resource_images(obj.get('/Resources'))
   return total
  images=resource_images(resources);contents=page.get_contents();images+=sum(op==b'INLINE IMAGE' for operands,op in contents.operations) if contents else 0
  pages.append({'physical_page':number,'text':text+('\n[IMAGE]'*images),'detected_direct_nested_and_inline_image_count':images,'image_marker_order':'end-of-page resource/inline-image inventory; unused resources may count; exact reading order not asserted','text_layer_nonempty':bool(text.strip())})
 atomic(a.out/'pages.jsonl',''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in pages).encode());result.update(status='acquired',physical_pages=len(pages),native_PDF_text_layer_extracted=True,legal_section_segmentation_qualified=False,source_header=' '.join(pages[0]['text'].split()),image_extraction=False)
except Exception as e:result.update(status='incomplete',error=type(e).__name__+': '+str(e))
finally:
 result['finished_at']=time.time();result['implementation']={n:hashlib.sha256(b).hexdigest() for n,b in SOURCES.items()}
 for name,h in result['implementation'].items():atomic(a.out/'executed-sources'/h/name,SOURCES[name])
 atomic(a.out/'export-receipt.json',result);browser.close();print(json.dumps(result,indent=2));raise SystemExit(0 if result.get('status')=='acquired' else 2)
