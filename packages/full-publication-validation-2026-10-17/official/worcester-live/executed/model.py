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
def semantics(node,url):
 return {'html':str(node),'text':clean(node.get_text(' ',strip=True)),'tables':table_data(node),'links':[{'text':clean(a.get_text(' ',strip=True)),'url':urljoin(url,a['href']),'attributes':dict(a.attrs)} for a in node.select('a[href]')],'assets':[{'url':urljoin(url,a.get('src') or a.get('data') or a.get('href')),'kind':a.name,'required':True} for a in node.select('img[src],object[data],embed[src],iframe[src],a[href$=".pdf"]')],'notes':[str(a) for a in node.select('aside.annotations,[role="note"],.Footnote,.footnote')],'superscripts':[str(x) for x in node.select('sup,sub')]}
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
 else:
  for a in node.select('script,style,nav,header,footer'):a.decompose()
  s=semantics(node,item['url'])
  if len(s['text'])<30:raise ValueError('Empty/TOC-only publication content')
  records=[dict(s,id=item['id'],heading=item['heading'],path=[config['publication']],source_url=item['url'],unit='publication_html_document',document_id=item['id'])]
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
   status=not semantic['text'] and re.search('reserved|repealed|deleted|omitted',title,re.I)
   if not semantic['text'] and not status:owners.append({'id':urlpath,'member':m['path'],'disposition':'unresolved','reason':'Legal heading has no body/status'});continue
   r=dict(semantic,id=urlpath,heading=title,path=[scope]+urlpath[len(scope):].strip('/').split('/')[:-1],source_url=source_url,unit='legal_status' if status else ('legal_section' if is_legal else 'container_owned_body'),document_id=urlpath,raw_ref=raw_ref+'!'+m['path'],raw_sha256=m['sha256'],jurisdiction=config['jurisdiction'],state=config['state'],publication=config['publication']);records.append(r);owners.append({'id':urlpath,'member':m['path'],'disposition':'included','record_id':urlpath,'member_sha256':m['sha256']})
   for asset in r['assets']:
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
