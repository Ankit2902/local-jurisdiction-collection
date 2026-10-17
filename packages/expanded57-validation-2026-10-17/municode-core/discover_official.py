import json,re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
from municode_shared import fetch
ROOT=Path(__file__).resolve().parent
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   a=dict(attrs)
   if 'href' in a:self.links.append(a['href'])
def main():
 result=[]
 for row in json.loads((ROOT/'assignment.json').read_text()):
  url=row['source_lead_url']
  if 'municode.com' in url:continue
  name=re.sub('[^a-z0-9]+','-',row['selection_name'].lower());out=ROOT/'raw'/name/'official.html'
  try:
   raw,r=fetch(url,out);p=Links();p.feed(raw.decode('utf8','replace'));links=[urljoin(url,u) for u in p.links if re.search('code|charter|ordinance|zoning|udo|\.pdf',u,re.I)];result.append({'jurisdiction':row['jurisdiction'],'url':url,'links':links});print(row['jurisdiction'],json.dumps(links),flush=True)
  except Exception as e:result.append({'jurisdiction':row['jurisdiction'],'url':url,'error':str(e)});print(row['jurisdiction'],str(e),flush=True)
 (ROOT/'official-discovery.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
