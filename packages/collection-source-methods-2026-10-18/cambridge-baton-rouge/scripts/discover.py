"""Three bounded official HTML GETs through copied reviewed shared host gate.
No image loading; external redirects refused before follow-up request.
"""
import sys
sys.dont_write_bytecode=True
import json,hashlib,urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime'))
import transport
SOURCES=[
 ('90-5918edb057f6','https://www.cambridgema.gov/cdd/zoninganddevelopment/zoning/ordinance'),
 ('95-152a3da8bd28','https://www.brla.gov/706/Unified-Development-Code'),
 ('95-4408caae6a9e','https://www.brla.gov/1129/Code-of-Ordinances')]
base=transport.Redirect
class OriginOnly(base):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if urllib.parse.urlsplit(newurl).hostname!=urllib.parse.urlsplit(req.full_url).hostname:
   raise RuntimeError('Unqualified cross-host redirect refused before request: '+newurl)
  return super().redirect_request(req,fp,code,msg,headers,newurl)
transport.Redirect=OriginOnly
def main():
 results=[]
 for ident,url in SOURCES:
  body=ROOT/'source'/f'{ident}.html';receipt=body.with_suffix('.receipt.json')
  if body.exists()or receipt.exists():raise RuntimeError('No automatic reuse/retry of existing discovery output: '+ident)
  try:
   data,meta=transport.fetch(url,max_bytes=2_000_000)
   body.write_bytes(data);receipt.write_text(json.dumps(meta,indent=2)+'\n')
   record={'publication_id':ident,'url':url,'receipt':receipt.name,'status':meta['status'],'bytes':len(data),'sha256':meta['sha256']}
   if meta.get('access_stop'):record['stopped']=True;results.append(record);continue
   if meta['status']!=200 or meta.get('policy_omitted_image'):record['incomplete']=True;results.append(record);continue
   soup=BeautifulSoup(data,'html.parser')
   for el in soup.select('script,style,nav,header,footer'):el.decompose()
   main=soup.select_one('main')or soup
   anchors=[]
   for a in main.select('a[href]'):
    anchors.append({'href':a['href'],'url':urllib.parse.urljoin(url,a['href']),'label':a.get_text(' ',strip=True),'title':a.get('title'),'type':a.get('type')})
   text=main.get_text('\n',strip=True)
   analysis={'publication_id':ident,'source_url':url,'source_sha256':meta['sha256'],'source_receipt':receipt.name,'headings':[a.get_text(' ',strip=True)for a in main.select('h1,h2,h3,h4')],'text':text,'anchors':anchors}
   (ROOT/'source'/f'{ident}.analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n')
   record['anchors']=len(anchors);results.append(record)
  except Exception as exc:
   # A persisted host stop prevents any new reservation/request.
   results.append({'publication_id':ident,'url':url,'refused':True,'error':str(exc)})
 (ROOT/'discovery-results.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(results,indent=2))
if __name__=='__main__':main()
