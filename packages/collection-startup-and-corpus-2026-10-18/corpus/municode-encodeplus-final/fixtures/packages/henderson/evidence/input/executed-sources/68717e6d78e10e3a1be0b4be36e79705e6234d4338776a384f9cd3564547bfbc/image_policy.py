"""Deliberate image omission. Source API bytes remain original; normalized HTML is image-free."""
import re,hashlib
from html import escape
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse
POLICY='omit-images-literal-placeholder-v1'
IMAGE_EXT=re.compile(r'\.(?:png|jpe?g|gif|svg|webp|avif|tiff?|bmp|ico)(?:$|/)',re.I)
def image_url(value):
 return bool(value and (value.lower().startswith('data:image/') or IMAGE_EXT.search(urlparse(value).path)))
def image_ref(ref,base,known=()):
 t=ref['tag'];a=ref.get('attributes',{});v=ref['value'];u=urljoin(base,v)
 return t in ('img','image','picture','svg') or (t=='source' and a.get('_in_picture')) or ref['attribute']=='style-url' or image_url(v) or u in known or (t in ('object','embed') and a.get('type','').lower().startswith('image/'))
def safe_metadata(value,locator='metadata'):
 if isinstance(value,dict):return {k:safe_metadata(v,locator+'.'+str(k)) for k,v in value.items()}
 if isinstance(value,list):return [safe_metadata(v,locator+'['+str(i)+']') for i,v in enumerate(value)]
 if isinstance(value,str) and 'data:image/' in value.lower():
  match=re.search(r'data:(image/[^;,\s)]+)',value,re.I)
  return {'inline_image_omitted':True,'mime':match.group(1).lower() if match else 'image/unknown','source_locator':locator,'source_string_sha256':hashlib.sha256(value.encode()).hexdigest(),'source_string_character_count':len(value)}
 return value
class ImageFreeHTML(HTMLParser):
 def __init__(self,base,known=()):
  super().__init__(convert_charrefs=False);self.base=base;self.known=set(known);self.out=[];self.skip=[];self.omissions=[];self.in_style=False
 def mark(self,t,a,reason):
  self.omissions.append({'tag':t,'attributes':dict(a),'reason':reason});self.out.append('[IMAGE]')
 def handle_starttag(self,t,aa):
  a=dict(aa)
  if self.skip:
   if t not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.skip.append(t)
   return
  candidate=a.get('src') or a.get('data') or a.get('href') or a.get('xlink:href') or ''
  is_image=t in ('img','picture','svg','image') or (t in ('object','embed') and (a.get('type','').lower().startswith('image/') or image_url(candidate)))
  if is_image:
   self.mark(t,aa,'image element deliberately omitted')
   if t in ('picture','svg','object'):self.skip.append(t)
   return
  # Image downloads linked as anchors are replaced, while their label remains available.
  if t=='a' and (image_url(candidate) or urljoin(self.base,candidate) in self.known):
   self.mark(t,aa,'image reference deliberately omitted');aa=[(k,v) for k,v in aa if k not in ('href','xlink:href','download')]
  clean=[];attribute_markers=[]
  for k,v in aa:
   if (v and 'data:image/' in v.lower()) or k in ('background','poster') or (k in ('src','href','xlink:href','data') and (image_url(v or '') or urljoin(self.base,v or '') in self.known)):
    self.omissions.append({'tag':t,'attributes':{k:v},'reason':'image attribute deliberately omitted'});attribute_markers.append('[IMAGE]');continue
   if k=='style' and v:
    def omit(m):self.omissions.append({'tag':t,'attributes':{'style':m.group(0)},'reason':'CSS image reference deliberately omitted'});attribute_markers.append('[IMAGE]');return 'none'
    v=re.sub(r'url\([^)]*\)',omit,v,flags=re.I)
   clean.append((k,v))
  self.out.append('<'+t+''.join(' '+k+('="'+escape(v,quote=True)+'"' if v is not None else '') for k,v in clean)+'>')
  self.out.extend(attribute_markers)
  if t=='style':self.in_style=True
 def handle_startendtag(self,t,a):
  self.handle_starttag(t,a)
  if t not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.handle_endtag(t)
 def handle_endtag(self,t):
  if self.skip:
   if t in self.skip:
    while self.skip:
     if self.skip.pop()==t:break
   return
  self.out.append('</'+t+'>')
  if t=='style':self.in_style=False
 def handle_data(self,s):
  if self.skip:return
  if self.in_style:
   count=len(re.findall(r'url\([^)]*\)',s,re.I));s=re.sub(r'url\([^)]*\)','none',s,flags=re.I)
   if count:self.omissions.extend([{'tag':'style','attributes':{},'reason':'CSS image reference deliberately omitted'}]*count);self.out.append('</style>'+'[IMAGE]'*count+'<style>')
  self.out.append(s)
 def handle_entityref(self,s):
  if not self.skip:self.out.append('&'+s+';')
 def handle_charref(self,s):
  if not self.skip:self.out.append('&#'+s+';')
def sanitize(html,base,known=()):
 p=ImageFreeHTML(base,known);p.feed(html or '');p.close();return ''.join(p.out),safe_metadata(p.omissions,'image_omissions')
