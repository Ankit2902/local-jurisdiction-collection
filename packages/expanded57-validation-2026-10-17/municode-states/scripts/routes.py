#!/usr/bin/env python3
import urllib.request, urllib.error, json, pathlib, hashlib, datetime, time, re
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCES={
'des-moines-ia':'https://www.dsm.city/',
'little-rock-ar':'https://littlerock.gov/',
'wilmington-de':'https://www.wilmingtonde.gov/',
'bridgeport-ct':'https://www.bridgeportct.gov/government/departments/city-clerk/municipal-code-and-city-charter',
'jackson-ms-zoning':'https://jacksonms.gov/government/city-departments/planning-and-development/office-of-city-planning/zoning/zoning-ordinances-and-code/',
'jackson-ms':'https://jacksonms.gov/government/city-departments/planning-and-development/resources/ordinances-and-regulations/',
'billings-mt-zoning':'https://www.billingsmt.gov/755/Zoning-Information',
'billings-mt-2026':'https://www.billingsmt.gov/3344/2026-Ordinances',
'billings-mt':'https://billingsmt.gov/155/Resolutions-Ordinances-City-Code',
'huntsville-al':'https://www.huntsvilleal.gov/development/building-construction/planning/zoning/zoning-ordinance/',
'providence-ri':'https://www.providenceri.gov/inspection/codes-ordinances/',
'cheyenne-wy':'https://www.cheyennecity.org/Your-Government/Departments/City-Clerk/City-CodeUDC',
'providence-ri-zoning':'https://www.providenceri.gov/planning/zoning/',
'fargo-nd':'https://www.fargond.gov/city-government/departments/planning-development/land-use-zoning/land-development-code',
'charleston-sc':'https://www.charleston-sc.gov/295/Zoning',
'charleston-wv':'https://www.charlestonwv.gov/government/city-departments/planning',
'bridgeport-ct-zoning':'https://www.bridgeportct.gov/government/departments/zoning-department',
'cheyenne-wy-udc':'https://www.cheyennecity.org/Your-Government/Departments/Planning-and-Development-Department/Unified-Development-Code'}
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.cur=None
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='a' and d.get('href'):self.cur={'url':d['href'],'text':''}
 def handle_data(self,d):
  if self.cur:self.cur['text']+=d
 def handle_endtag(self,t):
  if t=='a' and self.cur:self.links.append(self.cur);self.cur=None
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');args=p.parse_args();out={}
 for slug,url in SOURCES.items():
  dest=ROOT/'routes'/slug;dest.mkdir(parents=True,exist_ok=True);raw=dest/'official.html';receipt=dest/'receipt.json'
  if not args.offline and not raw.exists():
   at=datetime.datetime.now(datetime.timezone.utc).isoformat()
   try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; CompliSolv bounded validation)'}),timeout=45) as r:data=r.read();meta={'url':url,'final_url':r.url,'status':r.status,'headers':dict(r.headers)}
   except urllib.error.HTTPError as e:data=e.read();meta={'url':url,'status':e.code,'headers':dict(e.headers)}
   except Exception as e:data=b'';meta={'url':url,'status':None,'error':str(e)}
   raw.write_bytes(data);meta.update(acquired_at=at,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data));receipt.write_text(json.dumps(meta,indent=2));time.sleep(3)
  if not raw.exists():continue
  data=raw.read_bytes();meta=json.loads(receipt.read_text());encoding=meta.get('headers',{}).get('Content-Encoding','')
  if encoding=='br':
   import brotli
   data=brotli.decompress(data)
  elif encoding=='gzip':
   import gzip
   data=gzip.decompress(data)
  l=Links();l.feed(data.decode('utf-8',errors='replace'));relevant=[x for x in l.links if re.search(r'municode|ecode360|zoning|charter|ordinance|\.pdf|development.code',x['url']+' '+x['text'],re.I)]
  (dest/'links.json').write_text(json.dumps(relevant,indent=2));out[slug]={'receipt':json.loads(receipt.read_text()),'links':relevant}
 print(json.dumps(out,indent=2))
