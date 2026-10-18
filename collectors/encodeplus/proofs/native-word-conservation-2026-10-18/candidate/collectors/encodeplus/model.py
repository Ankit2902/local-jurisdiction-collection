"""Publication inventory and exclusive source-node ownership; no network."""
import copy,csv,datetime,gzip,io,json,re
from urllib.parse import urljoin,urlparse,parse_qs
from bs4 import BeautifulSoup,Comment,NavigableString
from .util import digest,hash_json
from .reference_qualifications import authority_reference

def decode(data,headers):
 coding=next((v for k,v in headers.items() if k.lower()=='content-encoding'),'').lower()
 if coding=='gzip':data=gzip.decompress(data)
 elif coding=='br':
  import brotli
  data=brotli.decompress(data)
 return data.decode('utf-8-sig')
def clean(s):return ' '.join(str(s).split())
BLOCK_TAGS={'address','article','aside','blockquote','caption','dd','div','dl','dt','fieldset','figcaption','figure','footer','form','h1','h2','h3','h4','h5','h6','header','hr','li','main','nav','ol','p','pre','section','table','tbody','td','th','thead','tr','ul'}
def source_text(el):
 """Preserve inline source joins; add only DOM block/BR boundaries, never spaces between font spans."""
 chunks=[]
 def walk(node):
  if isinstance(node,Comment):return
  if isinstance(node,NavigableString):chunks.append(re.sub(r'\s+',' ',str(node)));return
  tag=getattr(node,'name',None)
  if tag in {'script','style'}:return
  if tag=='br':chunks.append('\n');return
  if tag in BLOCK_TAGS:chunks.append('\n')
  for child in node.children:walk(child)
  if tag in BLOCK_TAGS:chunks.append('\n')
 walk(el)
 return '\n'.join(clean(line) for line in ''.join(chunks).splitlines() if clean(line))
def heading(section):
 for h in section.find_all(re.compile('^h[1-6]$')):
  if h.find_parent('section',attrs={'data-secid':True})==section:
   clone=copy.deepcopy(h)
   for sup in clone.find_all('sup'):sup.decompose()
   definition=clone.select_one('.def')
   return clean(source_text(definition)) if definition else clean(source_text(clone))
 return ''
def inventory(html,cfg):
 soup=BeautifulSoup(html,'html.parser');head=soup.select_one('#toc-pagehead');assert head and clean(head.get_text(' ',strip=True))==cfg['identity'],'Wrong publication identity'
 nodes=[];seen=set()
 for li in soup.select('#toc-list li.tocLink'):
  m=re.fullmatch('secid-x([0-9]+)',li.get('id',''));assert m,'Unknown TOC ID shape';ident=m.group(1);assert ident not in seen,'Duplicate TOC ID';seen.add(ident);a=li.select_one('a[href]');label=li.select_one('.toc-item');assert a and label
  url=urljoin(cfg['base'],a['href']);assert parse_qs(urlparse(url).query).get('secid')==[ident],'TOC link/ID mismatch'
  nodes.append({'id':ident,'heading':clean(source_text(label)),'viewer_url':url,'has_children':bool(re.search(r',\s*true\s*\)',a.get('onclick',''))),'declared_depth':next((x[len('toc-level'):] for x in li.find_parent('ul').get('class',[]) if x.startswith('toc-level')),None)})
 assert nodes,'Empty inventory'
 # Flat source inventory is canonical. TOC declared depths never determine body parentage.
 return {'identity':cfg['identity'],'base':cfg['base'],'nodes':nodes,'sha256':hash_json(nodes),'hierarchy_source':'canonical body DOM ancestry and response breadcrumbs; TOC depth is advisory only'}
IMAGE_SUFFIX=re.compile(r'\.(png|jpe?g|gif|svg|webp|tiff?|bmp|ico|avif)$',re.I)
def image_url(value):return value.lower().startswith('data:image/') or bool(IMAGE_SUFFIX.search(urlparse(value).path))
def redact_text_image_uris(value):
 """Quoted image values or terminal URI tokens only; ambiguous bare prose fails closed.
 No payload decoding, image reads or guessed whitespace/prose boundary is allowed.
 """
 value=str(value);chunks=[];position=0
 for match in re.finditer(r'data:image/',value,re.I):
  if match.start()<position:continue
  start=match.start();chunks.append(value[position:start])
  quote=value[start-1] if start and value[start-1] in ['"',"'"] else None
  if quote:
   end=value.find(quote,match.end())
   if end<0:raise ValueError('Unsupported ambiguous image text boundary; source sha256='+digest(value.encode()))
  else:
   token=re.match(r'[^\s"\'<>]+',value[start:]);end=start+len(token.group()) if token else start
   if value[end:].strip():raise ValueError('Unsupported ambiguous image text boundary; source sha256='+digest(value.encode()))
  chunks.append('[IMAGE]');position=end
 chunks.append(value[position:]);return ''.join(chunks)
def replace_images(body,base,known_image_urls=()):
 """User policy: never fetch/extract graphics; retain refs and literal placeholders."""
 images=[]
 def remember(el,attr,value):
  url=urljoin(base,value) if value else None;inline='data:image/' in str(value or '').lower();alt=el.get('alt');alt_inline='data:image/' in str(alt or '').lower()
  images.append({'tag':el.name,'attribute':attr,'url':url if not inline and not (url or '').lower().startswith('data:') else None,'inline_data_sha256':digest(str(value).encode()) if inline or (url or '').lower().startswith('data:') else None,'alt':'[IMAGE]' if alt_inline else alt,'alt_inline_data_sha256':digest(str(alt).encode()) if alt_inline else None,'placeholder':'[IMAGE]','disposition':'Intentional user-policy skip; no image request/extraction'})
 for el in [body]+list(body.find_all(True)):
  if el is not body and (el.parent is None or not any(parent is body for parent in el.parents)):continue
  for attr_name,attr_value in list(el.attrs.items()):
   if 'data:image/' in str(attr_value).lower() and attr_name not in ['src','href','xlink:href','data','srcset','style']:
    remember(el,attr_name,str(attr_value));el[attr_name]='[IMAGE]'
  if el.get('background'):remember(el,'background',el['background']);del el['background'];el.append('[IMAGE]')
  if el.name=='style':
   css_values=re.findall(r'url\([\'\"]?([^\)\'\"]+)',el.get_text())
   if css_values:
    for value in css_values:remember(el,'css-rule',value)
    el.replace_with(' '.join('[IMAGE]' for value in css_values))
   continue
  graphic=el.name in ['img','picture','svg','image'] or (el.name=='input' and el.get('type','').lower()=='image') or (el.name in ['object','embed','source'] and el.get('type','').strip().lower().startswith('image/'))
  attr='src' if el.get('src') else 'href' if el.get('href') else 'xlink:href' if el.get('xlink:href') else 'data' if el.get('data') else None
  linked_graphic=el.name in ['a','object','embed','source'] and attr and (image_url(el[attr]) or urljoin(base,el[attr]) in known_image_urls)
  if graphic or linked_graphic:
   if el.name in ['picture','svg']:
    for child in el.find_all(True):
     for a in ['src','href','xlink:href','data','srcset']:
      if child.get(a):remember(child,a,child[a])
   if attr:remember(el,attr,el[attr])
   if el.get('srcset'):remember(el,'srcset',el['srcset'])
   if not attr and el.name in ['svg','picture']:remember(el,'inline',None)
   el.replace_with('[IMAGE]');continue
  if el.get('poster'):remember(el,'poster',el['poster']);del el['poster'];el.insert_before('[IMAGE]')
  style=el.get('style','');values=re.findall(r'url\([\'\"]?([^\)\'\"]+)',style)
  if values:
   for value in values:remember(el,'style',value)
   del el['style'];el.append('[IMAGE]')
  for attr_name,attr_value in list(el.attrs.items()):
   if 'data:image/' in str(attr_value).lower():remember(el,attr_name,str(attr_value));el[attr_name]='[IMAGE]'
 for node in list(body.find_all(string=True)):
  if 'data:image/' in str(node).lower():
   remember(node.parent,'text-node',str(node))
   if isinstance(node,Comment):node.extract()
   else:node.replace_with(redact_text_image_uris(str(node)))
 return images
def refs(body,base,dispositions=None):
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
   context=clean((el.find_parent(['p','li','td']) or el.parent).get_text(' ',strip=True));target=urljoin(base,h);target_parts=urlparse(target);local_doc=target_parts.netloc==urlparse(base).netloc and target_parts.path.startswith(urlparse(base).path) and bool(re.search(r'doc-view(?:er)?\.aspx$',target_parts.path))
   incorporated=bool(re.search(r'\b(incorporat(?:ed|ion)|adopt(?:ed|ion)|made a part|integral part)\b',context,re.I) and re.search(r'\b(map|plan|standard|manual|document|appendix|exhibit|schedule|code|ordinance|resolution)\b',context,re.I)) and not local_doc and not h.startswith('#')
   direct_document=bool(re.search(r'\.(pdf|docx?|xlsx?|csv|zip)$',path) or any(x in path for x in ['doclibrary.aspx','download.aspx']))
   relation=authority_reference(el,base) if incorporated and not direct_document else None
   if relation is not None:
    if dispositions is not None:dispositions.append(relation)
   elif not image_url(h) and (direct_document or incorporated):found.append((el,'href',h,True))
  for value in re.findall(r'url\([\'\"]?([^\)\'\"]+)',el.get('style','')):found.append((el,'style',value,True))
 result=[]
 for el,attr,value,required in found:
  url=urljoin(base,value)
  if el.name in ['img','picture','svg','image','use'] or attr in ['srcset','style'] or image_url(value):continue
  result.append({'url':url,'attribute':attr,'tag':el.name,'alt':el.get('alt'),'required':required,'supported_scheme':urlparse(url).scheme in ['https','http','data']})
 return result
def omit_equivalent_date_sort_keys(body):
 """Only an exactly equivalent hidden ISO/visible US date is navigation sort metadata."""
 ledger=[];cells=body.find_all(['td','th'])
 for span in list(body.find_all('span',style=True)):
  if not re.search(r'(?:^|;)\s*display\s*:\s*none(?:\s*!important)?\s*(?:;|$)',span['style'],re.I):continue
  hidden=clean(source_text(span));cell=span.find_parent(['td','th'])
  if cell is None or not re.fullmatch(r'\d{4}/\d{2}/\d{2}',hidden):continue
  clone=copy.deepcopy(cell);match=next((x for x in clone.find_all('span') if str(x)==str(span)),None)
  if match is None:continue
  match.decompose();visible=clean(source_text(clone))
  if not re.fullmatch(r'\d{2}/\d{2}/\d{4}',visible):continue
  try:equivalent=datetime.datetime.strptime(hidden,'%Y/%m/%d').date()==datetime.datetime.strptime(visible,'%m/%d/%Y').date()
  except ValueError:equivalent=False
  if not equivalent:continue
  ledger.append({'owned_cell_index':next(i for i,x in enumerate(cells) if x is cell),'hidden_html':str(span),'hidden_date':hidden,'visible_date':visible,'disposition':'Display-none ISO date is exactly equivalent to sole visible cell date; publisher sort key omitted from substantive text only, original owned/source HTML retained'})
  span.decompose()
 return ledger

def parse_document(html,requested,cfg,known,known_image_urls=()):
 soup=BeautifulSoup(html,'html.parser');page=soup.select_one('#thePage');assert page and page.get('secid')==requested,'Requested container identity mismatch'
 sections=page.select('section[data-secid]');ids=[s['data-secid'] for s in sections];assert len(ids)==len(set(ids)),'Duplicate body source IDs';assert requested in ids,'Requested node absent'
 crumbs=[]
 for a in soup.select('#pageControls .breadCrumbs .breadCrumbs a'):
  q=parse_qs(urlparse(a.get('href','')).query);crumbs.append({'id':q.get('secid',[None])[0],'heading':clean(source_text(a)),'href':urljoin(cfg['base'],a.get('href',''))})
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
 selected=next(el for el in sections if el['data-secid']==requested);selected_key=section_key(selected)
 scoped=[];context_ids=[]
 for el in sections:
  key=section_key(el)
  belongs=el is selected or (selected_key and key and key.startswith(selected_key+'-')) or any(parent is selected for parent in el.find_parents('section',attrs={'data-secid':True}))
  if belongs:scoped.append(el)
  else:
   # Publisher emits ancestor heading stubs around selected content. They supply paths, never bodies/coverage.
   assert key and selected_key and selected_key.startswith(key+'-'),'Unexplained source section outside requested subtree: '+el['data-secid']
   context_ids.append(el['data-secid'])
 for source in scoped:
  ident=source['data-secid'];h=heading(source);heading_source='body_heading' if h else 'toc_label' if ident in known else 'definition_label' if source.select_one('.def') else 'absent_in_publisher_source';h=h or known.get(ident,{}).get('heading') or (clean(source_text(source.select_one('.def'))) if source.select_one('.def') else '')
  parents=list(reversed(source.find_parents('section',attrs={'data-secid':True})))
  key=section_key(source)
  if not parents and key:
   parts=key.split('-');parent_keys=['-'.join(parts[:i]) for i in range(1,len(parts))];parents=[keys[k] for k in parent_keys if k in keys]
  ancestry=[{'id':p['data-secid'],'heading':heading(p) or known.get(p['data-secid'],{}).get('heading') or (clean(source_text(p.select_one('.def'))) if p.select_one('.def') else None)} for p in parents]
  canonical_prefix=[]
  for crumb in prefix:
   params=parse_qs(urlparse(crumb.get('href','')).query);toc=params.get('tocid',[None])[0];crumb_key='_'+toc.replace('.','-') if toc else None
   if key and crumb_key and not key.startswith(crumb_key+'-'):continue
   if any(parent['heading']==crumb['heading'] for parent in ancestry) or crumb['heading']==h:continue
   canonical_prefix.append({'id':keys[crumb_key]['data-secid'] if crumb_key in keys else crumb['id'],'heading':crumb['heading']})
  canonical_path=canonical_prefix+ancestry
  owned=copy.deepcopy(source)
  for descendant in list(owned.find_all('section',attrs={'data-secid':True})):
   if descendant.find_parent('section',attrs={'data-secid':True})==owned:descendant.decompose()
  omitted=[]
  for el in owned.select('.archiveNotice.nullValue'):omitted.append(clean(el.get_text(' ',strip=True)));el.decompose()
  image_refs=replace_images(owned,cfg['base'],known_image_urls)
  body=copy.deepcopy(owned);hidden_sort_keys=omit_equivalent_date_sort_keys(body)
  own_h=next((x for x in body.find_all(re.compile('^h[1-6]$')) if x.find_parent('section',attrs={'data-secid':True})==body),None)
  operative_heading=False
  if own_h:
   definition=own_h.select_one('.def');whole=clean(source_text(own_h))
   operative_heading=bool(definition and whole!=clean(source_text(definition))) or bool(ident not in known and re.search(r'\b(shall|means|is defined)\b',whole,re.I))
   if operative_heading:own_h.name='p';own_h['data-source-operative-heading']='retained'
   else:own_h.decompose()
  text=source_text(body);tables=[]
  for table in body.find_all('table'):
   rows=[]
   for tr in table.find_all('tr'):
    if tr.find_parent('table')!=table:continue
    rows.append([{'text':clean(source_text(c)),'tag':c.name,'rowspan':c.get('rowspan','1'),'colspan':c.get('colspan','1'),'html':str(c)} for c in tr.find_all(['td','th']) if c.find_parent('tr')==tr])
   tables.append(rows)
  for mini in body.select('.mini-TOC'):mini.decompose()
  # Mini-TOCs are navigation, never a substantive container body.
  text=source_text(body)
  reference_dispositions=[];assets=refs(body,cfg['base'],reference_dispositions);notes=[clean(source_text(x)) for x in body.select('.archiveNotice,.footnote,.note')]
  if text or assets:kind='operative_or_descriptive_body';disposition='Exclusive legal/descriptive body retained'
  elif known.get(ident,{}).get('has_children') or (key and any(k.startswith(key+'-') for k in keys)):kind='structural_container';disposition='Explicit container has_children/source body ancestry, no owned substantive text'
  elif re.search(r'\b(repealed|reserved|omitted)\b',h,re.I):kind='source_excluded_repealed_or_reserved';disposition='Explicit source heading disposition retained verbatim'
  else:kind='source_empty_unresolved';disposition='Unexplained empty operative leaf; source has no owned body or asset. Retained for inventory accounting but blocks publication text completeness'

  records.append({'id':ident,'heading':h,'heading_source':heading_source,'toc_heading':known.get(ident,{}).get('heading'),'toc_heading_matches':h==known[ident]['heading'] if ident in known else None,'path':canonical_path,'parent_id':canonical_path[-1]['id'] if canonical_path else None,'ownership':'exclusive section body; descendant sections removed','kind':kind,'disposition':disposition,'canonical_body_key':key,'hierarchy_method':'Observed body class ancestry plus DOM and response breadcrumbs; not TOC declared depth','page_ownership_ledger':{'unowned_legal_text':0,'unowned_assets':0,'excluded_controls':omitted_controls,'context_section_ids':context_ids,'context_disposition':'Ancestor heading stubs provide canonical hierarchy only; excluded from acquired body IDs'},'text':text,'html':str(owned),'body_html':str(body),'operative_heading_retained_as_body':operative_heading,'body_sha256':digest(str(owned).encode()),'tables':tables,'assets':assets,'image_refs':image_refs,'image_policy':'literal [IMAGE]; intentional skip, no image fetch','image_only':bool(image_refs) and not bool(text.replace('[IMAGE]','').strip()),'links':[{'text':clean(source_text(a)),'attributes':dict(a.attrs),'url':urljoin(cfg['base'],a.get('href',''))} for a in body.find_all('a')],'notes':notes,'omitted_null_metadata':omitted,'omitted_hidden_sort_keys':hidden_sort_keys,'mini_toc_disposition':'Removed from legal text; retained in owned source HTML as navigation','list_count':len(body.find_all(['ol','ul'])),'inventory_origin':'toc' if ident in known else 'embedded_source_section','source_url':cfg['base']+'doc-view.aspx?secid='+ident+'&ajax=0'})
  if reference_dispositions:records[-1]['qualified_reference_dispositions']=reference_dispositions
 return records

def outputs(records):
 records=sorted(records,key=lambda r:int(r['id']));jsonl=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records).encode();buf=io.StringIO(newline='');fields=['id','heading','parent_id','kind','text','source_url','body_sha256'];w=csv.DictWriter(buf,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in records)
 return {'records.jsonl':jsonl,'records.csv':buf.getvalue().encode()}
