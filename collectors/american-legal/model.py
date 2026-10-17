"""Pure American Legal inventory/content models. No network or output mutation."""
import csv,hashlib,io,json,re
from urllib.parse import urljoin,urlparse,unquote
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
def srcset_urls(value):
 result=[];pos=0
 while pos<len(value):
  while pos<len(value) and (value[pos].isspace() or value[pos]==','):pos+=1
  start=pos
  while pos<len(value) and not value[pos].isspace():pos+=1
  token=value[start:pos]
  if not token:break
  if token.lower().startswith('data:'):result.append(token.rstrip(','))
  else:result.extend(u for u in token.strip(',').split(',') if u)
  while pos<len(value) and value[pos]!=',':pos+=1
 return result

def refs(html,base):
 soup=BeautifulSoup(html.replace('className=','class='),'html.parser');assets=[];links=[]
 for e in soup.find_all(True):
  for attr in ['src','data','poster','href','to','srcset','xlink:href','background']:
   if not e.get(attr):continue
   raw_value=e[attr]
   for raw in (srcset_urls(raw_value) if attr=='srcset' else [raw_value]):
    resolved=raw;match=re.search(r"pathname\s*:\s*['\"]([^'\"]+)",raw)
    if match:resolved=match.group(1)
    kind=None
    if e.name=='link' and attr=='href':kind='stylesheet' if 'stylesheet' in e.get('rel',[]) else None
    elif e.name in ['img','source','video','audio','embed','object','iframe','image','use'] and attr in ['src','data','poster','srcset','href','xlink:href']:kind='image' if e.name in ['img','picture','image','use'] or attr in ['poster','srcset'] or (e.name=='source' and e.find_parent('picture')) else 'media'
    elif e.name in ['a','link'] and attr in ['href','to'] and re.search(r'\.(?:pdf|docx?|xlsx?|zip|csv|tiff?|png|jpe?g)(?:$|[?#])',resolved,re.I):kind='attachment'
    if e.name in ['a','link'] and attr in ['href','to'] and kind is None:
     context=e.find_parent(['p','li','td','div']);context=context.get_text(' ',strip=True) if context else ''
     if re.search(r'(?:incorporat\w*|adopt\w*).{0,100}(?:reference|map|plan|manual|standard|document)',context,re.I):kind='attachment'
    if raw.lower().startswith('data:image/') or e.get('type','').strip().lower().startswith('image/') or attr=='background' or (e.name=='input' and e.get('type','').strip().lower()=='image'):kind='image'
    entry={'tag':e.name,'attribute':attr,'raw':raw,'source_attribute':raw_value,'url':urljoin(base,resolved),'label':e.get_text(' ',strip=True)}
    if raw.lower().startswith('data:'):entry['disposition']='inline-retained';entry['sha256']=digest(raw.encode())
    elif raw.lower().startswith(('javascript:','mailto:','tel:','#')):entry['disposition']='non-download-reference'
    else:entry['disposition']='required-asset' if kind else 'navigation-reference'
    if kind or image_url(entry['url']):
     if kind=='image' or image_url(entry['url']):entry=image_reference(entry);kind='image'
     entry['kind']=kind
     if entry['disposition']=='required-asset':entry['url']=entry['url'].split('#',1)[0]
     assets.append(entry)
    else:links.append(entry)
  if e.get('style') and re.search(r'url\(',e['style'],re.I):
   for u in re.findall(r'url\([\s\'\"]*([^\)\'\"]+)',e['style'],re.I):assets.append({'tag':e.name,'attribute':'style','raw':u,'url':urljoin(base,u),'label':'','kind':'style-resource','disposition':'inline-retained' if u.lower().startswith('data:') else 'required-asset'})
 for svg in soup.find_all('svg'):
  if not svg.find_parent('svg'):assets.append(image_reference({'url':'inline-svg:'+digest(str(svg).encode()),'raw':'[IMAGE]','source_attribute':'[IMAGE]','tag':'svg','attribute':'inline','source_markup_sha256':digest(str(svg).encode()),'label':''}))
 for style in soup.find_all('style'):
  for u in css_links(style.get_text().encode()):
   kind='style-resource' if re.search(r'\.(?:css|woff2?|ttf|otf|eot)(?:$|[?#])',u,re.I) else 'image'
   ref={'url':urljoin(base,u),'raw':u,'source_attribute':u,'tag':'style','attribute':'stylesheet','kind':kind,'disposition':'required-asset','label':''};assets.append(image_reference(ref) if kind=='image' else ref)
 assets=[image_reference(a) if a.get('kind')=='image' or image_url(a['url']) or (a.get('attribute')=='style' and not re.search(r'\.(?:css|woff2?|ttf|otf|eot)(?:$|[?#])',a['url'],re.I)) else a for a in assets]
 return assets,links

def html_record(payload,item,identity,source_url,source_sha,resolved_images=()):
 assert payload['doc_id']==item['document_id'] and payload['id']==item['internal_id'],'Wrong requested rendered document'
 html=payload.get('html');assert isinstance(html,str) and html.strip(),'Missing rendered body'
 soup=BeautifulSoup(html.replace('className=','class='),'html.parser');root=soup.find(id='rid-'+item['document_id']);assert root,'Requested own heading container absent'
 assets,links=refs(html,source_url);assets,links=internal_references(assets,links,identity);assets=[image_reference(a) if a['url'] in set(resolved_images) else a for a in assets];placeholders=normalize_images(soup,source_url,resolved_images)
 for e in soup.select('script,style,AnnotationDrawer,annotationdrawer,CodeOptions,codeoptions,.clearfix'):e.decompose()
 ids=[e['id'][4:] for e in soup.select('[id^="rid-"]')];assert len(ids)==len(set(ids)),'Duplicate raw body block IDs'
 # A renderer packet owns its original doc/index range. Additional inventory headings are forbidden by verifier.
 tables=[];table_nodes=soup.find_all('table');table_parents=[]
 for table in table_nodes:
  parent=table.find_parent('table');table_parents.append(next((i for i,t in enumerate(table_nodes) if t is parent),None))
  rows=[]
  for tr in table.find_all('tr'):
   if tr.find_parent('table') is not table:continue
   rows.append([{'tag':c.name,'text':c.get_text(' ',strip=True),'rowspan':int(c.get('rowspan',1)),'colspan':int(c.get('colspan',1))} for c in tr.find_all(['td','th'],recursive=False)])
  tables.append(rows)
 text=soup.get_text('\n',strip=True);assert text.strip(),'Empty packet'
 own_heading=root.get_text(' ',strip=True);body_text=text.replace(root.get_text('\n',strip=True),'',1).strip()
 classification='operative-or-front-matter-body' if len(body_text)>10 else 'intentional-image-placeholder' if placeholders else 'structural-heading-only' if item['has_children'] else 'reserved-heading-only' if re.search(r'repealed|reserved|deleted|omitted|not used',item['heading'],re.I) else 'unqualified-heading-only'
 return {'document_id':item['document_id'],'heading':item['heading'],'path':item['path'],'parent_id':item['parent_id'],'kind':'html-renderer-owned-range','text':text,'html':str(soup),'image_placeholders':placeholders,'image_policy':IMAGE_POLICY,'body_block_ids':ids,'content_classification':classification,'tables':tables,'table_parent_indices':table_parents,'links':links,'assets':assets,'source_url':source_url,'source_sha256':source_sha,'publication_identity':identity,'notes':{'publisher_title':payload.get('title'),'code_lookup':payload.get('code_lookup')},'text_sha256':digest(text.encode())}

def internal_references(assets,links,identity):
 """Same-book legal citations are bound to retained IDs, never treated as document downloads."""
 kept=[];links=list(links)
 for entry in assets:
  u=urlparse(entry['url']);parts=u.path.strip('/').split('/')
  if entry.get('kind')!='image' and u.hostname=='codelibrary.amlegal.com' and len(parts)==5 and parts[0]=='codes' and parts[1]==identity.get('client_slug') and parts[2] in ['latest',identity.get('version_uuid')] and parts[3]==identity.get('code_slug'):
   links.append(dict(entry,disposition='internal-publication-reference',target_document_id=unquote(parts[4])))
  else:kept.append(entry)
 return kept,links

def bind_reference_graph(records,inventory):
 """Recompute citation closure against all independently inventoried/owned source IDs."""
 known={n['document_id'] for n in inventory['nodes']}|{v for r in records for v in r['body_block_ids']};unresolved=[]
 for record in records:
  for link in record['links']:
   if link.get('disposition')=='internal-publication-reference':
    link['target_retained']=link['target_document_id'] in known
    if not link['target_retained']:unresolved.append({'owner_id':record['document_id'],'target_id':link['target_document_id'],'url':link['url']})
 return unresolved

def passthrough_record(item,inventory,identity,source):
 """Publisher-defined navigation container: own TOC heading, zero descendant legal-body copies."""
 target=item.get('passthru_doc_id');byid={n['document_id']:n for n in inventory['nodes']};assert item['has_children'] and target in byid and target!=item['document_id'],'Unqualified passthrough container target'
 current=byid[target];visited=set();descendant=False
 while current.get('parent_id'):
  parent=current['parent_id'];assert parent not in visited,'Passthrough ancestry cycle';visited.add(parent)
  if parent==item['document_id']:descendant=True;break
  assert parent in byid,'Missing passthrough target ancestry';current=byid[parent]
 assert descendant,'Passthrough landing target is not an independently inventoried descendant'
 assert source['url']=='https://codelibrary.amlegal.com/api/section-toc/'+str(item['internal_id'])+'/' and len(source['sha256'])==64,'Missing original passthrough TOC source receipt'
 text=item['heading'];url=f"https://codelibrary.amlegal.com/codes/{identity['client_slug']}/{identity['version_uuid']}/{identity['code_slug']}/{target}"
 return {'document_id':item['document_id'],'heading':text,'path':item['path'],'parent_id':item['parent_id'],'kind':'publisher-toc-passthrough-container','text':text,'html':None,'image_placeholders':[],'image_policy':IMAGE_POLICY,'body_block_ids':[],'content_classification':'structural-heading-only','tables':[],'table_parent_indices':[],'links':[{'url':url,'disposition':'internal-publication-reference','target_document_id':target,'label':byid[target]['heading'],'relation':'publisher-passthrough-navigation'}],'assets':[],'source_url':source['url'],'source_sha256':source['sha256'],'publication_identity':identity,'passthru_target_id':target,'notes':{'normalization_basis':'Independent publisher TOC grouping; landing child owns its legal body, never duplicated here'},'text_sha256':digest(text.encode())}

def pdf_pages(data,owner,source_url):
 assert data.startswith(b'%PDF-'),'Native source is not PDF'
 from pdf_layout import layout_page
 import pymupdf
 reader=PdfReader(io.BytesIO(data));geometry=pymupdf.open(stream=data,filetype='pdf');assert len(geometry)==len(reader.pages);result=[]
 for i,page in enumerate(reader.pages):
  text=page.extract_text() or '';resources=page.get('/Resources') or {};resources=resources.get_object() if hasattr(resources,'get_object') else resources;objects=resources.get('/XObject',{})
  objects=objects.get_object() if hasattr(objects,'get_object') else objects
  layout=layout_page(geometry[i],text);images=sum(v.get_object().get('/Subtype')=='/Image' for v in objects.values());text=text+('\n'+('[IMAGE]\n'*(images+int(layout['vector_graphics_present']))).rstrip() if images or layout['vector_graphics_present'] else '');result.append({'document_id':owner+':page:'+str(i+1),'owner_id':owner,'page':i+1,'text':text,'text_sha256':digest(text.encode()),'image_xobject_count':images,'image_placeholder_count':images+int(layout['vector_graphics_present']),'layout':layout,'image_policy':IMAGE_POLICY,'source_url':source_url})
 assert len(result)==len(reader.pages);geometry.close()
 return result

def normalize_pdf_assets(assets,pages,read):
 """Every retained PDF gets normalized pages; identical bytes have one owner, with explicit aliases."""
 owners={assets[p['source_url']]['sha256']:p['owner_id'] for p in pages};metadata={}
 for url,asset in sorted(assets.items()):
  if asset['status']!='retained' or asset.get('validation',{}).get('kind')!='pdf':continue
  sha=asset['sha256'];owner=owners.get(sha);ids=[]
  if owner is None:
   owner='attachment:'+sha;additional=pdf_pages(read(asset),owner,url);pages.extend(additional);ids=[p['document_id'] for p in additional];owners[sha]=owner
  else:ids=[p['document_id'] for p in pages if p['owner_id']==owner and p['source_url']==url]
  metadata[url]={'normalized_pdf_owner_id':owner,'normalized_pdf_page_ids':ids,'normalized_pdf_document_pages':asset['validation']['pages'],'normalized_pdf_shared_bytes':not bool(ids)}
 return metadata

def output_bytes(records,pages):
 data={'sections.jsonl':b''.join(json.dumps(r,ensure_ascii=False).encode()+b'\n' for r in records),'pdf-pages.jsonl':b''.join(json.dumps(r,ensure_ascii=False).encode()+b'\n' for r in pages)}
 out=io.StringIO(newline='');fields=['document_id','kind','heading','parent_id','text','source_url','source_sha256'];w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(records);data['sections.csv']=out.getvalue().encode();return data

def native_records(data,inventory,identity,url,sha,resolved_images=(),inventory_sources=None):
 """Partition flat publisher-native rich blocks by independently inventoried TOC owners."""
 soup=BeautifulSoup(data,'html.parser');body=soup.body;assert body,'Native HTML body missing';wanted={n['document_id']:n for n in inventory['nodes']};allblocks=body.select('[id^="rid-"]');ids=[e['id'][4:] for e in allblocks];assert len(ids)==len(set(ids)),'Duplicate native source block IDs'
 raw_ids=set(ids);virtual={key:passthrough_record(n,inventory,identity,(inventory_sources or {}).get(key,{})) for key,n in wanted.items() if key not in raw_ids and n.get('passthru_doc_id')}
 assert set(wanted)-set(virtual)<=set(ids),'Native export omits independent TOC nodes: '+str(sorted(set(wanted)-set(virtual)-set(ids)))
 native_heads={e['id'][4:] for e in body.select('.toc-destination[id^="rid-"]')};assert not native_heads-set(wanted),'Uninventoried native section headings; full independent TOC required'
 unknown=[]
 for text in body.find_all(string=True):
  if text.strip() and not any(p.get('id','').startswith('rid-') for p in text.parents if getattr(p,'attrs',None)) and text.parent.name not in ['script','style']:unknown.append(str(text).strip())
 assert not unknown,'Unowned native text outside source blocks: '+str(unknown[:3])
 parts={key:[] for key in wanted};owner=None
 for block in allblocks:
  nested=next((p for p in block.parents if getattr(p,'attrs',None) and p.get('id','').startswith('rid-')),None)
  if nested:
   assert block['id'][4:] not in wanted,'Nested independent TOC heading needs explicit ownership support';continue
  key=block['id'][4:]
  if key in wanted:owner=key
  assert owner,'Source block before any independent TOC owner';parts[owner].append(str(block))
 result=[]
 for item in inventory['nodes']:
  did=item['document_id']
  if did in virtual:result.append(virtual[did]);continue
  fragment=''.join(parts[did]);record=html_record({'doc_id':did,'id':item['internal_id'],'title':item['heading'],'html':fragment},item,identity,url,sha,resolved_images);record['kind']='publisher-native-html-owned-range';record['notes']['normalization_basis']='Independent TOC owners + every retained native rich block, exactly once';result.append(record)
 owned=[v for r in result for v in r['body_block_ids']];assert len(owned)==len(set(owned)) and set(owned)==set(ids),'Native raw blocks not reconciled exactly once';return result

def css_links(data):
 text=data.decode('utf-8',errors='strict');return sorted(set(re.findall(r'url\([\s\'"]*([^\)\'\"]+)',text,re.I)+re.findall(r'@import\s+[\'"]([^\'"]+)',text,re.I)))
def validate_asset(url,data,content_type):
 import zipfile
 path=urlparse(url).path.lower();mime=(content_type or '').split(';')[0].lower();assert data,'Empty asset'
 # Fail closed before any decoder, including accidentally supplied separate image bytes.
 image_magic=data.startswith((b'\x89PNG\r\n\x1a\n',b'\xff\xd8\xff',b'GIF87a',b'GIF89a',b'BM',b'II*\x00',b'MM\x00*',b'\x00\x00\x01\x00')) or (data.startswith(b'RIFF') and data[8:12]==b'WEBP') or b'<svg' in data[:1024].lower()
 if image_url(url) or mime.startswith('image/') or image_magic:
  return {'kind':'image-policy-excluded','qualified':False,'reason':'Separate image bytes are forbidden; no decoding or validation performed','policy':IMAGE_POLICY,'placeholder':'[IMAGE]'}
 if path.endswith('.pdf') or mime=='application/pdf':
  assert data.startswith(b'%PDF-'),'PDF asset returned nonPDF';reader=PdfReader(io.BytesIO(data));assert len(reader.pages)>0;return {'kind':'pdf','qualified':True,'pages':len(reader.pages)}
 if path.endswith('.css') or mime=='text/css':assert b'<html' not in data.lower();css_links(data);return {'kind':'css','qualified':True}
 if path.endswith(('.zip','.docx','.xlsx','.pptx')) or mime in ['application/zip','application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
  z=zipfile.ZipFile(io.BytesIO(data));assert z.testzip() is None;return {'kind':'zip-container','qualified':True,'members':len(z.namelist())}
 if path.endswith(('.woff','.woff2','.ttf','.otf')):assert data[:4] in [b'wOFF',b'wOF2',b'\x00\x01\x00\x00',b'OTTO'];return {'kind':'font','qualified':True}
 return {'kind':'unqualified-binary','qualified':False,'reason':'Bytes retained; format/content validation not implemented'}

IMAGE_POLICY='literal-[IMAGE]-no-image-fetch-v1'
def image_url(url):return url.lstrip().lower().startswith('data:image/') or bool(re.search(r'\.(?:png|jpe?g|gif|webp|svg|avif|bmp|ico|tiff?)(?:$|[?#])',url,re.I))
def image_reference(ref):
 raw=ref.get('raw','');source=ref.get('source_attribute',raw)
 if raw.lower().startswith('data:'):
  ref=dict(ref,raw='[IMAGE]',source_attribute='[IMAGE]',url='inline-image:'+digest(raw.encode()),source_ref_sha256=digest(source.encode()))
 return dict(ref,kind='image',disposition='image-placeholder',placeholder='[IMAGE]',policy=IMAGE_POLICY)
def normalize_images(soup,base,extra=()):
 """Image markup is replaced, never extracted. IDs live on a span at the same source position."""
 from bs4 import NavigableString
 extra=set(extra);replaced=[]
 for e in list(soup.find_all(['picture','svg','img','image','use','object','embed','iframe','input','source'])):
  if e.parent is None:continue
  if e.name in ['object','embed','iframe','input','source']:
   u=e.get('data') or e.get('src') or '';is_image=e.get('type','').strip().lower().startswith('image/') or u.lower().startswith('data:image/') or image_url(u) or urljoin(base,u).split('#')[0] in extra or (e.name=='input' and e.get('type','').strip().lower()=='image')
   if not is_image:continue
  if any(getattr(p,'name',None) in ['picture','svg'] for p in e.parents):continue
  marker=soup.new_tag('span');marker.string='[IMAGE]'
  if e.get('id'):marker['id']=e['id']
  for child in e.select('[id]'):
   if child['id']!=e.get('id'):
    keep=soup.new_tag('span',id=child['id']);marker.append(keep)
  replaced.append({'tag':e.name,'source_id':e.get('id'),'source_markup_sha256':digest(str(e).encode())});e.replace_with(marker)
 for e in list(soup.find_all(['a','link'])):
  raw=e.get('href') or e.get('to') or '';m=re.search(r"pathname\s*:\s*['\"]([^'\"]+)",raw);u=urljoin(base,m.group(1) if m else raw).split('#')[0]
  if raw and (image_url(u) or u in extra):
   marker=soup.new_tag('span');marker.string='[IMAGE]'
   if e.get('id'):marker['id']=e['id']
   e.replace_with(marker);replaced.append({'tag':'image-link','source_markup_sha256':digest(raw.encode())})
 for e in list(soup.find_all(True)):
  if e.get('background'):
   e.attrs.pop('background',None);e.insert(0,NavigableString('[IMAGE]'));replaced.append({'tag':'background'})
  if e.get('poster'):
   e.attrs.pop('poster',None);e.insert(0,NavigableString('[IMAGE]'));replaced.append({'tag':'poster'})
  if e.name=='link' and 'stylesheet' in e.get('rel',[]):e.decompose();continue
  value=e.get('style') or (e.get_text() if e.name=='style' else '')
  urls=re.findall(r'url\([\s\'"]*([^\)\'\"]+)',value,re.I)
  image_sets=re.findall(r'(?:-webkit-)?image-set\([^)]*\)',value,re.I)
  if image_sets:
   for expression in image_sets:value=value.replace(expression,'none')
   e.insert_before(NavigableString('[IMAGE]'*len(image_sets)));replaced.extend({'tag':'css-image-set'} for _ in image_sets)
  images=[u for u in urls if u.lower().startswith('data:image/') or image_url(u) or urljoin(base,u) in extra or not re.search(r'\.(?:css|woff2?|ttf|otf|eot)(?:$|[?#])',u,re.I)]
  if images:
   if e.name=='style':e.replace_with(NavigableString('[IMAGE]'*len(images)))
   else:
    for u in images:value=re.sub(r'url\([\s\'\"]*'+re.escape(u)+r'[\s\'\"]*\)', 'none',value,flags=re.I)
    e['style']=value;e.insert(0,NavigableString('[IMAGE]'*len(images)))
   replaced.extend({'tag':'css-image','source_markup_sha256':digest(u.encode())} for u in images)
 return replaced
