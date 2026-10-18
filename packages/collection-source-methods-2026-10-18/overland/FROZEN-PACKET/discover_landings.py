import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,urllib.parse,time
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H/'captured'))
from bs4 import BeautifulSoup
from collectors.encodeplus.transport import fetch,scope_path
rows=[r for r in json.loads((H/'catalog-input.json').read_text())if r['publisher']=='official'];src=(H/'publisher-documents-retained.html').read_bytes();m=json.loads((H/'publisher-documents-retained.html.receipt.json').read_text());assert hashlib.sha256(src).hexdigest()==m['sha256'];soup=BeautifulSoup(src,'html.parser');d=H/'landing-discovery';d.mkdir(exist_ok=True);results=[]
for r in rows:
 a=next(a for a in soup.select('a[href]')if urllib.parse.urljoin(m['url'],a['href'])==r['source_url']);section=a.find_parent(['section','footer','nav']) or a.parent.parent;item={'id':r['id'],'catalog_title':r['title'],'url':r['source_url'],'source_anchor':str(a),'source_context':str(section),'anchor_source_sha256':m['sha256'],'anchor_source_url':m['url']};p=d/(r['id']+'.html')
 try:
  body,receipt=fetch(r['source_url'],p);item.update(status=receipt['http_status'],final_url=receipt['final_url'],redirects=receipt['redirects'],sha256=receipt['sha256'],bytes=len(body));html=BeautifulSoup(body,'html.parser');main=html.find('main')or html.find(id='main-content')or html.find(id='content')or html.body or html
  item['title']=html.title.get_text(' ',strip=True)if html.title else None;item['headings']=[h.get_text(' ',strip=True)for h in main.select('h1,h2,h3')];item['main_text']=main.get_text(' ',strip=True);item['main_links']=[{'href':a['href'],'resolved':urllib.parse.urljoin(receipt['final_url'],a['href']),'label':a.get_text(' ',strip=True)}for a in main.select('a[href]')]
 except Exception as e:
  item['error']=str(e)
  if p.with_name(p.name+'.receipt.json').exists():item['receipt']=json.loads(p.with_name(p.name+'.receipt.json').read_text())
 results.append(item);(d/'inventory.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({k:v for k,v in item.items()if k in['id','status','error','title','final_url','bytes']}),flush=True)
