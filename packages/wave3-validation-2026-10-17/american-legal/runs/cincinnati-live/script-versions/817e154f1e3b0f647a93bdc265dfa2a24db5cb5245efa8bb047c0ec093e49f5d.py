#!/usr/bin/env python3
"""Bounded live direct public Municode endpoints; current app routes, shared rate gate, no retries."""
import argparse,datetime,json,pathlib,platform,sys,urllib.parse,hashlib,shutil
from municode_shared import fetch,api
from normalize import normalize
ROOT=pathlib.Path(__file__).resolve().parents[1]
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def slug(row):return row['jurisdiction'].lower().replace(' ','_')+'-'+row['state'].lower()
def get(url,out):return json.loads(fetch(url,out)[0])
def acquire(row,out):
 out.mkdir(parents=True,exist_ok=True);url='https://library.municode.com/'+row['state'].lower()+'/'+row['jurisdiction'].lower().replace(' ','_')+'/codes/code_of_ordinances'
 receipt={'url':url,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'standalone-python-public-application-api','runtime':platform.python_version(),'os':platform.platform(),'complete_corpus':False,'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'publisher_download':{'status':'not_tested','reason':'Acquisition did not reach export inventory'}}
 versions=out/'script-versions';versions.mkdir(exist_ok=True)
 for fn in ['acquire.py','municode_shared.py','normalize.py']:
  p=ROOT/'scripts'/fn;shutil.copy2(p,versions/(hashlib.sha256(p.read_bytes()).hexdigest()+p.suffix))
 try:
  org=get('https://library.municode.com/localapi/Organizations/GetByUrlEncodedNames/'+row['state'].lower()+'/'+row['jurisdiction'].lower().replace(' ','_'),out/'organization.json')
  assert org['State']['StateAbbreviation']==row['state'] and org['ClientName'].lower()==row['jurisdiction'].lower(), 'Organization identity mismatch'
  cc=get(api('ClientContent/'+str(org['ClientID'])),out/'client-content.json');receipt['publications']=cc.get('codes',[])
  product=get(api('Products/name',clientId=org['ClientID'],productName='code of ordinances'),out/'product-envelope.json')['Model']
  assert product['Client']['ClientID']==org['ClientID'],'Product client mismatch'
  dump(out/'product.json',product);receipt['product']=product
  job=get(api('Jobs/latest/'+str(product['ProductID'])),out/'job.json');receipt['job']=job
  pid=product['ProductID'];jid=job['Id'];tree=get(api('codesToc/fullTree',productId=pid,jobId=jid,nodeId=pid),out/'toc-full.json');nodes=[]
  def walk(n,parents=[]):
   if n.get('Id'):nodes.append({**n,'path':parents+[n.get('Heading','')]})
   for c in n.get('Children',[]):walk(c,parents+[n.get('Heading','')])
  walk(tree);receipt['inventory_nodes']=len(nodes);receipt['families_top_level']=[{'id':n.get('Id'),'heading':n.get('Heading')} for n in tree.get('Children',[])]
  import re
  leaves=[n for n in nodes if not n.get('HasChildren') and not n.get('Children') and re.match(r'^(?:Sec(?:tion)?\.?\s*|§\s*|[0-9]+[.\-])[0-9a-zA-Z.\-]*',n.get('Heading',''),re.I) and not re.search('reser|comparative|contents',n.get('Heading',''),re.I)]
  pref=[n for n in leaves if not any(re.search('charter|constitution',x,re.I) for x in n['path'])];selected=(pref or leaves)[:3]
  assert len(selected)>=2,'Fewer than 2 substantive leaves observed'
  samples=[]
  for i,n in enumerate(selected):samples.append({'node':n,'content':get(api('CodesContent',productId=pid,jobId=jid,nodeId=n['Id'],groupChunks='false'),out/f'content-{i}.json')})
  dump(out/'samples.json',samples);receipt['selected_nodes']=[{'id':n['Id'],'heading':n['Heading']} for n in selected]
  pub=next((p for p in cc.get('codes',[]) if p.get('productId')==pid and p.get('hasPdf') and p.get('hasPdfDownloadEnabled')),None)
  if pub and pub.get('publicationId'):
   try:
    pdf=get(api('PublicationPdfDownload/'+str(pub['publicationId'])),out/'pdf-url.json');pdfurl=pdf if isinstance(pdf,str) else pdf.get('url',pdf.get('Url'))
    assert pdfurl,'Unknown PDF URL response shape'
    data,r=fetch(pdfurl,out/'publisher-export.pdf');assert data.startswith(b'%PDF-'),'Not PDF'
    receipt['publisher_download']={'status':'passed','url':pdfurl,'reason':'Original publisher-native PDF acquired automatically via published export feature','publication_id':pub['publicationId'],'bytes':len(data),'sha256':r['sha256']}
   except Exception as e:receipt['publisher_download']={'status':'blocked','reason':str(e),'publication_id':pub['publicationId']}
  else:receipt['publisher_download']={'status':'unavailable','reason':'ClientContent inventory does not expose an enabled native PDF for this primary publication; separate official alternatives inventoried'}
  receipt['status']='acquired'
 except Exception as e:receipt.update(status='failed',error=str(e))
 receipt['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(out/'receipt.json',receipt)
 if receipt['status']=='acquired':normalize(out)
 return {'slug':slug(row),'status':receipt['status'],'error':receipt.get('error'),'publisher_download':receipt['publisher_download']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--sequence',type=int);p.add_argument('--skip-sequence',type=int,action='append',default=[]);p.add_argument('--out',type=pathlib.Path);p.add_argument('--offline',action='store_true');a=p.parse_args()
 for row in json.loads((ROOT/'assignment.json').read_text()):
  if (a.sequence and row['sequence']!=a.sequence) or row['sequence'] in a.skip_sequence:continue
  out=a.out if a.out else ROOT/'direct'/slug(row)
  if a.offline:
   if (out/'samples.json').exists():print(json.dumps(normalize(out)),flush=True)
   else:print(json.dumps({'slug':slug(row),'status':'no retained legal sample to replay'}),flush=True)
  elif (out/'receipt.json').exists():print(json.dumps({'slug':slug(row),'status':'already_attempted; use --out new-directory for a fresh live run'}),flush=True)
  else:print(json.dumps(acquire(row,out)),flush=True)
