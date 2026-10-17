"""Pure source parsers and deterministic coverage reconciliation; no network or writes."""
import copy,hashlib,json,pathlib,re,zipfile,io
from urllib.parse import urljoin,urlsplit,urlunsplit,unquote
from bs4 import BeautifulSoup
import pypdfium2
import legacy_html

def sha(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def clean(t):return re.sub(r'\s+',' ',t).strip()
def key(url):return legacy_html.doc_key(url)
def table_data(node):
 return [{'html':str(t),'rows':[[{'text':clean(c.get_text(' ',strip=True)),'rowspan':str(c.get('rowspan','1')),'colspan':str(c.get('colspan','1')),'tag':c.name} for c in row.find_all(['td','th'],recursive=False)] for row in t.find_all('tr')]} for t in node.find_all('table')]
def classify_asset(asset,config):
 asset=dict(asset);asset.setdefault('required',True);asset.setdefault('classification','owned_or_unresolved_attachment')
 # External location or an HTTP failure never makes an asset optional.
 forced=re.search(r'incorporat|adopted? by reference|appendix|attachment|official map',asset.get('context',''),re.I)
 for rule in config.get('reference_rules',[]):
  if not forced and re.search(rule['url_regex'],asset['url']) and re.search(rule['context_regex'],asset.get('context',''),re.I):
   asset.update(required=False,classification='independent_legal_layer_reference',reason=rule['reason'])
 return asset

def source_assets(node,url):
 import base64
 output=[]
 def add(target,element,attribute,raw=None):
  if not target:return
  target=urljoin(url,target.strip());asset={'url':target,'kind':element.name,'source_attribute':attribute,'required':True,'context':clean((element.parent or element).get_text(' ',strip=True))[:2500]}
  if raw is not None:asset['source_attribute_value']=raw
  if target.startswith('data:'):
   try:
    header,payload=target.split(',',1);content=base64.b64decode(payload,validate=True) if ';base64' in header else unquote(payload).encode();asset.update(url='data:sha256:'+sha(content),inline_data=True,sha256=sha(content),bytes=len(content),media_type=header[5:].split(';')[0],status='retained_inline',reason='Embedded native bytes retained in source HTML; semantic image interpretation not asserted')
   except Exception:asset.update(url='unparsed-inline:'+sha(target.encode()),status='unresolved',requires_manual_review=True,reason='Malformed or unsupported inline-data reference; raw attribute retained in HTML')
  elif target.startswith(('http:','https:')) and urlsplit(target).fragment and target.split('#')[0]==url.split('#')[0]:
   anchor=urlsplit(target).fragment;root=node
   while getattr(root,'parent',None) is not None:root=root.parent
   definition=root.find(id=anchor)
   asset.update(status='retained_inline_reference' if definition else 'unresolved',requires_manual_review=not bool(definition),sha256=sha(str(definition).encode()) if definition else None,reason='Local SVG/CSS definition resolved within retained source' if definition else 'Local SVG/CSS definition absent from retained content')
  if element.name in ['iframe','object','embed']:asset['requires_nested_asset_review']=True
  output.append(asset)
 for element in node.find_all(True):
  for attribute in (['src'] if element.name in ['img','source','video','audio','track','embed','iframe','input'] else [])+(['data'] if element.name=='object' else [])+(['poster'] if element.name=='video' else [])+(['href','xlink:href'] if element.name in ['image','use'] else []):
   if element.get(attribute):add(element[attribute],element,attribute)
  if element.name=='a' and element.get('href') and urlsplit(element['href']).path.lower().endswith(('.pdf','.svg','.png','.jpg','.jpeg','.gif','.webp','.zip','.docx')):add(element['href'],element,'href')
  if element.get('srcset'):
   raw=element['srcset']
   if 'data:' in raw:add('unparsed-srcset:'+sha(raw.encode()),element,'srcset',raw);output[-1].update(requires_manual_review=True,status='unresolved')
   else:
    for candidate in raw.split(','):
     parts=candidate.strip().split()
     if parts:add(parts[0],element,'srcset',raw)
  css=element.get('style','')+(' '+element.get_text() if element.name=='style' else '')
  for match in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)",css,re.I):add(match[2],element,'css-url',css)
 return output

def semantics(node,url):
 return {'html':str(node),'text':clean(node.get_text(' ',strip=True)),'tables':table_data(node),'links':[{'text':clean(a.get_text(' ',strip=True)),'url':urljoin(url,a['href']),'attributes':dict(a.attrs)} for a in node.select('a[href]')],'assets':source_assets(node,url),'notes':[str(a) for a in node.select('aside.annotations,[role="note"],.Footnote,.footnote')],'superscripts':[str(x) for x in node.select('sup,sub')]}
def html_records(data,item,config):
 soup=BeautifulSoup(data,'html.parser');selector=config.get('content_selector','main');node=soup.select_one(selector)
 if not node:raise ValueError('Exact content container absent: '+selector)
 if re.search('just a moment|access denied|attention required',soup.title.get_text() if soup.title else '',re.I):raise ValueError('Challenge is not legal text')
 mode=config['mode'];records=[];dispositions=[]
 if mode=='portland_titles':
  chapter=None
  for h in node.select('h2,h3'):
   title=clean(h.get_text(' ',strip=True))
   if h.name=='h2' and title.startswith('Chapter '):chapter=title
   if h.name!='h3' or not re.match(r'^\d+\.\d+\.\d+',title):continue
   body=h.parent.select_one('.field--name-field-section-body');link=h.find('a',href=True)
   if body is None or link is None:raise ValueError('Section heading without owned body/link')
   ident=re.match(r'^(\d+\.\d+\.\d+)',title)[1];s=semantics(body,item['url']);records.append(dict(s,id=ident,heading=title,path=[item['heading'],chapter],source_url=urljoin(item['url'],link['href']),unit='legal_section',document_id=item['id']))
  if not records:raise ValueError('Full-title container yielded no legal sections')
 elif mode=='legacy_codepublishing':
  page={'url':item['url'],'publication_id':config['id'],'path':item['raw_ref'],'sha256':sha(data),'content_selector':selector};snapshot={'jurisdiction_slug':config['id'],'jurisdiction':config['jurisdiction'],'snapshot_id':'source-bound','publications':[{'publication_id':config['id'],'title':config['publication']}]}
  result=legacy_html.parse_page(data,page,snapshot);dispositions=result['dispositions']
  for row,proof in zip(result['records'],result['provenance']):
   body=BeautifulSoup(row['full_text'],'html.parser');s=semantics(body,item['url']);records.append(dict(s,id=proof['node_id'],heading=row['section_name'],path=[row.get('title'),row.get('chapter'),row.get('article')],source_url=row['source_url'],unit='owned_heading_body',document_id=item['id']))
 elif mode=='html_graph' and config.get('parser')=='spokane':
  from urllib.parse import parse_qs
  query=parse_qs(urlsplit(item['url']).query)
  if 'Section' not in query:return [],[{'node_id':item['id'],'disposition':'structural','reason':'SourceTitle/Chapter navigation only; never a legal record'}]
  section=query['Section'][0];anchor=node.find('a',href='/smc/?Section='+section)
  if not anchor:raise ValueError('Exact requested Spokane section anchor absent')
  heading=clean(str(anchor.next_sibling));body=BeautifulSoup(''.join(str(x) for x in anchor.next_siblings),'html.parser');s=semantics(body,item['url'])
  if len(s['text'])<len(heading)+20:raise ValueError('Section body empty/TOC-only')
  s['text']=s['text'][len(heading):].strip();records=[dict(s,id=section,heading=heading,path=[config['publication'],section.split('.')[0]],source_url=item['url'],unit='legal_section',document_id=item['id'])]
 else:
  if not config.get('legal_marker_regex'):raise ValueError('Generic HTML document requires an explicitly qualified legal_marker_regex; no TOC-only pass')
  if not re.search(config['legal_marker_regex'],node.get_text(' ',strip=True)):raise ValueError('Expected legal body marker absent')
  for a in node.select('script,style,nav,header,footer'):a.decompose()
  s=semantics(node,item['url'])
  if len(s['text'])<30:raise ValueError('Empty/TOC-only publication content')
  records=[dict(s,id=item['id'],heading=item['heading'],path=[config['publication']],source_url=item['url'],unit='publication_html_document',document_id=item['id'])]
 if mode=='legacy_codepublishing' and records:records[0]['document_assets']=semantics(node,item['url'])['assets']
 for r in records:
  r['assets']=[classify_asset(a,config) for a in r.get('assets',[])]
  if r.get('document_assets'):r['document_assets']=[classify_asset(a,config) for a in r['document_assets']]
 for r in records:r.update(raw_ref=item['raw_ref'],raw_sha256=sha(data),jurisdiction=config['jurisdiction'],state=config['state'],publication=config['publication'])
 return records,dispositions

def pdf_records(data,item,config):
 if not data.startswith(b'%PDF-'):raise ValueError('Not PDF bytes')
 doc=pypdfium2.PdfDocument(data);records=[]
 for index in range(len(doc)):
  page=doc[index];textpage=page.get_textpage();text=textpage.get_text_range();records.append({'id':item['id']+'::page:'+str(index+1),'document_id':item['id'],'unit':'pdf_page','heading':item['heading'],'path':[config['publication'],item['heading']],'source_url':item['url']+'#page='+str(index+1),'text':text,'raw_ref':item['raw_ref'],'raw_sha256':sha(data),'physical_page':index+1,'page_count':len(doc),'character_count':textpage.count_chars(),'width':page.get_width(),'height':page.get_height(),'tables':[],'links':[],'assets':[],'jurisdiction':config['jurisdiction'],'state':config['state'],'publication':config['publication'],'semantic_review_required':True,'semantic_limit':'Page text is not section segmentation. Tables/spans, figures, reading order, PDF link annotations and incorporated standards require review; no legal-semantic completeness claim.'});textpage.close();page.close()
 doc.close();return records,[]

def archive_inventory(data,config):
 z=zipfile.ZipFile(io.BytesIO(data));seen=set();members=[];total=0
 for info in z.infolist():
  path=pathlib.PurePosixPath(info.filename)
  if path.is_absolute() or '..' in path.parts or '\\' in info.filename or info.filename in seen or info.flag_bits&1 or (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Unsafe/duplicate/encrypted ZIP entry')
  seen.add(info.filename);total+=info.file_size
  if total>config.get('max_uncompressed_bytes',600_000_000):raise ValueError('Archive expansion limit')
  if info.is_dir():continue
  content=z.read(info);members.append({'path':info.filename,'bytes':len(content),'sha256':sha(content),'crc':info.CRC})
 root=next(iter(seen)).split('/')[0]+'/'
 # ZIP top directory is dynamically observed, never extracted to filesystem.
 prefix=config.get('archive_prefix','/us/md/cities/baltimore/code').strip('/')+'/'
 canonical=[m for m in members if m['path'].startswith(root+prefix) and m['path'].endswith('/index.html')]
 if not canonical:raise ValueError('No canonical publication members in archive')
 return z,root,members,canonical

def archive_records(data,config,raw_ref):
 z,root,members,canonical=archive_inventory(data,config);records=[];owners=[];paths={m['path']:m for m in members};scope='/'+config.get('archive_prefix','/us/md/cities/baltimore/code').strip('/');all_assets=[]
 for m in canonical:
  urlpath='/'+m['path'][len(root):-len('/index.html')];source_url=config.get('public_origin','https://codes.baltimorecity.gov')+urlpath;soup=BeautifulSoup(z.read(m['path']),'html.parser');article=soup.select_one('article');owned=[]
  if not article:owners.append({'id':urlpath,'member':m['path'],'disposition':'unresolved','reason':'No article legal container'});continue
  # Source heading IDs independently identify this canonical owner, preventing aggregate/descendant duplication.
  headings=[h for h in article.select('h1,h2,h3,h4,h5,h6') if h.get('id')==urlpath]
  if len(headings)!=1:owners.append({'id':urlpath,'member':m['path'],'disposition':'unresolved','reason':'Canonical owner heading ID count !=1'});continue
  heading=headings[0];title=clean(heading.get_text(' ',strip=True));clone=BeautifulSoup(str(article),'html.parser')
  for nav in clone.select('nav,script,style'):nav.decompose()
  ownheading=next((h for h in clone.select('[id]') if h.get('id')==urlpath),None)
  # Descendant IDs are rendered by their own canonical files. Remove ranges owned by those IDs, not quoted empty-ID notes.
  descendants=[h for h in clone.select('h1[id],h2[id],h3[id],h4[id],h5[id],h6[id]') if h.get('id') and h.get('id')!=urlpath]
  for h in descendants:
   sib=h.next_sibling
   while sib:
    nxt=sib.next_sibling
    if getattr(sib,'name',None) and re.match(r'h[1-6]',sib.name) and sib.get('id'):break
    sib.extract();sib=nxt
   h.decompose()
  if ownheading:ownheading.decompose()
  body=clone.find('article');semantic=semantics(body,source_url);semantic['text']=clean(body.get_text(' ',strip=True));is_legal=any(x in heading.get('class',[]) for x in ['h__section','h__table'])
  if semantic['text'] or is_legal:
   status=not semantic['text'] and re.search('reserved|repealed|deleted|omitted|vacant|transferred|not adopted',title,re.I)
   heading_only=not semantic['text'] and not status
   if heading_only:semantic['text']=title
   r=dict(semantic,id=urlpath,heading=title,path=[scope]+urlpath[len(scope):].strip('/').split('/')[:-1],source_url=source_url,unit='legal_status' if status else ('source_heading_only' if heading_only else ('legal_section' if is_legal else 'container_owned_body')),document_id=urlpath,raw_ref=raw_ref+'!'+m['path'],raw_sha256=m['sha256'],jurisdiction=config['jurisdiction'],state=config['state'],publication=config['publication'],semantic_review_required=bool(heading_only));records.append(r);owners.append({'id':urlpath,'member':m['path'],'disposition':'included','record_id':urlpath,'member_sha256':m['sha256']})
   for asset in r['assets']:
    asset=classify_asset(asset,config)
    if asset.get('inline_data'):all_assets.append(dict(asset,owner=urlpath));continue
    u=urlsplit(asset['url']);assetpath=unquote(u.path);candidate=root+assetpath.lstrip('/');match=paths.get(candidate)
    all_assets.append(dict(asset,owner=urlpath,status='retained_in_archive' if match else 'unresolved',member=candidate if match else None,sha256=match['sha256'] if match else None))
  else:owners.append({'id':urlpath,'member':m['path'],'disposition':'excluded','reason':'Structural navigation-only; no owned legal body'})
 expectedids={o['id'] for o in owners};linked=set()
 for m in canonical:
  s=BeautifulSoup(z.read(m['path']),'html.parser')
  for a in s.select('article nav a[href]'):
   path=urlsplit(urljoin(config.get('public_origin','https://codes.baltimorecity.gov')+'/',a['href'])).path.rstrip('/')
   if path==scope or path.startswith(scope+'/'):linked.add(path)
 return records,{'members':members,'owners':owners,'assets':all_assets,'archive_root':root,'canonical_member_count':len(canonical),'missing_internal_nav_targets':sorted(linked-expectedids),'alternate_aggregate_members_excluded':len([m for m in members if m['path'].startswith(root+scope.lstrip('/')+'/') and m['path'].endswith('index.full.html')]),'archive_crc_verified':True}
