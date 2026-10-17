"""Continue ordinary-browser-discovered public API paths using shared rate-limited HTTP.
Retains prior failed browser run. No IDs guessed, cookies imported or access checks bypassed.
"""
import json,sys,shutil,hashlib,platform
from pathlib import Path
from municode_shared import fetch,api
from normalize import normalize
ROOT=Path(__file__).resolve().parents[1]
def run(name):
 old=ROOT/'browser'/name;r=json.loads((old/'receipt.json').read_text());out=ROOT/'recovery'/name;out.mkdir(parents=True,exist_ok=True)
 product=json.loads((old/next(x['file'] for x in r['responses'] if '/Products/name' in x['url'] and x['status']==200)).read_text())['Model']
 job=json.loads((old/next(x['file'] for x in r['responses'] if '/Jobs/latest/' in x['url'] and x['status']==200)).read_text())
 receipt={'url':r['url'],'product':product,'job':job,'method':'standalone-http-from-retained-browser-bootstrap','status':'failed','complete_corpus':False,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'runtime':platform.platform(),'responses':[],'bootstrap_evidence':str(old.relative_to(ROOT))}
 def get(path,file,**params):
  b,rc=fetch(api(path,**params),out/file);receipt['responses'].append({'url':rc['url'],'status':rc['http_status'],'file':file,'sha256':rc['sha256']});return json.loads(b)
 try:
  productId=product['ProductID'];jobId=job['Id'];toc=get('codesToc/fullTree','toc-full.json',productId=productId,jobId=jobId,nodeId=productId)
  nodes=[]
  def walk(n,parents=[]):
   nodes.append({**n,'path':parents+[n.get('Heading','')]})
   for c in n.get('Children',[]):walk(c,parents+[n.get('Heading','')])
  walk(toc);import re
  sections=[n for n in nodes if not n.get('HasChildren') and re.match(r'^(?:Sec(?:tion)?\.?\s*|§\s*|[0-9]+[.\-])',n.get('Heading',''),re.I) and not re.search('reserv|comparative|contents',n.get('Heading',''),re.I)][:3]
  samples=[{'node':n,'content':get('CodesContent','section-'+str(i)+'.json',productId=productId,jobId=jobId,nodeId=n['Id'],groupChunks='false')} for i,n in enumerate(sections)]
  (out/'samples.json').write_text(json.dumps(samples,indent=2));receipt['families_top_level']=[{'id':n['Id'],'heading':n.get('Heading')} for n in toc.get('Children',[])];receipt['inventory_nodes']=len(nodes)
  try:
   cc=get('ClientContent/'+str(product['Client']['ClientID']),'client-content.json');receipt['publications']=cc.get('codes',[])
  except Exception as ex:receipt['publication_inventory_error']=str(ex)
  receipt['publisher_download']={'status':'unavailable' if not product.get('HasPdf') else 'not_tested','reason':'Observed Products/name HasPdf=false' if not product.get('HasPdf') else 'Primary PDF not attempted by recovery wrapper'}
  receipt['status']='acquired'
 except Exception as ex:receipt['error']=str(ex)
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2))
 if receipt['status']=='acquired':print(normalize(out))
 else:print(receipt)
if __name__=='__main__':run(sys.argv[1])
