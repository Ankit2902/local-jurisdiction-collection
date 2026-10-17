"""Publication inventory and exclusive source-node ownership; no network."""
import copy,csv,gzip,io,json,re
from urllib.parse import urljoin,urlparse,parse_qs
from bs4 import BeautifulSoup
from .util import digest,hash_json

def decode(data,headers):
 coding=next((v for k,v in headers.items() if k.lower()=='content-encoding'),'').lower()
 if coding=='gzip':data=gzip.decompress(data)
 elif coding=='br':
  import brotli
  data=brotli.decompress(data)
 return data.decode('utf-8-sig')
def clean(s):return ' '.join(str(s).split())
def heading(section):
 for h in section.find_all(re.compile('^h[1-6]$')):
  if h.find_parent('section',attrs={'data-secid':True})==section:
   clone=copy.deepcopy(h)
   for sup in clone.find_all('sup'):sup.decompose()
   return clean(clone.get_text(' ',strip=True))
 return ''
def inventory(html,cfg):
 soup=BeautifulSoup(html,'html.parser');head=soup.select_one('#toc-pagehead');assert head and clean(head.get_text(' ',strip=True))==cfg['identity'],'Wrong publication identity'
 nodes=[];seen=set()
 for li in soup.select('#toc-list li.tocLink'):
  m=re.fullmatch('secid-x([0-9]+)',li.get('id',''));assert m,'Unknown TOC ID shape';ident=m.group(1);assert ident not in seen,'Duplicate TOC ID';seen.add(ident);a=li.select_one('a[href]');label=li.select_one('.toc-item');assert a and label
  url=urljoin(cfg['base'],a['href']);assert parse_qs(urlparse(url).query).get('secid')==[ident],'TOC link/ID mismatch'
  nodes.append({'id':ident,'heading':clean(label.get_text(' ',strip=True)),'viewer_url':url,'has_children':bool(re.search(r',\s*true\s*\)',a.get('onclick',''))),'declared_depth':next((x[len('toc-level'):] for x in li.find_parent('ul').get('class',[]) if x.startswith('toc-level')),None)})
 assert nodes,'Empty inventory'
 # Flat source inventory is canonical. TOC declared depths never determine body parentage.
 return {'identity':cfg['identity'],'base':cfg['base'],'nodes':nodes,'sha256':hash_json(nodes),'hierarchy_source':'canonical body DOM ancestry and response breadcrumbs; TOC depth is advisory only'}
def refs(body,base):
 found=[]
 for el in body.find_all(True):
  attr='src' if el.name in ['img','iframe','embed','source','audio','video'] else 'data' if el.name=='object' else None
  if attr and el.get(attr):found.append((el,attr,el[attr],True))
  if el.get('srcset'):
   for value in el['srcset'].split(','):found.append((el,'srcset',value.strip().split()[0],True))
  if el.name=='a' and el.get('href'):
   h=el['href'];path=urlparse(h).path.lower()
   if re.search(r'\.(pdf|docx?|xlsx?|csv|zip|png|jpe?g|gif|svg|webp|tiff?)$',path) or any(x in path for x in ['doclibrary.aspx','download.aspx']):found.append((el,'href',h,True))
  for value in re.findall(r'url\([\'\"]?([^\)\'\"]+)',el.get('style','')):found.append((el,'style',value,True))
 result=[]
 for el,attr,value,required in found:
  url=urljoin(base,value)
  result.append({'url':url,'attribute':attr,'tag':el.name,'alt':el.get('alt'),'required':required,'supported_scheme':urlparse(url).scheme in ['https','http','data']})
 return result
def parse_document(html,requested,cfg,known):
 soup=BeautifulSoup(html,'html.parser');page=soup.select_one('#thePage');assert page and page.get('secid')==requested,'Requested container identity mismatch'
 sections=page.select('section[data-secid]');ids=[s['data-secid'] for s in sections];assert len(ids)==len(set(ids)),'Duplicate body source IDs';assert requested in ids,'Requested node absent'
 crumbs=[]
 for a in soup.select('#pageControls .breadCrumbs .breadCrumbs a'):
  q=parse_qs(urlparse(a.get('href','')).query);crumbs.append({'id':q.get('secid',[None])[0],'heading':clean(a.get_text(' ',strip=True)),'href':urljoin(cfg['base'],a.get('href',''))})
 # Final breadcrumb is selected container itself; the DOM below provides its canonical children.
 prefix=crumbs[:-1];records=[]
 for source in sections:
  ident=source['data-secid'];h=heading(source);assert h,'Section has no exclusively owned heading: '+ident
  parents=list(reversed(source.find_parents('section',attrs={'data-secid':True})));ancestry=[{'id':p['data-secid'],'heading':heading(p)} for p in parents];assert all(p['heading'] for p in ancestry)
  owned=copy.deepcopy(source)
  for descendant in list(owned.find_all('section',attrs={'data-secid':True})):
   if descendant.find_parent('section',attrs={'data-secid':True})==owned:descendant.decompose()
  omitted=[]
  for el in owned.select('.archiveNotice.nullValue'):omitted.append(clean(el.get_text(' ',strip=True)));el.decompose()
  body=copy.deepcopy(owned)
  own_h=next((x for x in body.find_all(re.compile('^h[1-6]$')) if x.find_parent('section',attrs={'data-secid':True})==body),None)
  if own_h:own_h.decompose()
  text='\n'.join(clean(s) for s in body.get_text('\n',strip=True).splitlines() if clean(s));tables=[]
  for table in body.find_all('table'):
   rows=[]
   for tr in table.find_all('tr'):
    if tr.find_parent('table')!=table:continue
    rows.append([{'text':clean(c.get_text(' ',strip=True)),'tag':c.name,'rowspan':c.get('rowspan','1'),'colspan':c.get('colspan','1'),'html':str(c)} for c in tr.find_all(['td','th']) if c.find_parent('tr')==tr])
   tables.append(rows)
  assets=refs(body,cfg['base']);notes=[clean(x.get_text(' ',strip=True)) for x in body.select('.archiveNotice,.footnote,.note')]
  records.append({'id':ident,'heading':h,'toc_heading':known.get(ident,{}).get('heading'),'toc_heading_matches':h==known[ident]['heading'] if ident in known else None,'path':prefix+ancestry,'parent_id':ancestry[-1]['id'] if ancestry else (prefix[-1]['id'] if prefix else None),'ownership':'exclusive section body; descendant sections removed','kind':'operative_or_descriptive_body' if text or assets else 'structural_container','text':text,'html':str(owned),'body_html':str(body),'body_sha256':digest(str(owned).encode()),'tables':tables,'assets':assets,'image_only':bool(assets) and not bool(text),'links':[{'text':clean(a.get_text(' ',strip=True)),'attributes':dict(a.attrs),'url':urljoin(cfg['base'],a.get('href',''))} for a in body.find_all('a')],'notes':notes,'omitted_null_metadata':omitted,'list_count':len(body.find_all(['ol','ul'])),'inventory_origin':'toc' if ident in known else 'embedded_source_section','source_url':cfg['base']+'doc-view.aspx?secid='+ident+'&ajax=0'})
 return records

def outputs(records):
 records=sorted(records,key=lambda r:int(r['id']));jsonl=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records).encode();buf=io.StringIO(newline='');fields=['id','heading','parent_id','kind','text','source_url','body_sha256'];w=csv.DictWriter(buf,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in records)
 return {'records.jsonl':jsonl,'records.csv':buf.getvalue().encode()}
