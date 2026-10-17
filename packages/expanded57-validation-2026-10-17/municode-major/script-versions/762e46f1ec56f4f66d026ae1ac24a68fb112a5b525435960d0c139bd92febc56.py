"""Retain official routing HTML and exact outbound code/download links; no law completeness claim."""
import argparse, hashlib, json, sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
from municode_shared import fetch
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
'fresno':'https://www.fresno.gov/cityattorney/',
'atlanta':'https://www.atlantaga.gov/government/departments/city-planning/ordinances-regulations',
'kansas-city':'https://www.kcmo.gov/city-hall/departments/city-planning-development/building-and-development-code',
'mesa':'https://www.mesaaz.gov/Business-Development/Development-Services/Development-Codes-Ordinances-Regulations',
'raleigh':'https://raleighnc.gov/government/services/city-code',
'raleigh-udo':'https://raleighnc.gov/planning/services/unified-development-ordinance-udo',
'miami':'https://www.miami.gov/My-Government/View-City-of-Miami-Code-of-Ordinances-Municode',
'virginia-beach':'https://virginiabeach.gov/city-hall/codes-ordinances',
'long-beach':'https://www.longbeach.gov/lbcd/planning/current/zoning/',
'tulsa':'https://www.cityoftulsa.org/government/city-charter-ordinances-and-executive-orders/',
'tulsa-zoning':'https://tulsaplanning.org/resources/plans/',
'aurora':'https://www.auroragov.org/business_services/development_center/codes_rules/building___zoning_code/unified_development_ordinance',
'wichita':'https://www.wichita.gov/1710/Legal-Information',
'new-orleans-czo':'https://czo.nola.gov/home/'
}
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.current=None
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='a' and d.get('href'):self.current={'href':d['href'],'text':''}
  if t=='iframe' and d.get('src'):self.links.append({'href':d['src'],'text':'iframe'})
 def handle_data(self,d):
  if self.current:self.current['text']+=d
 def handle_endtag(self,t):
  if t=='a' and self.current:self.links.append(self.current);self.current=None

def run(offline=False):
 out=ROOT/'evidence/routes';out.mkdir(parents=True,exist_ok=True);results=[]
 for name,url in SOURCES.items():
  p=out/(name+'.html');err=None
  if not offline:
   try:fetch(url,p,timeout=30)
   except Exception as ex:err=str(ex)
  receipt=json.loads(p.with_name(p.name+'.receipt.json').read_text()) if p.with_name(p.name+'.receipt.json').exists() else {}
  if not p.exists():results.append({'name':name,'url':url,'error':err});continue
  body=p.read_bytes();parser=Links();parser.feed(body.decode('utf8','replace'))
  links=[{'url':urljoin(url,x['href']),'text':' '.join(x['text'].split())} for x in parser.links if any(s in (x['href']+' '+x['text']).lower() for s in ['municode','codehub','udo.','zoning','charter','code','ordinance','pdf','download'])]
  r={'name':name,'url':url,'http_status':receipt.get('http_status'),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'links':links,'error':err};results.append(r);print(name,r['http_status'],len(links),flush=True)
 (ROOT/'route-inventory.json').write_text(json.dumps(results,indent=2))
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');a=p.parse_args();run(a.offline)
