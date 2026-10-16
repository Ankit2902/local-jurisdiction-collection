"""Bounded official-site routing check; no code acquisition or credentials."""
import json,time
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import requests
from bs4 import BeautifulSoup
from ecode360 import digest,dump,now
SOURCES={
'burlingame-ca':'https://burlingame.org/172/Codes-Regulations',
'emeryville-ca':'https://www.emeryville.org/Site-Footer/Footer-Widgets/Quick-Links/Municipal-Code',
'half-moon-bay-ca':'https://www.halfmoonbay.gov/384/Municipal-Code',
'malibu-ca':'https://malibucity.org/188/City-Council-Documents',
'san-leandro-ca':'https://www.sanleandro.org/342/Other-Planning-Resources',
'santa-clara-ca':'https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/',
'santa-monica-ca':'https://www.santamonica.gov/',
'santa-rosa-ca':'https://www.srcity.org/785/Code-Enforcement',
'south-san-francisco-ca':'https://www.ssf.gov/',
'sunnyvale-ca':'https://www.sunnyvale.ca.gov/your-government/departments/office-of-the-city-attorney',
'west-hollywood-ca':'https://www.weho.org/city-government/city-clerk',
'tukwila-wa':'https://www.tukwilawa.gov/departments/city-clerks-office/tukwila-municipal-code/'
}
def main():
 out=Path(__file__).parent/'evidence'/'official-routing';out.mkdir(parents=True,exist_ok=True);results=[]
 for slug,url in SOURCES.items():
  row={'slug':slug,'official_page_url':url,'checked_at':now(),'official_routing_verified':False,'publication_version_verified':False}
  try:
   r=requests.get(url,headers={'User-Agent':'CompliSolv municipal-code method validation/1.0'},timeout=25)
   folder=out/slug;folder.mkdir(parents=True,exist_ok=True);(folder/'official.html').write_bytes(r.content)
   row.update({'status':r.status_code,'final_url':r.url,'redirect_chain':[{'url':x.url,'status':x.status_code,'location':x.headers.get('Location')} for x in r.history],
     'raw_path':str((folder/'official.html').relative_to(Path(__file__).parent)),'raw_sha256':digest(r.content)})
   soup=BeautifulSoup(r.content,'html.parser');links=[]
   for a in soup.select('a[href]'):
    href=urljoin(r.url,a['href']);host=urlsplit(href).hostname or ''
    if any(x in host for x in ['ecode360.com','codepublishing.com','municode.com','municipal.codes','qcode.us']):
     links.append({'label':' '.join(a.get_text(' ',strip=True).split()),'url':href})
   row['publisher_links']=links
   row['official_routing_verified']=r.status_code==200 and bool(links)
   dump(folder/'receipt.json',row)
  except requests.RequestException as exc:row['error']=str(exc)
  results.append(row);time.sleep(.4)
 dump(out/'results.json',results);print(json.dumps(results,indent=2))
if __name__=='__main__':main()
