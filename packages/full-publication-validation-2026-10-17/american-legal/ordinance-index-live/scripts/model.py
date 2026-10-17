"""Pure American Legal inventory/content models. No network or output mutation."""
import csv,hashlib,io,json,re
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
from pypdf import PdfReader

def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def label(v):return re.sub(r'[^a-z0-9]','',v.casefold())
def redux(data):
 m=re.search(r'window\._redux_state\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")',data.decode('utf-8'))
 if not m:raise ValueError('Publisher redux metadata absent')
 return json.loads(json.loads(m.group(1)))
def select(data,url,jurisdiction,state,selector=None,aliases=()):
 s=redux(data)['codes'];client=s['currClient'];v=s['selectedVersion'];parts=urlparse(url).path.split('/');slug=parts[2]
 assert client['slug']==slug and v['client_slug']==slug,'Client route mismatch'
 assert label(client['name']) in {label(x) for x in [jurisdiction,*aliases]},'Exact jurisdiction identity mismatch: '+client['name']
 assert client['region']['slug'].casefold()==state.casefold(),'State identity mismatch'
 route_code=parts[4] if len(parts)>4 and parts[4]!='overview' else None
 selector=selector or route_code
 choices=[c for c in v['toc'] if not selector or selector in [c['slug'],c['uuid'],c['title']]]
 assert len(choices)==1,'Choose an observed publication slug/title explicitly: '+str([(c['slug'],c['title']) for c in v['toc']])
 c=choices[0];identity={'client_slug':slug,'jurisdiction':client['name'],'state':state.upper(),'version_uuid':v['uuid'],'version_name':v['name'],'currency_info':v.get('currency_info'),'code_uuid':c['uuid'],'code_slug':c['slug'],'code_title':c['title'],'is_pdf':c['is_pdf']}
 return identity,c,v['toc']
def node(n,parent=None,path=()):
 assert n.get('doc_id') and n.get('id') is not None,'Unknown inventory node shape'
 return {'document_id':n['doc_id'],'internal_id':n['id'],'heading':n['title'],'parent_id':parent,'path':[*path,n['title']],'has_children':bool(n.get('has_children')),'orig_doc_id':n.get('orig_doc_id') or n['doc_id'],'orig_doc_idx':n.get('orig_doc_idx') or 0,'passthru_doc_id':n.get('passthru_doc_id'),'type':n.get('type','section')}
def inventory_from_sources(identity,code,fetch):
 result=[];seen=set();expanded=[]
 def visit(n,parent=None,path=()):
  item=node(n,parent,path);key=item['document_id'];assert key not in seen,'Duplicate inventory ID '+key;seen.add(key);result.append(item)
  if item['has_children']:
   url='https://codelibrary.amlegal.com/api/section-toc/'+str(item['internal_id'])+'/'
   raw=fetch(url);body=json.loads(raw);assert body['doc_id']==key and body['id']==item['internal_id'] and body['code_uuid']==identity['code_uuid'],'Wrong TOC source identity';assert 'children' in body and isinstance(body['children'],list),'TOC children missing';expanded.append(key)
   for child in body['children']:
    assert child.get('parent_doc_id') in (None,key),'TOC parent mismatch';visit(child,key,item['path'])
 for n in code['sections']:visit(n)
 return {'nodes':result,'expanded':expanded,'root_ids':[n['doc_id'] for n in code['sections']],'complete':True}
def refs(html,base):
 soup=BeautifulSoup(html,'html.parser');assets=[];links=[]
 for e in soup.find_all(True):
  for attr in ['src','data','poster','href','to','srcset']:
   if not e.get(attr):continue
   raw=e[attr];resolved=raw;match=re.search(r"pathname\s*:\s*['\"]([^'\"]+)",raw)
   if match:resolved=match.group(1)
   kind=None
   if e.name=='link' and attr=='href':kind='stylesheet' if 'stylesheet' in e.get('rel',[]) else None
   elif e.name in ['img','source','video','audio','embed','object','iframe'] and attr in ['src','data','poster','srcset']:kind='media'
   elif e.name in ['a','link'] and attr in ['href','to'] and re.search(r'\.(?:pdf|docx?|xlsx?|zip|csv|tiff?|png|jpe?g)(?:$|[?#])',resolved,re.I):kind='attachment'
   entry={'tag':e.name,'attribute':attr,'raw':raw,'url':urljoin(base,resolved),'label':e.get_text(' ',strip=True)}
   if raw.startswith('data:'):entry['disposition']='inline-retained';entry['sha256']=digest(raw.encode())
   elif raw.startswith(('javascript:','mailto:','tel:','#')):entry['disposition']='non-download-reference'
   else:entry['disposition']='required-asset' if kind else 'navigation-reference'
   if kind:entry['kind']=kind;assets.append(entry)
   else:links.append(entry)
  if e.get('style') and 'url(' in e['style']:
   for u in re.findall(r'url\([\s\'"]*([^\)\'\"]+)',e['style']):assets.append({'tag':e.name,'attribute':'style','raw':u,'url':urljoin(base,u),'label':'','kind':'style-resource','disposition':'inline-retained' if u.startswith('data:') else 'required-asset'})
 return assets,links

def html_record(payload,item,identity,source_url,source_sha):
 assert payload['doc_id']==item['document_id'] and payload['id']==item['internal_id'],'Wrong requested rendered document'
 html=payload.get('html');assert isinstance(html,str) and html.strip(),'Missing rendered body'
 soup=BeautifulSoup(html.replace('className=','class='),'html.parser');root=soup.find(id='rid-'+item['document_id']);assert root,'Requested own heading container absent'
 for e in soup.select('script,style,AnnotationDrawer,annotationdrawer,CodeOptions,codeoptions,.clearfix'):e.decompose()
 ids=[e['id'][4:] for e in soup.select('[id^="rid-"]')];assert len(ids)==len(set(ids)),'Duplicate raw body block IDs'
 # A renderer packet owns its original doc/index range. Additional inventory headings are forbidden by verifier.
 tables=[]
 for table in soup.find_all('table'):
  if table.find_parent('table'):continue
  rows=[]
  for tr in table.find_all('tr'):
   if tr.find_parent('table') is not table:continue
   rows.append([{'tag':c.name,'text':c.get_text(' ',strip=True),'rowspan':int(c.get('rowspan',1)),'colspan':int(c.get('colspan',1))} for c in tr.find_all(['td','th'],recursive=False)])
  tables.append(rows)
 text=soup.get_text('\n',strip=True);assert text.strip(),'Empty packet'
 assets,links=refs(html,source_url)
 return {'document_id':item['document_id'],'heading':item['heading'],'path':item['path'],'parent_id':item['parent_id'],'kind':'html-renderer-owned-range','text':text,'html':html,'body_block_ids':ids,'tables':tables,'links':links,'assets':assets,'source_url':source_url,'source_sha256':source_sha,'publication_identity':identity,'notes':{'publisher_title':payload.get('title'),'code_lookup':payload.get('code_lookup')},'text_sha256':digest(text.encode())}

def pdf_pages(data,owner,source_url):
 assert data.startswith(b'%PDF-'),'Native source is not PDF';reader=PdfReader(io.BytesIO(data));result=[]
 for i,page in enumerate(reader.pages):
  text=page.extract_text() or '';result.append({'document_id':owner+':page:'+str(i+1),'owner_id':owner,'page':i+1,'text':text,'text_sha256':digest(text.encode()),'image_xobject_count':len(page.images),'source_url':source_url})
 assert len(result)==len(reader.pages)
 return result

def output_bytes(records,pages):
 data={'sections.jsonl':b''.join(json.dumps(r,ensure_ascii=False).encode()+b'\n' for r in records),'pdf-pages.jsonl':b''.join(json.dumps(r,ensure_ascii=False).encode()+b'\n' for r in pages)}
 out=io.StringIO(newline='');fields=['document_id','kind','heading','parent_id','text','source_url','source_sha256'];w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(records);data['sections.csv']=out.getvalue().encode();return data
