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
  if attr and el.get(attr) and not el[attr].startswith('#'):found.append((el,attr,el[attr],True))
  if el.name in ['image','use']:
   for attr_name in ['href','xlink:href']:
    if el.get(attr_name) and not el[attr_name].startswith('#'):found.append((el,attr_name,el[attr_name],True))
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
 def section_key(el):
  keys=[c for c in el.get('class',[]) if re.fullmatch(r'_\d+(?:-\d+)*',c)]
  return max(keys,key=len) if keys else None
 keys={section_key(el):el for el in sections if section_key(el)}
 assert len(keys)==sum(bool(section_key(el)) for el in sections),'Ambiguous canonical body class hierarchy'
 outside=copy.deepcopy(page)
 for el in list(outside.select('section[data-secid]')):
  if not el.find_parent('section',attrs={'data-secid':True}):el.decompose()
 omitted_controls=[]
 for el in outside.select('#sectionBanner,script,style'):
  omitted_controls.append({'tag':el.name,'id':el.get('id'),'reason':'Publisher document branding/nonlegal executable style control'});el.decompose()
 assert not clean(outside.get_text(' ',strip=True)),'Unowned non-control text outside section[data-secid]'
 assert not refs(outside,cfg['base']),'Unowned asset outside section[data-secid]'
 for source in sections:
  ident=source['data-secid'];h=heading(source);heading_source='body_heading' if h else 'toc_label' if ident in known else 'definition_label' if source.select_one('.def') else 'absent_in_publisher_source';h=h or known.get(ident,{}).get('heading') or (clean(source.select_one('.def').get_text(' ',strip=True)) if source.select_one('.def') else '')
  parents=list(reversed(source.find_parents('section',attrs={'data-secid':True})))
  key=section_key(source)
  if not parents and key:
   parts=key.split('-');parent_keys=['-'.join(parts[:i]) for i in range(1,len(parts))];parents=[keys[k] for k in parent_keys if k in keys]
  ancestry=[{'id':p['data-secid'],'heading':heading(p) or known.get(p['data-secid'],{}).get('heading') or (clean(p.select_one('.def').get_text(' ',strip=True)) if p.select_one('.def') else None)} for p in parents]
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
  for mini in body.select('.mini-TOC'):mini.decompose()
  # Mini-TOCs are navigation, never a substantive container body.
  text='\n'.join(clean(t) for t in body.get_text('\n',strip=True).splitlines() if clean(t))
  assets=refs(body,cfg['base']);notes=[clean(x.get_text(' ',strip=True)) for x in body.select('.archiveNotice,.footnote,.note')]
  if text or assets:kind='operative_or_descriptive_body';disposition='Exclusive legal/descriptive body retained'
  elif known.get(ident,{}).get('has_children') or (key and any(k.startswith(key+'-') for k in keys)):kind='structural_container';disposition='Explicit container has_children/source body ancestry, no owned substantive text'
  elif re.search(r'\b(repealed|reserved|omitted)\b',h,re.I):kind='source_excluded_repealed_or_reserved';disposition='Explicit source heading disposition retained verbatim'
  else:raise ValueError('Unexplained empty operative leaf '+ident)

  records.append({'id':ident,'heading':h,'heading_source':heading_source,'toc_heading':known.get(ident,{}).get('heading'),'toc_heading_matches':h==known[ident]['heading'] if ident in known else None,'path':prefix+ancestry,'parent_id':ancestry[-1]['id'] if ancestry else (prefix[-1]['id'] if prefix else None),'ownership':'exclusive section body; descendant sections removed','kind':kind,'disposition':disposition,'canonical_body_key':key,'hierarchy_method':'Observed body class ancestry plus DOM and response breadcrumbs; not TOC declared depth','page_ownership_ledger':{'unowned_legal_text':0,'unowned_assets':0,'excluded_controls':omitted_controls},'text':text,'html':str(owned),'body_html':str(body),'body_sha256':digest(str(owned).encode()),'tables':tables,'assets':assets,'image_only':bool(assets) and not bool(text),'links':[{'text':clean(a.get_text(' ',strip=True)),'attributes':dict(a.attrs),'url':urljoin(cfg['base'],a.get('href',''))} for a in body.find_all('a')],'notes':notes,'omitted_null_metadata':omitted,'mini_toc_disposition':'Removed from legal text; retained in owned source HTML as navigation','list_count':len(body.find_all(['ol','ul'])),'inventory_origin':'toc' if ident in known else 'embedded_source_section','source_url':cfg['base']+'doc-view.aspx?secid='+ident+'&ajax=0'})
 return records

def outputs(records):
 records=sorted(records,key=lambda r:int(r['id']));jsonl=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records).encode();buf=io.StringIO(newline='');fields=['id','heading','parent_id','kind','text','source_url','body_sha256'];w=csv.DictWriter(buf,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in records)
 return {'records.jsonl':jsonl,'records.csv':buf.getvalue().encode()}
