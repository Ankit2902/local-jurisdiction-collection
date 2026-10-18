"""Pure source parsers and deterministic coverage reconciliation; no network or writes."""
import copy,hashlib,json,pathlib,re,zipfile,io
from urllib.parse import urljoin,urlsplit,urlunsplit,unquote
from bs4 import BeautifulSoup
import legacy_html

def sha(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def clean(t):return re.sub(r'\s+',' ',t).strip()
def key(url):return legacy_html.doc_key(url)
def redact_image_metadata(value):
 # A URI attribute/metadata field is an explicit source boundary. Whitespace can
 # occur inside image payloads: never stop at its first line or decode pixels.
 # Hash the full original field and replace that field, preserving DOM siblings,
 # captions and visible text outside it.
 def contains(v):return isinstance(v,str) and bool(re.search(r'data:image/',v,re.I))
 if isinstance(value,str):return '[IMAGE]' if contains(value) else value
 if isinstance(value,list):return [redact_image_metadata(v) for v in value]
 if isinstance(value,dict):
  result={}
  for k,v in value.items():
   result[k]=redact_image_metadata(v)
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

def source_assets(node,url):
 import base64
 output=[]
 def add(target,element,attribute,raw=None):
  if not target:return
  target=urljoin(url,target.strip());asset={'url':target,'kind':element.name,'source_id':element.get('id'),'source_attribute':attribute,'required':True,'context':dom_text(element.parent or element)[:2500]}
  if str(element.get('type','')).lower().startswith('image/') or element.name=='input' and element.get('type','').lower()=='image':asset['media_type']='image/*' if element.name=='input' else element.get('type','image/*').lower()
  if raw is not None:
   asset['source_attribute_value']='[IMAGE]' if 'data:image/' in raw.lower() else raw
   asset['source_attribute_sha256']=sha(raw.encode())
  if target.lower().startswith('data:image/'):
   header,payload=target.split(',',1);asset.update(url='inline-image-ref:sha256:'+sha(target.encode()),inline_image_reference=True,media_type=header[5:].split(';')[0].lower(),source_reference_sha256=sha(target.encode()),encoded_characters=len(payload),status='policy_omitted_image',required=False,reason='User image omission: base64 image data not decoded or extracted')
  elif target.startswith('data:'):
   try:
    header,payload=target.split(',',1);content=base64.b64decode(payload,validate=True) if ';base64' in header else unquote(payload).encode();asset.update(url='data:sha256:'+sha(content),inline_data=True,sha256=sha(content),bytes=len(content),media_type=header[5:].split(';')[0].lower(),status='retained_inline',reason='Embedded native bytes retained in source HTML; semantic image interpretation not asserted')
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
   explicit=re.search(r'incorporat|adopted? by reference|appendix|attachment|official map',dom_text(element.parent or element),re.I)
   if urlsplit(element['href']).path.lower().endswith(('.pdf','.svg','.png','.jpg','.jpeg','.gif','.webp','.zip','.docx')) or explicit:
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
  for match in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)",css,re.I):add(match[2],element,'css-url',css)
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
 return {'html':str(clean_node),'text':dom_text(clean_node),'tables':table_data(clean_node),'links':redact_image_metadata([{'text':dom_text(a),'url':('inline-image-ref:sha256:'+sha(a['href'].encode()) if a['href'].startswith('data:image/') else urljoin(url,a['href'])),'attributes':{k:('[IMAGE]' if isinstance(v,str) and 'data:image/' in v else v) for k,v in a.attrs.items()}} for a in node.select('a[href]')]),'assets':refs,'image_placeholder_count':clean_node.get_text().count('[IMAGE]'),'notes':[str(sanitize_images(a)) for a in node.select('aside.annotations,[role="note"],.Footnote,.footnote')],'superscripts':[str(x) for x in clean_node.select('sup,sub')]}

