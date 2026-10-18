"""Source-derived inventory and one-owner-per-node content for two ICC HTML families."""
from __future__ import annotations
import copy,json,re
from urllib.parse import urljoin,urlsplit,urlunsplit,unquote
from bs4 import BeautifulSoup,ProcessingInstruction,Comment,Declaration,NavigableString
from .common import *
from . import legacy_ecode as ec
from . import legacy_municipal as mc

def clean_url(u):
 p=urlsplit(u);return urlunsplit((p.scheme,p.netloc,p.path.rstrip('/') or '/','',''))
def family_of(url):
 h=urlsplit(url).hostname or ''
 if h=='ecode360.com':return 'ecode360'
 if h.endswith('.municipal.codes'):return 'municipal.codes'
 raise QualificationError('Unsupported publisher hostname')
def same_publication(url,base):
 a,b=urlsplit(url),urlsplit(base);p=unquote(a.path).rstrip('/');q=unquote(b.path).rstrip('/')
 return a.scheme=='https' and a.netloc==b.netloc and (p==q or p.startswith(q+'/')) and not a.query

def soup(raw):
 s=BeautifulSoup(raw,'html.parser');ec.reject_shell(s)
 if not s.body:raise QualificationError('No body')
 return s

def identity(raw,url,family,base=None):
 s=soup(raw)
 if family=='ecode360':
  i=ec.page_identity(s);customer=json.loads(s.body.get('data-customer','{}'));return {'family':family,**i,'name':s.body.get('data-customer-name') or customer.get('name'),'state':customer.get('state'),'current_code_id':s.body.get('data-current-code-id',i['code_id'])}
 labels=[el['data-disclaimer'] for el in s.select('[data-disclaimer]') if 'current through' in el['data-disclaimer']]
 for p in s.select('p'):
  t=p.get_text(' ',strip=True)
  if re.match(r'^(?:The )?.{0,100}(?:Code|Charter|Ordinance|code|charter).{0,30}(?:current|updated) through',t):labels.append(t)
 if not labels:
  for el in s.select('footer,aside,.disclaimer'):
   for t in el.stripped_strings:
    if 'current through' in t:labels.append(t)
 if not labels:raise QualificationError('Municipal publication currency label not found; edition unpinned')
 return {'family':family,'publication_base':clean_url(base or url),'currency_raw':sorted(set(labels)),'name':s.title.get_text(' ',strip=True) if s.title else '', 'state':None}

def edition(i):return {k:v for k,v in i.items() if k not in ['name','state']}
def jurisdiction_check(i,jurisdiction=None,state=None):
 if jurisdiction:
  wanted=re.sub('[^a-z0-9]','',jurisdiction.lower());name=re.sub('[^a-z0-9]','',(i.get('name') or '').lower());tokens=[t for t in re.findall('[a-z]+',jurisdiction.lower()) if t not in ['city','of','municipality','county','the']]
  if wanted not in name and not all(t in name for t in tokens):raise QualificationError('Jurisdiction label mismatch')
 if state and i.get('state') and state.upper()!=i['state'].upper():raise QualificationError('State mismatch')

def municipal_publications(raw,url):
 s=soup(raw);out={};host=urlsplit(url).netloc
 for el in s.select('[data-scope][data-source],main a[href],.sitenavbar a[href]'):
  if el.has_attr('data-scope') and el.get('data-scope') not in ['all','selections']:
   scope=el['data-scope'];out['https://'+host+'/'+scope]={'title':scope,'url':'https://'+host+'/'+scope,'evidence':'observed publication data-scope'}
  elif el.get('href'):
   u=urljoin(url,el['href']);p=urlsplit(u)
   if p.netloc==host and re.fullmatch('/[A-Za-z][A-Za-z0-9_-]*',p.path) and p.path.strip('/') not in ['contents','settings','help','enactments','updates','search','selections']:
    out[clean_url(u)]={'title':el.get_text(' ',strip=True),'url':clean_url(u),'evidence':'observed publication anchor'}
 return list(out.values())

def ecode_inventory(raw,url):
 s=soup(raw);nodes={};root=str(s.body.get('data-guid') or s.body.get('data-cust-id'))
 nodes[root]={'id':root,'url':clean_url(url),'heading':s.select_one('#pageTitle').get_text(' ',strip=True) if s.select_one('#pageTitle') else s.title.get_text(' ',strip=True),'kind':'publication' if not root.isdigit() else 'container','observed_on':clean_url(url)}
 for el in s.select('#toc .contentTitle[data-guid]'):
  nid=str(el['data-guid']);a=el.select_one('a.titleLink[href]');heading=el.get('data-full-title') or el.get_text(' ',strip=True)
  if not a:raise QualificationError('TOC node lacks source URL '+nid)
  u=urljoin(url,a['href']);path=urlsplit(u).path.rstrip('/').split('/')[-1]
  if path!=nid:
   if urlsplit(u).fragment==nid:u='https://ecode360.com/'+nid
   else:raise QualificationError('TOC ID/URL mismatch '+nid)
  descriptor={'id':nid,'url':clean_url(u),'heading':heading,'kind':el.get('data-code-content-type','unclassified'),'parent_id':el.get('data-parent-guid'),'observed_on':clean_url(url)}
  if nid in nodes and nodes[nid]['url']!=descriptor['url']:raise QualificationError('Conflicting TOC URL')
  nodes[nid]=descriptor
 return root,list(nodes.values())

def municipal_inventory(raw,url,base):
 s=soup(raw);main=s.select_one('main')
 if not main:raise QualificationError('No independent contents main')
 pending=main.select('[data-lazy]')
 if pending:raise QualificationError('Contents has unresolved/lazy controls; unsupported inventory cannot be complete')
 nodes={clean_url(base):{'id':clean_url(base),'url':clean_url(base),'heading':s.title.get_text(' ',strip=True) if s.title else base,'kind':'publication','observed_on':url}}
 for a in main.select('a[href]'):
  u=clean_url(urljoin(url,a['href']));original=urlsplit(urljoin(url,a['href']))
  if original.query or original.fragment or not same_publication(u,base) or u.endswith('/contents') or re.search('/(?:share|history|search|versions)$',u):continue
  if u==clean_url(base):continue
  nodes[u]={'id':u,'url':u,'heading':a.get_text(' ',strip=True),'kind':'toc_node','observed_on':url,'parent_id':None}
  li=a.find_parent('li');parent=li.find_parent('li') if li else None
  if parent:
   pa=parent.find('a',recursive=False)
   if pa:nodes[u]['parent_id']=clean_url(urljoin(url,pa['href']))
  if li:nodes[u]['source_classes']=li.get('class',[])
 if len(nodes)<2:raise QualificationError('Contents inventory empty')
 return list(nodes.values())

KNOWN_STRUCTURAL={'publication','container','chapter','article','title','subtitle','part','subpart','division','subdivision','subchapter','appendix','backappendices','book','charter','code'}
KNOWN_OPERATIVE={'section','appendixsection','chartersection','councilrule'}
def image_source(el):
 u=el.get('src','')
 return el.name=='source' and bool(el.find_parent('picture') or el.get('srcset') or el.get('type','').lower().startswith('image/') or u.lower().startswith('data:image/') or re.search(r'\.(png|jpe?g|gif|svg|webp|avif|bmp|ico|tiff?)(?:[?#]|$)',u,re.I))
def image_anchor(el):
 return el.get('type','').lower().startswith('image/') or el.get('href','').lower().startswith('data:image/') or bool(re.search(r'\.(png|jpe?g|gif|svg|webp|avif|tiff?)(?:[?#]|$)',el.get('href',''),re.I))
def image_attribute(name,value):
 # A known image locator remains image data even if its URI declares another
 # MIME type. Hash the complete bounded attribute; preserve captions/prose.
 text=str(value)
 if 'data:image/' in text.lower() or (name in {'src','srcset','href','xlink:href','data','style','background','poster'} and re.search(r'data\s*:',text,re.I)):
  return 'image-data-sha256:'+digest(text.encode())
 return value
def owned_definition_reference(el,s,base,owner):
 # Only a publisher definition's own inert term anchor inside this exact body.
 if urlsplit(base).netloc!='ecode360.com' or not str(owner).isdigit():return None
 roots=s.select('[id="'+str(owner)+'_content"].content')
 if len(roots)!=1 or roots[0] not in el.parents:return None
 if 'termLink' not in el.get('class',[]) or not re.fullmatch(r'\s*return\s+false\s*;?\s*',el.get('onclick','')):return None
 if el.get('type','').strip().lower() not in ['', 'text/html']:return None
 parent=el.parent
 if parent.name!='dfn' or 'term' not in parent.get('class',[]):return None
 definition=el.find_parent('section',class_='definition')
 if not definition or definition.get('id') is None:return None
 target=definition['id'];parts=urlsplit(urljoin(base,el['href']))
 if not target.isdigit() or parts.scheme!='https' or parts.netloc!='ecode360.com' or parts.path!='/'+target or parts.query or parts.fragment!=target:return None
 if len(roots[0].find_all(id=target))!=1:return None
 nearest=definition.find_parent(lambda p:'content' in p.get('class',[]) and bool(re.fullmatch(r'[0-9]+_content',p.get('id',''))))
 if nearest is not roots[0]:return None
 text=definition.select_one('.deftext')
 if text is None or not text.get_text(' ',strip=True):return None
 return {'owner_id':str(owner),'definition_id':target,'body_root_id':str(owner)+'_content','source_href':el['href'],'resolved_href':urljoin(base,el['href']),'definition_html_sha256':digest(str(definition).encode()),'definition_text_sha256':digest(text.get_text(' ',strip=True).encode()),'basis':'Unique typed definition target, exact inert own term anchor and substantive definition body already retained by this owner'}

def asset_refs(html,base,owner):
 s=BeautifulSoup(html,'html.parser');out={}
 def add(href,kind):
  if not href or href.startswith('#'):return
  u=urljoin(base,href);original_kind=kind
  if u.startswith('data:'):kind='embedded_data'
  elif urlsplit(u).scheme not in ['http','https']:kind='unsupported_asset'
  else:u=u.split('#')[0]
  image=original_kind in ['img_asset','picture_asset','image_asset','use_asset','svg_asset','srcset','css_asset','poster_asset','background_asset'] or bool(re.search(r'\.(?:png|jpe?g|gif|svg|webp|avif|bmp|ico|tiff?)(?:[?#]|$)',u,re.I)) or u.lower().startswith('data:image/')
  if image and re.search(r'data\s*:',u,re.I):u='image-data-sha256:'+digest(u.encode())
  out[u]={'url':u,'owner_id':owner,'required':not image,'image':image,'kind':kind,'policy':'literal [IMAGE]; intentionally not acquired' if image else 'required nonimage asset'}
 for el in s.find_all(True):
  name=el.name.lower()
  for attr in ['src','poster','background','data','xlink:href']:
   if el.get(attr) and (attr!='data' or name=='object'):add(el[attr],'image_asset' if (name in ['object','embed'] and el.get('type','').lower().startswith('image/')) or image_source(el) else (attr+'_asset' if attr in ['poster','background'] else name+'_asset'))
  if name in ['image','use'] and el.get('href'):add(el['href'],'svg_asset')
  if el.get('srcset'):
   # A data URI srcset cannot be safely split on commas; retain an unresolved required ref.
   if 'data:' in el['srcset'].lower():add('image-srcset:'+el['srcset'],'srcset')
   else:
    for part in el['srcset'].split(','):add(part.strip().split()[0],'srcset')
  if name=='a' and el.get('href'):
   u=el['href']
   if el.get('type','').lower().startswith('image/'):add(u,'image_asset')
   elif re.search(r'(?:^|[/_-])(attachment|download|document|exhibit|media)(?:[/_?=-]|$)',u,re.I) or re.search(r'\b(download|attachment|exhibit|figure|map)\b',el.get_text(' ',strip=True),re.I) or re.search(r'\.(pdf|docx?|xlsx?|csv|zip|tiff?|png|jpe?g|gif|svg)(?:[?#]|$)',u,re.I):
    proof=owned_definition_reference(el,s,base,owner)
    if proof:
     key=clean_url(proof['resolved_href'])
     if not out.get(key,{}).get('required'):out[key]={'url':key,'owner_id':str(owner),'required':False,'image':False,'kind':'owned_definition_self_anchor','policy':'Already retained own definition; no separate document acquisition','source_target':proof}
    else:add(u,'attachment')
  for css in [el.get('style',''),el.get_text() if name=='style' else '']:
   for m in re.finditer(r'url\(\s*[\"\']?([^\)\"\']+)',css,re.I):add(m.group(1).strip(),'css_asset')
 return list(out.values())

def has_owned_visual(html):
 s=BeautifulSoup(html,'html.parser');return bool(s.select_one('img,svg,object,embed,iframe,video,audio,canvas,picture,[background]') or any(image_source(el) or (el.get('style') and 'url(' in el['style'].lower()) for el in s.find_all(True)))

def strip_processing(s):
 for n in list(s.descendants):
  if isinstance(n,(ProcessingInstruction,Comment,Declaration)):n.extract()
 return s

def normalized_images(html):
 s=strip_processing(BeautifulSoup(html,'html.parser'))
 # Keep publisher raw intact separately. Normalized rows never embed or request image bytes.
 for el in list(s.find_all(['img','picture','svg','image','canvas','source'])):
  if el.parent is not None and (el.name!='source' or image_source(el)):el.replace_with(NavigableString('[IMAGE]'))
 for el in list(s.find_all(['object','embed'])):
  u=el.get('data') or el.get('src') or '';typ=el.get('type','')
  if typ.lower().startswith('image/') or u.lower().startswith('data:image/') or re.search(r'\.(png|jpe?g|gif|svg|webp|avif|tiff?)(?:[?#]|$)',u,re.I):el.replace_with(NavigableString('[IMAGE]'))
 for a in s.select('a[href]'):
  if image_anchor(a):
   a['href']='#image-omitted'
   a.append(NavigableString('[IMAGE]'))
 for el in list(s.find_all(True)):
  if el.get('background'):el.attrs.pop('background',None);el.insert(0,NavigableString('[IMAGE]'))
  if el.get('poster'):el.attrs.pop('poster',None);el.insert(0,NavigableString('[IMAGE]'))
  if el.get('style') and re.search(r'url\(',el['style'],re.I):
   count=len(re.findall(r'url\(',el['style'],re.I));el['style']=re.sub(r'url\([^)]*\)','none',el['style'],flags=re.I);el.insert(0,NavigableString(' '.join(['[IMAGE]']*count)))
  if el.name=='style' and re.search(r'url\(',el.get_text(),re.I):el.replace_with(NavigableString(' '.join(['[IMAGE]']*len(re.findall(r'url\(',el.get_text(),re.I)))))
 # Nonvisual attributes can also contain wrapped image data. Hash the complete
 # bounded attribute instead of retaining continuation bytes after whitespace.
 # Visible source text and unrelated attributes remain unchanged.
 for el in s.find_all(True):
  for name,value in list(el.attrs.items()):
   if 'data:image/' in str(value).lower():
    el.attrs[name]='[IMAGE] image-data-sha256:'+digest(str(value).encode())
 return s

def image_occurrences(html,owner):
 s=BeautifulSoup(html,'html.parser');items=[]
 for el in s.find_all(True):
  parent_image=el.find_parent(['picture','svg'])
  visual=(el.name in ['img','picture','svg','image','canvas'] or image_source(el)) and not parent_image
  if el.name in ['object','embed']:
   u=el.get('data') or el.get('src') or '';visual=el.get('type','').lower().startswith('image/') or u.lower().startswith('data:image/') or bool(re.search(r'\.(png|jpe?g|gif|svg|webp|avif|tiff?)(?:[?#]|$)',u,re.I))
  if el.name=='a' and el.get('href'):visual=image_anchor(el)
  count=(1 if visual else 0)+(1 if el.get('poster') else 0)+(1 if el.get('background') else 0)+len(re.findall(r'url\(',el.get('style',''),re.I))+(len(re.findall(r'url\(',el.get_text(),re.I)) if el.name=='style' else 0)
  for _ in range(count):items.append({'owner_id':owner,'ordinal':len(items)+1,'source_tag':el.name,'source_id':el.get('id'),'source_attributes':{k:image_attribute(k,v) for k,v in el.attrs.items()},'policy':'literal [IMAGE]; no image bytes acquired'})
 return items

def substantive(html):
 s=strip_processing(BeautifulSoup(html,'html.parser'))
 for h in s.select('header,h1,h2,h3,h4,h5,h6,script,style,object,embed,iframe,video,audio'):h.decompose()
 for a in s.select('a[href]'):
  if re.search(r'\.(pdf|docx?|xlsx?|zip)(?:[?#]|$)',a['href'],re.I):a.decompose()
 return bool(s.get_text(' ',strip=True))

def new_statutory_link_evidence(anchor,base,owner):
 """Exact source provenance for newly observed forwarding forms; no acquisition."""
 u=urljoin(base,anchor['href'])
 if anchor.find_parent(['svg','picture']):return None
 if 'statref' not in anchor.get('class',[]) or not re.fullmatch(r'https://municipal\.codes/(?:NY/(?:ABC|COR|MHY|STF|PBL|NPC|RPP|HAY)/[A-Za-z0-9.-]+|US/USC/[0-9]+)',u):return None
 context=anchor.find_parent(['p','li','dd','td','div']) or anchor.parent
 return {'schema':'source-statref-context-1','source_owner_id':str(owner),'source_classes':anchor.get('class',[]),'source_anchor_html_sha256':digest(str(anchor).encode()),'source_context_html_sha256':digest(str(context).encode()),'source_context_text':normalized_images(str(context)).get_text(' ',strip=True),'anchor_has_download':anchor.has_attr('download'),'anchor_has_nonempty_mime':bool(anchor.get('type','').strip()),'source_url':u,'source_label':anchor.get_text(' ',strip=True),'scope':'External citation witness only; referenced law not acquired or certified'}

def link_refs(html,base,owner):
 s=BeautifulSoup(html,'html.parser');out=[]
 for a in s.select('a[href]'):
  if not a['href']:continue
  link={'url':('image-data-sha256:'+digest(a['href'].encode()) if 'data:image/' in a['href'].lower() or (image_anchor(a) and re.search(r'data\s*:',a['href'],re.I)) else urljoin(base,a['href'])),'label':a.get_text(' ',strip=True),'owner_id':owner}
  evidence=new_statutory_link_evidence(a,base,owner)
  if evidence:link['source_statutory_evidence']=evidence
  out.append(link)
 return out

def _record(nid,label,kind,body,url,parent=None,independent_owners=None):
 # Own body only. Nested independently identified content is never counted twice.
 clone=BeautifulSoup(str(body),'html.parser')
 for child in list(clone.select('.content[id]')):
  if child.parent is None:continue
  target=child.get('id','')
  if target==str(nid)+'_content':continue
  if re.fullmatch(r'[0-9]+_content',target) and target[:-8] in (independent_owners or set()):child.decompose()
 for ui in clone.select('script,button,input,.actions,.selection-control'):ui.decompose()
 for a in clone.select('a[href^="#"]'):a['href']='https://ecode360.com/'+str(nid)+a['href']
 original=str(clone);refs=asset_refs(original,url,str(nid));occurrences=image_occurrences(original,str(nid));links=link_refs(original,url,str(nid));clone=normalized_images(original);serial=ec.serialize(clone,url);html=str(clone);text=serial['full_text']
 return {'id':str(nid),'heading':label,'kind':kind,'parent_id':parent,'source_url':url,'content_html':html,'text':text,'semantic_html':serial['semantic_html'],'tables_html':[str(t) for t in clone.select('table')],'notes_html':[str(n) for n in clone.select('.history,.footnote,.footnotes,.note')],'assets':refs,'links':links,'image_references':occurrences,'image_placeholder_count':len(occurrences),'body_sha256':digest(canon({'heading':label,'html':serial['semantic_html']}))}

def parse_ecode(raw,url,expected):
 s=soup(raw);got=identity(raw,url,'ecode360')
 if edition(got)!=edition(expected):raise QualificationError('Edition/customer drift')
 pageid=str(s.body.get('data-guid') or s.body.get('data-cust-id'))
 if urlsplit(url).path.strip('/').isdigit() and pageid!=urlsplit(url).path.strip('/'):raise QualificationError('Requested node/body GUID mismatch')
 root,nodes=ecode_inventory(raw,url);by={n['id']:n for n in nodes};records=[];dispositions=[];owned=set()
 code=s.select_one('#codeContent')
 if not code:raise QualificationError('No legal codeContent')
 bodies=code.select('[id$="_content"].content');independent_owners={b['id'][:-8] for b in bodies if re.fullmatch(r'[0-9]+_content',b['id'])}
 for body in bodies:
  nid=body['id'][:-8];header=s.select_one('#childContent .contentTitle[data-guid="'+nid+'"]') or s.select_one('[id="'+nid+'_title"]');label=header.get('data-full-title') if header else None;kind=header.get('data-code-content-type') if header else None
  if not kind:
   body_kind=next((c[:-8] for c in body.get('class',[]) if c.endswith('_content')),None);kind=body_kind
  if not label and nid==pageid:label=s.select_one('#pageTitle').get_text(' ',strip=True) if s.select_one('#pageTitle') else s.body.get('data-page-string');kind=kind or by.get(nid,{}).get('kind','container')
  if not label:raise QualificationError('Owned content lacks matching heading '+nid)
  rec=_record(nid,label,kind or 'container',body,'https://ecode360.com/'+nid,(header.get('data-parent-guid') if header else None) or (pageid if nid!=pageid else None),independent_owners);owned.add(nid)
  if substantive(rec['content_html']):records.append(rec);dispositions.append({'id':nid,'classification':'owned_content','evidence':'exact '+nid+'_content and own heading'})
  elif has_owned_visual(rec['content_html']) or any(a['required'] for a in rec['assets']):records.append(rec);dispositions.append({'id':nid,'classification':'unresolved_nontext_document','evidence':'Own body has only nonimage embed/document; original bytes are separate from normalized primary text'})
  elif re.search('reserved|repealed',label,re.I):dispositions.append({'id':nid,'classification':'reserved_or_repealed_empty','evidence':label})
  elif (kind or '').lower() in KNOWN_STRUCTURAL:dispositions.append({'id':nid,'classification':'structural_empty','evidence':'Exact own empty content body'})
  else:dispositions.append({'id':nid,'classification':'unresolved_empty','evidence':'Empty operative or unknown type not marked reserved/repealed'})
  if nid not in by:nodes.append({'id':nid,'url':'https://ecode360.com/'+nid,'heading':label,'kind':kind,'observed_on':url})
 # Every legal body and note must have an owner, even on pages that own history.
 own=strip_processing(BeautifulSoup(str(code),'html.parser'))
 for el in list(own.select('.content[id]')):
  if el.parent is None:continue
  target=el.get('id','')
  if el.parent is not None and re.fullmatch(r'[0-9]+_content',target) and target[:-8] in owned:el.decompose()
 if own.select_one('.content'):raise QualificationError('Unowned legal content container outside exact independently owned GUID bodies')
 for el in own.select('#toc,#displayDate,.contentTitle,button,input,.actions,.selection-control'):el.decompose()
 if own.get_text(' ',strip=True) or has_owned_visual(str(own)) or asset_refs(str(own),url,pageid):raise QualificationError('Unowned legal/notes/visual content requires profiling: '+own.get_text(' ',strip=True)[:180])
 if pageid not in owned:
  label=by.get(pageid,{}).get('heading','')
  classification='reserved_or_repealed_empty' if re.search('reserved|repealed',label,re.I) else ('structural_empty' if len(nodes)>1 or not pageid.isdigit() else 'unresolved_empty')
  dispositions.append({'id':pageid,'classification':classification,'evidence':'No own content; exact retained page structure/heading'})
 return {'nodes':nodes,'records':records,'dispositions':dispositions,'page_id':pageid,'identity':got}

def parse_municipal(raw,url,base,expected,known_nodes=None):
 s=soup(raw);got=identity(raw,url,'municipal.codes',base)
 if edition(got)!=edition(expected):raise QualificationError('Municipal publication currency drift')
 main=s.select_one('main')
 if not main:raise QualificationError('No legal main')
 records=[];dispositions=[];nodes=[]
 for card in main.select('article'):
  classes=[x[5:] for x in card.get('class',[]) if x.startswith('type-')]
  if not classes:raise QualificationError('Untyped legal article')
  kind=classes[0];nid,canonical,_=mc.node_identity(card,url,base);rid=clean_url(canonical)
  if '#' in canonical:
   candidate=clean_url(base)+'/'+card['id'];rid=candidate if known_nodes and candidate in known_nodes else clean_url(base)+'#'+card['id']
  own=copy.deepcopy(card)
  for child in own.select('article'):child.decompose()
  own=mc.clean(own);header=own.select_one('header');label=header.get_text(' ',strip=True) if header else ''
  if not label:raise QualificationError('Article missing own heading '+rid)
  body=mc.clean(own,True);original=str(body);refs=asset_refs(original,url,rid);occurrences=image_occurrences(original,rid);links=link_refs(original,url,rid);body=normalized_images(original);text=mc.text(body);parent=card.find_parent('article');parenturl=None
  if parent:
   _,parenturl,_=mc.node_identity(parent,url,base)
   if '#' in parenturl:
    candidate=clean_url(base)+'/'+parent['id'];parenturl=candidate if known_nodes and candidate in known_nodes else clean_url(base)+'#'+parent['id']
   else:parenturl=clean_url(parenturl)
  rec={'id':rid,'heading':label,'kind':kind.lower(),'parent_id':parenturl or (known_nodes or {}).get(rid,{}).get('parent_id'),'source_url':rid,'text':text,'content_html':str(body),'semantic_html':str(body),'tables_html':[str(t) for t in body.select('table')],'notes_html':[str(t) for t in body.select('.note,.history,.footnote,.footnotes')],'assets':refs,'links':links,'image_references':occurrences,'image_placeholder_count':len(occurrences),'body_sha256':digest(canon({'heading':label,'html':str(body)}))}
  nodes.append({'id':rid,'url':rid,'heading':label,'kind':kind.lower(),'observed_on':url})
  if substantive(rec['content_html']):records.append(rec);cl='owned_content'
  elif has_owned_visual(rec['content_html']) or any(a['required'] for a in rec['assets']):records.append(rec);cl='unresolved_nontext_document'
  elif re.search('reserved|repealed',label,re.I):cl='reserved_or_repealed_empty'
  elif kind.lower() in KNOWN_STRUCTURAL:cl='structural_empty'
  else:cl='unresolved_empty'
  dispositions.append({'id':rid,'classification':cl,'evidence':'Exact typed article own heading/body; descendants removed'})
 if not nodes and clean_url(url)!=clean_url(base):raise QualificationError('No typed legal articles in publication export')
 remainder=copy.deepcopy(main)
 for el in remainder.select('article,nav,.toc,.tocHeading,.levelnodeactions,script,header h1,header h2,header h3,header h4,header h5,header h6'):el.decompose()
 strip_processing(remainder)
 if remainder.get_text(' ',strip=True) or has_owned_visual(str(remainder)) or asset_refs(str(remainder),url,base):raise QualificationError('Unowned publication text/visual outside typed legal articles: '+remainder.get_text(' ',strip=True)[:180])
 if clean_url(url)!=clean_url(base) and clean_url(url) not in {n['id'] for n in nodes}:raise QualificationError('Requested municipal node is absent from returned content')
 return {'nodes':nodes,'records':records,'dispositions':dispositions,'identity':got}
