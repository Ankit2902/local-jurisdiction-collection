"""Standalone public HTTP acquisition using exact public organization route observed in app.
No browser/runtime needed. Reuses unmodified shared Municode rate gate and offline parser.
"""
import argparse,json,hashlib,platform,shutil,re
from pathlib import Path
from urllib.parse import urlparse
from municode_shared import fetch,api,now
from normalize import normalize
from collect_all import URLS
ROOT=Path(__file__).resolve().parents[1]
def run(a):
 name=a['jurisdiction'].lower().replace(' ','-');out=ROOT/'http'/name;out.mkdir(parents=True,exist_ok=True)
 url=URLS[a['sequence']];parts=urlparse(url).path.strip('/').split('/');state,city=parts[:2];product_name=parts[3].replace('_',' ')
 receipt={'url':url,'started_at':now(),'method':'standalone-urllib-observed-public-organization-and-content-api','complete_corpus':False,'status':'failed','runtime':platform.platform(),'python':platform.python_version(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'responses':[],'no_cookies_imported':True}
 shutil.copyfile(__file__,out/'executed-collect_http.py');shutil.copyfile(Path(__file__).with_name('municode_shared.py'),out/'executed-municode_shared.py')
 def get(url,file):
  b,r=fetch(url,out/file);receipt['responses'].append({'url':r['url'],'status':r['http_status'],'file':file,'sha256':r['sha256']});return json.loads(b)
 try:
  org=get('https://library.municode.com/localapi/Organizations/GetByUrlEncodedNames/'+state+'/'+city,'organization.json')
  product=get(api('Products/name',clientId=org['ClientID'],productName=product_name),'product-response.json')['Model'];receipt['product']=product
  job=get(api('Jobs/latest/'+str(product['ProductID'])),'job.json');receipt['job']=job;productId=product['ProductID'];jobId=job['Id']
  toc=get(api('codesToc/fullTree',productId=productId,jobId=jobId,nodeId=productId),'toc-full.json');nodes=[]
  def walk(n,parents=[]):
   nodes.append({**n,'path':parents+[n.get('Heading','')]})
   for c in n.get('Children',[]):walk(c,parents+[n.get('Heading','')])
  walk(toc);receipt['inventory_nodes']=len(nodes);receipt['families_top_level']=[{'id':n['Id'],'heading':n.get('Heading')} for n in toc.get('Children',[])]
  sections=[n for n in nodes if not n.get('HasChildren') and re.match(r'^(?:Sec(?:tion)?\.?\s*|§\s*|[0-9]+[.\-])',n.get('Heading',''),re.I) and not re.search('reserv|comparative|contents',n.get('Heading',''),re.I)][:3]
  if not sections:raise ValueError('No substantive leaf provisions found')
  samples=[]
  for i,n in enumerate(sections):
   content=get(api('CodesContent',productId=productId,jobId=jobId,nodeId=n['Id'],groupChunks='false'),'section-'+str(i)+'.json');samples.append({'node':n,'content':content})
  (out/'samples.json').write_text(json.dumps(samples,indent=2));receipt['selected_nodes']=[{'id':n['Id'],'heading':n['Heading']} for n in sections]
  cc=get(api('ClientContent/'+str(org['ClientID'])),'client-content.json');receipt['publications']=cc.get('codes',[])
  p=next((p for p in receipt['publications'] if p.get('productId')==productId),{})
  receipt['publisher_download']={'status':'unavailable','reason':'ClientContent primary publication does not report both hasPdf and hasPdfDownloadEnabled','publication':p}
  if p.get('hasPdf') and p.get('hasPdfDownloadEnabled') and p.get('publicationId'):
   try:
    pdf=get(api('PublicationPdfDownload/'+str(p['publicationId'])),'pdf-url.json');pdfurl=pdf if isinstance(pdf,str) else pdf.get('url',pdf.get('Url'))
    if not pdfurl:raise ValueError('Unknown publisher PDF URL response shape')
    b,r=fetch(pdfurl,out/'publisher-export-response.bin',timeout=120)
    if not b.startswith(b'%PDF-'):raise ValueError('Publisher response does not have PDF magic')
    (out/'publisher-export-response.bin').replace(out/'publisher-export.pdf');receipt['publisher_download']={'status':'passed','url':pdfurl,'reason':'Automatically acquired publisher-native publication PDF; parsing primary HTML sample only','bytes':len(b),'sha256':r['sha256']}
   except Exception as ex:receipt['publisher_download']={'status':'blocked','reason':str(ex)}
  receipt['status']='acquired'
 except Exception as ex:receipt['error']=str(ex)
 receipt['finished_at']=now();(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
 if receipt['status']=='acquired':report=normalize(out);print(name,'ACQUIRED',report['record_count'],receipt['publisher_download']['status'],flush=True)
 else:print(name,'FAILED',receipt.get('error'),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--target');p.add_argument('--skip-existing',action='store_true');args=p.parse_args()
 for a in json.loads((ROOT/'assignment.json').read_text()):
  name=a['jurisdiction'].lower().replace(' ','-')
  if args.target and name!=args.target:continue
  if not args.target and name in ('fresno','atlanta'):continue
  if args.skip_existing and (ROOT/'http'/name/'receipt.json').exists():continue
  run(a)
