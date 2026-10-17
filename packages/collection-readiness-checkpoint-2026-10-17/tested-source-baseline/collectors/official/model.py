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
def redact_image_metadata(value):
 if isinstance(value,str):return re.sub(r'data:image/[^\s\"\'<>]*', '[IMAGE]', value, flags=re.I)
 if isinstance(value,list):return [redact_image_metadata(v) for v in value]
 if isinstance(value,dict):return {k:redact_image_metadata(v) for k,v in value.items()}
 return value
def table_data(node):
 tables=node.find_all('table');output=[]
 for index,table in enumerate(tables):
  parent=table.find_parent('table');parent_index=next((i for i,t in enumerate(tables) if t is parent),None)
  output.append({'html':str(table),'parent_table_index':parent_index,'rows':[[{'text':clean(c.get_text(' ',strip=True)),'rowspan':str(c.get('rowspan','1')),'colspan':str(c.get('colspan','1')),'tag':c.name} for c in row.find_all(['td','th'],recursive=False)] for row in table.find_all('tr') if row.find_parent('table') is table]})
 return output

def classify_asset(asset,config):
 asset=dict(asset);asset.setdefault('required',True)
 if asset.get('status')=='policy_omitted_image':return asset
 asset.setdefault('classification','owned_or_unresolved_attachment')
 # External location or an HTTP failure never makes an asset optional.
 forced=re.search(r'incorporat|adopted? by reference|appendix|attachment|official map',asset.get('context',''),re.I)
 for rule in config.get('reference_rules',[]):
  if not forced and re.search(rule['url_regex'],asset['url']) and re.search(rule['context_regex'],asset.get('context',''),re.I):
   asset.update(required=False,classification='independent_legal_layer_reference',status='independent_legal_layer_reference',reason=rule['reason'])
 return asset

def source_assets(node,url):
 import base64
 output=[]
 def add(target,element,attribute,raw=None):
  if not target:return
  target=urljoin(url,target.strip());asset={'url':target,'kind':element.name,'source_id':element.get('id'),'source_attribute':attribute,'required':True,'context':clean((element.parent or element).get_text(' ',strip=True))[:2500]}
  if str(element.get('type','')).lower().startswith('image/') or element.name=='input' and element.get('type','').lower()=='image':asset['media_type']='image/*' if element.name=='input' else element.get('type','image/*')
  if raw is not None:
   asset['source_attribute_value']='[IMAGE]' if 'data:image/' in raw else raw
   asset['source_attribute_sha256']=sha(raw.encode())
  if target.startswith('data:image/'):
   header,payload=target.split(',',1);asset.update(url='inline-image-ref:sha256:'+sha(target.encode()),inline_image_reference=True,media_type=header[5:].split(';')[0],source_reference_sha256=sha(target.encode()),encoded_characters=len(payload),status='policy_omitted_image',required=False,reason='User image omission: base64 image data not decoded or extracted')
  elif target.startswith('data:'):
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
 for element in [node]+node.find_all(True):
  if element.name=='svg':output.append({'url':'inline-svg-ref:sha256:'+sha(str(element).encode()),'kind':'svg','required':False,'status':'policy_omitted_image','source_id':element.get('id'),'descendant_source_ids':[x['id'] for x in element.select('[id]')],'source_reference_sha256':sha(str(element).encode()),'reason':'User image omission: no vector extraction or interpretation'})
  for attribute in (['src'] if element.name in ['img','source','video','audio','track','embed','iframe','input'] else [])+(['data'] if element.name=='object' else [])+(['poster'] if element.name=='video' else [])+(['href','xlink:href'] if element.name in ['image','use'] else []):
   if element.get(attribute):add(element[attribute],element,attribute)
  if element.name=='a' and element.get('href'):
   explicit=re.search(r'incorporat|adopted? by reference|appendix|attachment|official map',clean((element.parent or element).get_text(' ',strip=True)),re.I)
   if urlsplit(element['href']).path.lower().endswith(('.pdf','.svg','.png','.jpg','.jpeg','.gif','.webp','.zip','.docx')) or explicit:
    add(element['href'],element,'href')
    if explicit:output[-1].update(classification='source_explicit_incorporation_or_attachment',required=True)
  if element.get('background'):add(element['background'],element,'background')
  if element.get('srcset'):
   raw=element['srcset']
   if 'data:' in raw:add('unparsed-srcset:'+sha(raw.encode()),element,'srcset',raw);output[-1].update(requires_manual_review=True,status='unresolved')
   else:
    for candidate in raw.split(','):
     parts=candidate.strip().split()
     if parts:add(parts[0],element,'srcset',raw)
  css=element.get('style','')+(' '+element.get_text() if element.name=='style' else '')
  for match in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)",css,re.I):add(match[2],element,'css-url',css)
 return redact_image_metadata(output)

def image_asset(asset):
 if asset.get('kind') in ['img','picture','image','use','svg']:return True
 if asset.get('source_attribute') in ['poster','srcset','css-url','background']:return True
 if asset.get('media_type','').startswith('image/'):return True
 return bool(re.search(r'\.(?:svg|png|jpe?g|gif|webp|avif|bmp|tiff?)(?:$|[?#])',asset.get('url',''),re.I))

def sanitize_images(node):
 from bs4 import NavigableString
 clone=BeautifulSoup(str(node),'html.parser')
 # Replace outer picture/SVG once, preserving original source identifiers in a metadata span.
 for tag in list(clone.select('picture,svg,img,source')):
  if tag.parent is None:continue
  if tag.name=='source' and not (tag.get('srcset') or str(tag.get('src','')).startswith('data:image/') or str(tag.get('type','')).startswith('image/') or image_asset({'url':tag.get('src',''),'kind':'source'})):continue
  replacement=clone.new_tag('span');replacement.string='[IMAGE]'
  if tag.get('id'):replacement['data-source-image-id']=tag['id'];replacement['id']=tag['id']
  tag.replace_with(replacement)
 for tag in list(clone.select('[style],[background],style,video[poster],object[data],embed[src],iframe[src],input[type="image"],a[href]')):
  if tag.parent is None:continue
  target=tag.get('data') or tag.get('src') or tag.get('href') or ''
  if tag.name in ['object','embed','a','iframe','input'] and (target.lower().startswith('data:image/') or tag.name=='input' and tag.get('type','').lower()=='image' or tag.get('type','').lower().startswith('image/') or re.search(r'\.(?:svg|png|jpe?g|gif|webp|avif|bmp|tiff?)(?:$|[?#])',target,re.I)):tag.replace_with(NavigableString('[IMAGE]'));continue
  def marker(count):
   target=tag.find(['td','th'],recursive=False) if tag.name=='tr' else tag
   if tag.name=='table':
    target=clone.new_tag('caption');tag.insert(0,target)
   if target is not None:target.insert(0,NavigableString(' '.join('[IMAGE]' for _ in range(count))))
   else:tag.insert_before(NavigableString(' '.join('[IMAGE]' for _ in range(count))))
  if tag.get('background'):del tag['background'];marker(1)
  if tag.get('poster'):del tag['poster'];marker(1)
  css=tag.get('style','')+(tag.get_text() if tag.name=='style' else '')
  if re.search(r'url\(',css,re.I):
   count=len(re.findall(r'url\(',css,re.I));marker(count)
   if tag.name=='style':tag.insert_before(NavigableString(' '.join('[IMAGE]' for _ in range(count))));tag.decompose()
   else:tag['style']=re.sub(r'url\([^)]*\)','none',tag.get('style',''),flags=re.I)
 for el in clone.find_all(True):
  el.attrs=redact_image_metadata(el.attrs)
 for text in list(clone.find_all(string=True)):
  if 'data:image/' in str(text).lower():text.replace_with(NavigableString(redact_image_metadata(str(text))))
 return clone

def semantics(node,url):
 refs=source_assets(node,url)
 for asset in refs:
  if image_asset(asset):asset.update(required=False,status='policy_omitted_image',classification='user_requested_image_omission',placeholder='[IMAGE]',reason='User explicitly requests no image acquisition and literal[IMAGE] replacement; reference/IDs retained, no pixels extracted')
 clean_node=sanitize_images(node)
 return {'html':str(clean_node),'text':clean(clean_node.get_text(' ',strip=True)),'tables':table_data(clean_node),'links':redact_image_metadata([{'text':clean(a.get_text(' ',strip=True)),'url':('inline-image-ref:sha256:'+sha(a['href'].encode()) if a['href'].startswith('data:image/') else urljoin(url,a['href'])),'attributes':{k:('[IMAGE]' if isinstance(v,str) and 'data:image/' in v else v) for k,v in a.attrs.items()}} for a in node.select('a[href]')]),'assets':refs,'image_placeholder_count':clean_node.get_text().count('[IMAGE]'),'notes':[str(sanitize_images(a)) for a in node.select('aside.annotations,[role="note"],.Footnote,.footnote')],'superscripts':[str(x) for x in clean_node.select('sup,sub')]}

def html_records(data,item,config):
 soup=BeautifulSoup(data,'html.parser');selector=config.get('content_selector','main');node=soup.select_one(selector)
 if not node:raise ValueError('Exact content container absent: '+selector)
 if re.search('just a moment|access denied|attention required',soup.title.get_text() if soup.title else '',re.I):raise ValueError('Challenge is not legal text')
 mode=config['mode'];records=[];dispositions=[]
 if mode=='portland_titles':
  chapter=None;owned_fields=set();citation=r'^(\d+[A-Z]?\.\d+[A-Z]?\.\d+[A-Z]?)\b'
  for header in node.select('.view-display-id-page_title_all > .view-header'):
   if clean(header.get_text(' ',strip=True)):
    text=semantics(header,item['url']);records.append(dict(text,id=item['id']+'::title-note',heading=item['heading']+' source note',path=[item['heading']],source_url=item['url'],unit='container_owned_body',document_id=item['id']))
  for h in node.select('h2,h3'):
   title=clean(h.get_text(' ',strip=True));is_chapter=h.name=='h2' and title.startswith('Chapter ');is_container=h.name=='h2' and 'node--embedded' in h.parent.get('class',[]) and h.find('a',href=True) is not None
   if is_chapter:chapter=title
   if not is_container and (h.name!='h3' or not re.match(citation,title)):continue
   container=h.parent;fields=[e for e in container.select('.field--name-field-section-body,.field--name-field-prefix-note,.field--name-field-suffix-note') if e.find_parent(class_='node--embedded') is container];owned_fields.update(id(e) for e in fields);body=BeautifulSoup(''.join(str(e) for e in fields),'html.parser') if fields else None;link=h.find('a',href=True)
   if link is None:raise ValueError('Code heading without source link')
   if is_container:
    if body is not None and clean(body.get_text(' ',strip=True)):
     text=semantics(body,item['url']);records.append(dict(text,id=urljoin(item['url'],link['href'])+'::owned-note',heading=title,path=[item['heading'],chapter],source_url=urljoin(item['url'],link['href']),unit='container_owned_body',document_id=item['id']))
    continue
   ident=re.match(citation,title)[1]
   if body is None:
    if re.search(r'\b(?:reserve|reserved|repeal|repealed|deleted)\b',title,re.I):
     status=semantics(h,item['url']);records.append(dict(status,id=ident,heading=title,path=[item['heading'],chapter],source_url=urljoin(item['url'],link['href']),unit='legal_status',document_id=item['id']));continue
    raise ValueError('Section heading without owned body: '+title)
   text=semantics(body,item['url']);records.append(dict(text,id=ident,heading=title,path=[item['heading'],chapter],source_url=urljoin(item['url'],link['href']),unit='legal_status' if not container.select_one('.field--name-field-section-body') and re.search(r'\b(?:repealed|reserved|deleted)\b',text['text'],re.I) else 'legal_section',document_id=item['id']))
  unowned=[clean(e.get_text(' ',strip=True))[:150] for e in node.select('.field--name-field-section-body,.field--name-field-prefix-note,.field--name-field-suffix-note') if id(e) not in owned_fields and clean(e.get_text(' ',strip=True))]
  if unowned:raise ValueError('Unowned Portland legal field: '+repr(unowned[:3]))
  if not records:raise ValueError('Full-title container yielded no legal sections')
 elif mode=='czo_sections':
  if not re.search(config['legal_marker_regex'],node.get_text(' ',strip=True)):raise ValueError('Qualified CZO publication identity absent')
  canonical={}
  for h in node.select('h1,h2,h3,h4,h5,h6'):
   if h.find_parent('table'):continue
   anchor=h.get('id');copylink=h.select_one('.copy-link[data-content]')
   if anchor and copylink:
    control=BeautifulSoup(copylink['data-content'],'html.parser').find('input',value=True)
    if control:
     target=control['value'];parts=urlsplit(target)
     if parts.hostname!='czo.nola.gov' or not parts.path.startswith('/Article-') or parts.fragment!=anchor:raise ValueError('CZO observed canonical section permalink mismatch')
     canonical[anchor]=target
  scoped=semantics(node,item['url'])
  for rule in config.get('content_exclusions',[]):
   for el in node.select(rule['selector']):el.decompose()
  wrapped='<div id="qualified-czo">'+str(node)+'</div>'
  page={'url':item['url'],'publication_id':config['id'],'path':item['raw_ref'],'sha256':sha(data),'content_selector':'#qualified-czo','duplicate_locator_strategy':'source_occurrence'};snapshot={'jurisdiction_slug':config['id'],'jurisdiction':config['jurisdiction'],'snapshot_id':'source-bound','publications':[{'publication_id':config['id'],'title':config['publication']}]};parsed=legacy_html.parse_page(wrapped.encode(),page,snapshot);dispositions=parsed['dispositions'];headings={n['node_id']:n for n in parsed['nodes']}
  for row,proof in zip(parsed['records'],parsed['provenance']):
   source=headings[proof['node_id']];body=BeautifulSoup(row['full_text'],'html.parser');semantic=semantics(body,item['url']);anchor=source['locator']['value'];url=canonical.get(anchor,row['source_url']);records.append(dict(semantic,id=proof['node_id'],heading=source['display_heading'],path=[x for x in [config['publication'],row.get('article'),row.get('chapter')] if x],source_url=url,unit='legal_section' if source['node_kind']=='section' else 'container_owned_body',document_id=item['id'],parent_node_id=source['parent_node_id'],source_order=source['source_order'],source_locator=source['locator'],semantic_review_required=bool(source['locator'].get('source_occurrence')),source_locator_limit='Exact duplicate printed source IDs retained with explicit occurrence suffix; no corrected citation inferred.' if source['locator'].get('source_occurrence') else None))
  if records:
   records[0]['document_assets']=scoped['assets'];records[0]['source_heading_inventory']=[{k:v for k,v in n.items() if k in ['node_id','parent_node_id','source_order','display_heading','source_url','locator']} for n in parsed['nodes']]
 elif mode=='legacy_codepublishing':
  page={'url':item['url'],'publication_id':config['id'],'path':item['raw_ref'],'sha256':sha(data),'content_selector':selector};snapshot={'jurisdiction_slug':config['id'],'jurisdiction':config['jurisdiction'],'snapshot_id':'source-bound','publications':[{'publication_id':config['id'],'title':config['publication']}]}
  try:result=legacy_html.parse_page(data,page,snapshot)
  except ValueError as error:
   if 'navigation/empty document' in str(error) or 'no inventoried legal headings' in str(error):
    stripped=legacy_html.content(legacy_html.decode(data),selector)
    for heading in stripped.select('h1,h2,h3,h4,h5,h6'):heading.decompose()
    if not clean(stripped.get_text(' ',strip=True)) and (node.select('.CiteTOC,.ctoc,.TitleTOC_outer,.TitleTOC_inner,.CHTOC,.digTitle,.digCH') or node.select_one('h1#cityname') and node.select_one('h2#codification')):return [],[{'node_id':item['id'],'disposition':'structural','reason':'Explicit publisherTOC-only container; descendants dynamically traversed, zero legalrecords'}]
   raise
  dispositions=result['dispositions']
  for row,proof in zip(result['records'],result['provenance']):
   body=BeautifulSoup(row['full_text'],'html.parser');s=semantics(body,item['url']);node_kind=next(n['node_kind'] for n in result['nodes'] if n['node_id']==proof['node_id']);records.append(dict(s,id=proof['node_id'],heading=row['section_name'],path=[row.get('title'),row.get('chapter'),row.get('article')],source_url=row['source_url'],unit='legal_section' if node_kind=='section' else 'container_owned_body',document_id=item['id']))
 elif mode=='html_graph' and config.get('parser')=='spokane':
  from urllib.parse import parse_qs
  query=parse_qs(urlsplit(item['url']).query)
  if 'Section' not in query:return [],[{'node_id':item['id'],'disposition':'structural','reason':'SourceTitle/Chapter navigation only; never a legal record'}]
  section=query['Section'][0];anchor=node.find('a',href='/smc/?Section='+section)
  if not anchor:raise ValueError('Exact requested Spokane section anchor absent')
  heading=clean(str(anchor.next_sibling));body=BeautifulSoup(''.join(str(x) for x in anchor.next_siblings),'html.parser');s=semantics(body,item['url'])
  if len(s['text'])<len(heading)+20 and not s.get('image_placeholder_count'):raise ValueError('Section body empty/TOC-only')
  s['text']=s['text'][len(heading):].strip();records=[dict(s,id=section,heading=heading,path=[config['publication'],section.split('.')[0]],source_url=item['url'],unit='legal_section',document_id=item['id'])]
 else:
  if not config.get('legal_marker_regex'):raise ValueError('Generic HTML document requires an explicitly qualified legal_marker_regex; no TOC-only pass')
  if not re.search(config['legal_marker_regex'],node.get_text(' ',strip=True)):raise ValueError('Expected legal body marker absent')
  for rule in config.get('content_exclusions',[]):
   for control in node.select(rule['selector']):control.decompose()
  for a in node.select('script,nav,header,footer'):a.decompose()
  s=semantics(node,item['url']);bodycheck=BeautifulSoup(str(node),'html.parser')
  for heading in bodycheck.select('h1,h2,h3,h4,h5,h6'):heading.decompose()
  if len(clean(bodycheck.get_text(' ',strip=True)))<30 and not s.get('image_placeholder_count'):raise ValueError('Heading/TOC/image-only document has no qualified operative text; manual review required')
  if len(s['text'])<30 and not s.get('image_placeholder_count'):raise ValueError('Empty/TOC-only publication content')
  if config.get('content_exclusions'):s['source_control_exclusions']=config['content_exclusions']
  records=[dict(s,id=item['id'],heading=item['heading'],path=[config['publication']],source_url=item['url'],unit='image_only_publication' if len(clean(bodycheck.get_text(' ',strip=True)))<30 else 'publication_html_document',document_id=item['id'])]
 if mode=='legacy_codepublishing' and records:
  scoped=semantics(node,item['url']);records[0]['document_assets']=scoped['assets'];missing_markers=max(0,scoped['image_placeholder_count']-sum(r.get('image_placeholder_count',0) for r in records))
  if missing_markers:records[0]['html']+='\n'+' '.join('[IMAGE]' for _ in range(missing_markers));records[0]['text']+='\n'+' '.join('[IMAGE]' for _ in range(missing_markers));records[0]['image_placeholder_count']+=missing_markers;records[0]['document_level_image_placeholders']=missing_markers
 if mode=='czo_sections':
  for r in records:
   for asset in r.get('assets',[])+r.get('document_assets',[]):
    u=urlsplit(asset['url'])
    if u.hostname=='czo.nola.gov' and u.fragment and node.find(id=u.fragment):asset.update(status='retained_inline_reference',classification='internal_legal_cross_reference',sha256=sha(str(node.find(id=u.fragment)).encode()),reason='Exact referenced section ID exists within this complete native print-all legal document')
 for r in records:
  r['assets']=[classify_asset(a,config) for a in r.get('assets',[])]
  if r.get('document_assets'):r['document_assets']=[classify_asset(a,config) for a in r['document_assets']]
 for r in records:r.update(raw_ref=item['raw_ref'],raw_sha256=sha(data),jurisdiction=config['jurisdiction'],state=config['state'],publication=config['publication'])
 return records,dispositions

def qualify_attachment(data,url,config):
 rule=next((r for r in config.get('attachment_qualifications',[]) if r['url']==url),None)
 if not rule:return qualify_pdf_attachment(data) if urlsplit(url).path.lower().endswith('.pdf') else None
 if rule['format']!='html':raise ValueError('Unqualified attachment format')
 soup=BeautifulSoup(data,'html.parser');matches=soup.select(rule['content_selector'])
 if len(matches)!=1:raise ValueError('Exact qualified nonimage attachment container absent')
 node=matches[0]
 for selector in rule.get('remove_selectors',[]):
  for el in node.select(selector):el.decompose()
 text=clean(node.get_text(' ',strip=True))
 if len(text)<100 or any(token not in text for token in rule['identity_tokens']):raise ValueError('Qualified legal attachment section/identity mismatch')
 normalized=semantics(node,url)
 if any(a.get('required') and a.get('status') not in ['retained_inline','retained_inline_reference'] for a in normalized['assets']):raise ValueError('Qualified HTML attachment contains unresolved required nested nonimage references')
 return {'format':'HTML','source_url':url,'qualification_rule':rule,'normalized':normalized,'semantic_limit':'Exact source-designated statute body; separate legal layer, no broad external-law consolidation asserted.'}

def qualify_pdf_attachment(data):
 if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-1024:]:raise ValueError('Required PDF attachment has no complete native PDF envelope')
 doc=pypdfium2.PdfDocument(data)
 try:
  if not len(doc):raise ValueError('Required PDF attachment has zero pages')
  for i in range(len(doc)):
   page=doc[i]
   try:
    if page.get_width()<=0 or page.get_height()<=0:raise ValueError('Required PDF attachment page invalid')
    text=page.get_textpage();text.count_chars();text.close()
   finally:page.close()
  return {'format':'PDF','page_count':len(doc),'validation':'PDFium all pages load with text access; native EOF present; no image extraction; legal semantics not established'}
 finally:doc.close()

def pdf_records(data,item,config):
 if config.get('pdf_normalization')=='coordinate-v1':
  import pdf_structure
  return pdf_structure.pages(data,item,config)
 if config.get('pdf_normalization') not in [None,'stream-v1']:raise ValueError('Unqualified PDF normalization mode')
 if not data.startswith(b'%PDF-'):raise ValueError('Not PDF bytes')
 doc=pypdfium2.PdfDocument(data);records=[]
 for index in range(len(doc)):
  page=doc[index];textpage=page.get_textpage();text=textpage.get_text_range();images=sum(1 for obj in page.get_objects(max_depth=15) if obj.type==pypdfium2.raw.FPDF_PAGEOBJ_IMAGE);text+=('\n'+'\n'.join('[IMAGE]' for _ in range(images))) if images else '';records.append({'id':item['id']+'::page:'+str(index+1),'document_id':item['id'],'unit':'pdf_page','heading':item['heading'],'path':[config['publication'],item['heading']],'source_url':item['url']+'#page='+str(index+1),'text':text,'raw_ref':item['raw_ref'],'raw_sha256':sha(data),'image_placeholder_count':images,'image_policy':'No image extraction. Detected raster image objects represented as literal[IMAGE] appended after page text; exact placement/vector illustration detection not established.','physical_page':index+1,'page_count':len(doc),'character_count':textpage.count_chars(),'width':page.get_width(),'height':page.get_height(),'tables':[],'links':[],'assets':[],'jurisdiction':config['jurisdiction'],'state':config['state'],'publication':config['publication'],'semantic_review_required':True,'semantic_limit':'Page text is not section segmentation. Tables/spans, figures, reading order, PDF link annotations and incorporated standards require review; no legal-semantic completeness claim.'});textpage.close();page.close()
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
  body=clone.find('article');semantic=semantics(body,source_url);is_legal=any(x in heading.get('class',[]) for x in ['h__section','h__table'])
  if semantic['text'] or is_legal:
   status=not semantic['text'] and re.search('reserved|repealed|deleted|omitted|vacant|transferred|not adopted',title,re.I)
   heading_only=not semantic['text'] and not status
   if heading_only:semantic['text']=title
   r=dict(semantic,id=urlpath,heading=title,path=[scope]+urlpath[len(scope):].strip('/').split('/')[:-1],source_url=source_url,unit='legal_status' if status else ('source_heading_only' if heading_only else ('legal_section' if is_legal else 'container_owned_body')),document_id=urlpath,raw_ref=raw_ref+'!'+m['path'],raw_sha256=m['sha256'],jurisdiction=config['jurisdiction'],state=config['state'],publication=config['publication'],semantic_review_required=bool(heading_only));records.append(r);owners.append({'id':urlpath,'member':m['path'],'disposition':'included','record_id':urlpath,'member_sha256':m['sha256']})
   for asset in r['assets']:
    asset=classify_asset(asset,config)
    if not asset.get('required',True):all_assets.append(dict(asset,owner=urlpath));continue
    if asset.get('inline_data'):all_assets.append(dict(asset,owner=urlpath));continue
    u=urlsplit(asset['url']);assetpath=unquote(u.path);candidate=root+assetpath.lstrip('/');match=paths.get(candidate)
    if not match and u.hostname==urlsplit(config.get('public_origin','https://codes.baltimorecity.gov')).hostname and candidate.rstrip('/')+'/index.html' in paths:
     candidate=candidate.rstrip('/')+'/index.html';match=paths[candidate];asset.update(classification='internal_legal_cross_reference',target_owner_id=assetpath.rstrip('/'))
     if u.fragment and not BeautifulSoup(z.read(candidate),'html.parser').find(id=unquote(u.fragment)):match=None
    all_assets.append(dict(asset,owner=urlpath,status='retained_in_archive' if match else 'unresolved',member=candidate if match else None,sha256=match['sha256'] if match else None))
  else:owners.append({'id':urlpath,'member':m['path'],'disposition':'excluded','reason':'Structural navigation-only; no owned legal body'})
 expectedids={o['id'] for o in owners};linked=set()
 for m in canonical:
  s=BeautifulSoup(z.read(m['path']),'html.parser')
  for a in s.select('article nav a[href]'):
   path=urlsplit(urljoin(config.get('public_origin','https://codes.baltimorecity.gov')+'/',a['href'])).path.rstrip('/')
   if path==scope or path.startswith(scope+'/'):linked.add(path)
 return records,{'members':members,'owners':owners,'assets':all_assets,'archive_root':root,'canonical_member_count':len(canonical),'missing_internal_nav_targets':sorted(linked-expectedids),'alternate_aggregate_members_excluded':len([m for m in members if m['path'].startswith(root+scope.lstrip('/')+'/') and m['path'].endswith('index.full.html')]),'archive_crc_verified':True}
