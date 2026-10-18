"""Pure source parsers and deterministic coverage reconciliation; no network or writes."""
import copy,hashlib,json,pathlib,re,zipfile,io
from urllib.parse import urljoin,urlsplit,urlunsplit,unquote
from bs4 import BeautifulSoup
import legacy_html

def sha(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def clean(t):return re.sub(r'\s+',' ',t).strip()
def key(url):return legacy_html.doc_key(url)
def legal_image_text(value):
 # Quoted literal boundaries are source-backed. An unquoted payload may continue
 # through whitespace and ordinary prose: do not guess its end or delete text.
 quoted=re.compile(r'([\"\'])(data:image/[^\"\']*)\1',re.I|re.S)
 replaced=quoted.sub(lambda m:m.group(1)+'[IMAGE]'+m.group(1),value)
 if re.search(r'data:image/',replaced,re.I):raise ValueError('Unqualified unquoted image-data boundary in legal text; preserve original source and obtain an explicitly bounded source representation. No automatic text deletion or image decoding.')
 return replaced

def redact_image_metadata(value,attribute_boundary=False):
 def contains(v):return isinstance(v,str) and bool(re.search(r'data:image/',v,re.I))
 if isinstance(value,str):return '[IMAGE]' if contains(value) else value
 if isinstance(value,list):return [redact_image_metadata(v,attribute_boundary) for v in value]
 if isinstance(value,dict):
  result={}
  legal_keys={'text','full_text','heading','context','note','label','title','document_heading'}
  for k,v in value.items():
   if contains(v) and not attribute_boundary and k in legal_keys:result[k]=legal_image_text(v)
   else:result[k]=redact_image_metadata(v,attribute_boundary)
   if contains(v):result['data-source-image-metadata-sha256-'+sha(str(k).encode())[:12]]=sha(v.encode())
  return result
 return value
def dom_text(node):
 # Inline element boundaries do not add spaces (1<sup>st</sup>, ft<sup>3</sup>).
 # Source block/line/cell boundaries retain a whitespace separator.
 from bs4 import Tag,NavigableString,Comment,Declaration,Doctype,ProcessingInstruction
 blocks={'address','article','aside','blockquote','br','caption','dd','div','dl','dt','fieldset','figcaption','figure','footer','form','h1','h2','h3','h4','h5','h6','header','hr','li','main','nav','ol','p','pre','section','table','tbody','td','tfoot','th','thead','tr','ul'}
 def walk(el):
  if isinstance(el,(Comment,Declaration,Doctype,ProcessingInstruction)):return ''
  if isinstance(el,NavigableString):return str(el)
  if not isinstance(el,Tag) or el.name in {'script','style','template'}:return ''
  inside=''.join(walk(x) for x in el.children)
  return ' '+inside+' ' if el.name in blocks else inside
 return clean(walk(node))

def table_data(node):
 tables=node.find_all('table');output=[]
 for index,table in enumerate(tables):
  parent=table.find_parent('table');parent_index=next((i for i,t in enumerate(tables) if t is parent),None)
  output.append({'html':str(table),'parent_table_index':parent_index,'rows':[[{'text':dom_text(c),'rowspan':str(c.get('rowspan','1')),'colspan':str(c.get('colspan','1')),'tag':c.name} for c in row.find_all(['td','th'],recursive=False)] for row in table.find_all('tr') if row.find_parent('table') is table]})
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

def image_reference_attributes(attributes):
 # This helper is used only inside a known image-reference attribute boundary.
 # A misleading data MIME must not make image payload metadata safe to copy.
 result=copy.deepcopy(dict(attributes))
 for name,value in list(result.items()):
  raw=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True)
  if re.search(r"\bdata:[^\s\"']*[,;]",raw,re.I):
   result[name]='[IMAGE]';result['data-source-image-attribute-sha256-'+sha(str(name).encode())[:12]]=sha(raw.encode())
 return result

def normalized_links(node,url):
 links=[]
 for element in ([node] if node.name=='a' and node.get('href') else [])+list(node.select("a[href]")):
  target=element['href'];attributes=redact_image_metadata(element.attrs,attribute_boundary=True)
  for name in ['style','srcset','background','poster']:
   if name in element.attrs:attributes.update(image_reference_attributes({name:element[name]}))
  image_context=image_asset({'url':target,'kind':'a','source_attribute':'href','media_type':str(element.get('type','')).lower()})
  if target.lower().startswith('data:'):
   digest=sha(target.encode());target=('inline-image-ref:sha256:' if image_context else 'unqualified-inline-document-ref:sha256:')+digest
   if image_context:attributes=image_reference_attributes(element.attrs)
   else:attributes['href']=target;attributes['data-source-inline-reference-sha256']=digest
  else:target=urljoin(url,target)
  links.append({'text':dom_text(element),'url':target,'attributes':attributes})
 return redact_image_metadata(links)

def source_assets(node,url):
 output=[]
 def add(target,element,attribute,raw=None):
  if not target:return
  target=urljoin(url,target.strip());asset={'url':target,'kind':element.name,'source_id':element.get('id'),'source_attribute':attribute,'required':True,'context':dom_text(element.parent or element)[:2500],'source_descriptive_attributes':redact_image_metadata({k:element[k] for k in ['alt','title','aria-label'] if element.get(k)},attribute_boundary=True)}
  if str(element.get('type','')).lower().startswith('image/') or element.name=='input' and element.get('type','').lower()=='image':asset['media_type']='image/*' if element.name=='input' else element.get('type','image/*').lower()
  image_context=image_asset(asset) or element.find_parent('picture') is not None
  if image_context:asset['source_descriptive_attributes']=image_reference_attributes(asset['source_descriptive_attributes'])
  if raw is not None:
   asset['source_attribute_value']='[IMAGE]' if 'data:image/' in raw.lower() or image_context and re.search(r"\bdata:[^\s\"']*[,;]",raw,re.I) else raw
   asset['source_attribute_sha256']=sha(raw.encode())
  if target.lower().startswith('data:'):
   header,separator,payload=target.partition(',');declared=header[5:].split(';')[0].lower();digest=sha(target.encode())
   if image_context:
    asset.update(url='inline-image-ref:sha256:'+digest,inline_image_reference=True,media_type=declared if declared.startswith('image/') else 'image/*',source_reference_sha256=digest,encoded_characters=len(payload),status='policy_omitted_image',required=False,reason='Source context is an image: inline payload is not decoded, extracted or qualified by its claimed MIME')
    if not declared.startswith('image/'):asset['source_declared_data_media_type']=declared
   else:
    asset.update(url='unqualified-inline-document-ref:sha256:'+digest,inline_data=True,source_reference_sha256=digest,encoded_characters=len(payload),media_type=declared,status='unqualified_inline_nonimage_document',required=True,format_qualified=False,reason='Nonimage inline document format is unsupported and unresolved; encoded reference retained by hash only, no payload decoding or format qualification')
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
   explicit=re.search(r'incorporat|adopted? by reference|appendix|attachment|official map',dom_text(element.parent or element),re.I)
   if element['href'].lower().startswith('data:') or urlsplit(element['href']).path.lower().endswith(('.pdf','.svg','.png','.jpg','.jpeg','.gif','.webp','.zip','.docx')) or explicit:
    add(element['href'],element,'href')
    if explicit:output[-1].update(classification='source_explicit_incorporation_or_attachment',required=True)
  if element.get('background'):add(element['background'],element,'background')
  if element.get('srcset'):
   raw=element['srcset']
   if 'data:' in raw.lower():add('unparsed-srcset:'+sha(raw.encode()),element,'srcset',raw);output[-1].update(requires_manual_review=True,status='unresolved')
   else:
    for candidate in raw.split(','):
     parts=candidate.strip().split()
     if parts:add(parts[0],element,'srcset',raw)
  css=element.get('style','')+(' '+element.get_text() if element.name=='style' else '')
  for match in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)",css,re.I|re.S):add(match[2],element,'css-url',css)
 return redact_image_metadata(output)

def image_asset(asset):
 if asset.get('kind') in ['img','picture','image','use','svg']:return True
 if asset.get('source_attribute') in ['poster','srcset','css-url','background']:return True
 if asset.get('media_type','').lower().startswith('image/') or asset.get('url','').lower().startswith('data:image/'):return True
 return bool(re.search(r'\.(?:svg|png|jpe?g|gif|webp|avif|bmp|tiff?)(?:$|[?#])',asset.get('url',''),re.I))

def sanitize_images(node):
 from bs4 import NavigableString
 clone=BeautifulSoup(str(node),'html.parser')
 # Replace outer picture/SVG once, preserving original source identifiers in a metadata span.
 for tag in list(clone.select('picture,svg,img,source')):
  if tag.parent is None:continue
  if tag.name=='source' and not (tag.get('srcset') or str(tag.get('src','')).lower().startswith('data:image/') or str(tag.get('type','')).lower().startswith('image/') or image_asset({'url':tag.get('src',''),'kind':'source'})):continue
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
 for element in clone.find_all(True):
  for attribute in ['href','src','data']:
   if str(element.get(attribute,'')).lower().startswith('data:'):
    digest=sha(element[attribute].encode());element[attribute]='unqualified-inline-document-ref:sha256:'+digest;element['data-source-inline-reference-sha256-'+attribute]=digest
 for el in clone.find_all(True):
  el.attrs=redact_image_metadata(el.attrs,attribute_boundary=True)
 for text in list(clone.find_all(string=True)):
  if 'data:image/' in str(text).lower():text.replace_with(NavigableString(legal_image_text(str(text))))
 return clone

def source_notes(node):
 # Preserve each source note occurrence once; include a note that IS the owned block.
 classes={'Footnote','footnote','HistoryNote','Note','TableFootnote','CellBodyNote','CellBodyFootnote'}
 selector='aside.annotations,[role="note"],'+','.join('.'+x for x in sorted(classes))
 root_note=bool(set(node.get('class',[]))&classes or node.get('role')=='note' or node.name=='aside' and 'annotations' in node.get('class',[]))
 selected=([node] if root_note else [])+list(node.select(selector));seen=set();result=[]
 for note in selected:
  if id(note) in seen:continue
  seen.add(id(note));result.append(str(sanitize_images(note)))
 return result

def semantics(node,url):
 refs=source_assets(node,url)
 for asset in refs:
  if image_asset(asset):asset.update(required=False,status='policy_omitted_image',classification='user_requested_image_omission',placeholder='[IMAGE]',reason='User explicitly requests no image acquisition and literal[IMAGE] replacement; reference/IDs retained, no pixels extracted')
 clean_node=sanitize_images(node)
 return {'html':str(clean_node),'text':dom_text(clean_node),'tables':table_data(clean_node),'links':normalized_links(node,url),'assets':refs,'image_placeholder_count':clean_node.get_text().count('[IMAGE]'),'notes':source_notes(node),'superscripts':[str(x) for x in clean_node.select('sup,sub')]}

