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
def asset_refs(html,base,owner):
 s=BeautifulSoup(html,'html.parser');out={}
 def add(href,kind):
  if not href or href.startswith('#'):return
  u=urljoin(base,href);original_kind=kind
  if u.startswith('data:'):kind='embedded_data'
  elif urlsplit(u).scheme not in ['http','https']:kind='unsupported_asset'
  else:u=u.split('#')[0]
  image=original_kind in ['img_asset','picture_asset','image_asset','use_asset','svg_asset','srcset','css_asset','poster_asset'] or bool(re.search(r'\.(?:png|jpe?g|gif|svg|webp|avif|bmp|ico|tiff?)(?:[?#]|$)',u,re.I)) or u.startswith('data:image/')
  if image and 'data:image/' in u:u='image-data-sha256:'+digest(u.encode())
  out[u]={'url':u,'owner_id':owner,'required':not image,'image':image,'kind':kind,'policy':'literal [IMAGE]; intentionally not acquired' if image else 'required nonimage asset'}
 for el in s.find_all(True):
  name=el.name.lower()
  for attr in ['src','poster','data','xlink:href']:
   if el.get(attr) and (attr!='data' or name=='object'):add(el[attr],'poster_asset' if attr=='poster' else name+'_asset')
  if name in ['image','use'] and el.get('href'):add(el['href'],'svg_asset')
  if el.get('srcset'):
   # A data URI srcset cannot be safely split on commas; retain an unresolved required ref.
   if 'data:' in el['srcset']:add('image-srcset:'+el['srcset'],'srcset')
   else:
    for part in el['srcset'].split(','):add(part.strip().split()[0],'srcset')
  if name=='a' and el.get('href'):
   u=el['href']
   if re.search(r'(?:^|[/_-])(attachment|download|document|exhibit|media)(?:[/_?=-]|$)',u,re.I) or re.search(r'\b(download|attachment|exhibit|figure|map)\b',el.get_text(' ',strip=True),re.I) or re.search(r'\.(pdf|docx?|xlsx?|csv|zip|tiff?|png|jpe?g|gif|svg)(?:[?#]|$)',u,re.I):add(u,'attachment')
  for css in [el.get('style',''),el.get_text() if name=='style' else '']:
   for m in re.finditer(r'url\(\s*[\"\']?([^\)\"\']+)',css,re.I):add(m.group(1).strip(),'css_asset')
 return list(out.values())

def has_owned_visual(html):
 s=BeautifulSoup(html,'html.parser');return bool(s.select_one('img,svg,object,embed,iframe,video,audio,canvas,picture') or any(el.get('style') and 'url(' in el['style'] for el in s.find_all(True)))

def strip_processing(s):
 for n in list(s.descendants):
  if isinstance(n,(ProcessingInstruction,Comment,Declaration)):n.extract()
 return s

def normalized_images(html):
 s=strip_processing(BeautifulSoup(html,'html.parser'))
 # Keep publisher raw intact separately. Normalized rows never embed or request image bytes.
 for el in list(s.find_all(['img','picture','svg','image','canvas','source'])):
  if el.parent is not None and (el.name!='source' or el.get('srcset') or el.get('type','').startswith('image/')):el.replace_with(NavigableString('[IMAGE]'))
 for el in list(s.find_all(['object','embed'])):
  u=el.get('data') or el.get('src') or '';typ=el.get('type','')
  if typ.startswith('image/') or u.startswith('data:image/') or re.search(r'\.(png|jpe?g|gif|svg|webp|avif|tiff?)(?:[?#]|$)',u,re.I):el.replace_with(NavigableString('[IMAGE]'))
 for el in list(s.find_all(True)):
  if el.get('poster'):el.attrs.pop('poster',None);el.insert(0,NavigableString('[IMAGE]'))
  if el.get('style') and re.search(r'url\(',el['style'],re.I):
   count=len(re.findall(r'url\(',el['style'],re.I));el['style']=re.sub(r'url\([^)]*\)','none',el['style'],flags=re.I);el.insert(0,NavigableString(' '.join(['[IMAGE]']*count)))
  if el.name=='style' and re.search(r'url\(',el.get_text(),re.I):el.replace_with(NavigableString(' '.join(['[IMAGE]']*len(re.findall(r'url\(',el.get_text(),re.I)))))
 return s

def image_occurrences(html,owner):
 s=BeautifulSoup(html,'html.parser');items=[]
 for el in s.find_all(True):
  parent_image=el.find_parent(['picture','svg'])
  visual=(el.name in ['img','picture','svg','image','canvas'] or (el.name=='source' and bool(el.get('srcset') or el.get('type','').startswith('image/')))) and not parent_image
  if el.name in ['object','embed']:
   u=el.get('data') or el.get('src') or '';visual=el.get('type','').startswith('image/') or u.startswith('data:image/') or bool(re.search(r'\.(png|jpe?g|gif|svg|webp|avif|tiff?)(?:[?#]|$)',u,re.I))
  count=(1 if visual else 0)+(1 if el.get('poster') else 0)+len(re.findall(r'url\(',el.get('style',''),re.I))+(len(re.findall(r'url\(',el.get_text(),re.I)) if el.name=='style' else 0)
  for _ in range(count):items.append({'owner_id':owner,'ordinal':len(items)+1,'source_tag':el.name,'source_id':el.get('id'),'source_attributes':{k:('image-data-sha256:'+digest(str(v).encode()) if 'data:image/' in str(v) else v) for k,v in el.attrs.items()},'policy':'literal [IMAGE]; no image bytes acquired'})
 return items

def substantive(html):
 s=strip_processing(BeautifulSoup(html,'html.parser'))
 for h in s.select('header,h1,h2,h3,h4,h5,h6,script,style'):h.decompose()
 return bool(s.get_text(' ',strip=True) or has_owned_visual(str(s)))

def link_refs(html,base,owner):
 s=BeautifulSoup(html,'html.parser');return [{'url':('image-data-sha256:'+digest(a['href'].encode()) if 'data:image/' in a['href'] else urljoin(base,a['href'])),'label':a.get_text(' ',strip=True),'owner_id':owner} for a in s.select('a[href]') if a['href']]

def _record(nid,label,kind,body,url,parent=None):
 # Own body only. Nested independently identified content is never counted twice.
 clone=BeautifulSoup(str(body),'html.parser')
 for child in clone.select('.content .content,article article'):child.decompose()
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
 for body in code.select('[id$="_content"].content'):
  nid=body['id'][:-8];header=s.select_one('#childContent .contentTitle[data-guid="'+nid+'"]') or s.select_one('[id="'+nid+'_title"]');label=header.get('data-full-title') if header else None;kind=header.get('data-code-content-type') if header else None
  if not label and nid==pageid:label=s.select_one('#pageTitle').get_text(' ',strip=True) if s.select_one('#pageTitle') else s.body.get('data-page-string');kind=by.get(nid,{}).get('kind','container')
  if not label:raise QualificationError('Owned content lacks matching heading '+nid)
  rec=_record(nid,label,kind or 'container',body,'https://ecode360.com/'+nid,(header.get('data-parent-guid') if header else None) or (pageid if nid!=pageid else None));owned.add(nid)
  if substantive(rec['content_html']):records.append(rec);dispositions.append({'id':nid,'classification':'owned_content','evidence':'exact '+nid+'_content and own heading'})
  elif re.search('reserved|repealed',label,re.I):dispositions.append({'id':nid,'classification':'reserved_or_repealed_empty','evidence':label})
  elif (kind or '').lower() in KNOWN_STRUCTURAL:dispositions.append({'id':nid,'classification':'structural_empty','evidence':'Exact own empty content body'})
  else:dispositions.append({'id':nid,'classification':'unresolved_empty','evidence':'Empty operative or unknown type not marked reserved/repealed'})
  if nid not in by:nodes.append({'id':nid,'url':'https://ecode360.com/'+nid,'heading':label,'kind':kind,'observed_on':url})
 # Every legal body and note must have an owner, even on pages that own history.
 own=strip_processing(BeautifulSoup(str(code),'html.parser'))
 for el in own.select('#toc,#displayDate,.content,.contentTitle,button,input,.actions,.selection-control'):el.decompose()
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
  elif re.search('reserved|repealed',label,re.I):cl='reserved_or_repealed_empty'
  elif kind.lower() in KNOWN_STRUCTURAL:cl='structural_empty'
  else:cl='unresolved_empty'
  dispositions.append({'id':rid,'classification':cl,'evidence':'Exact typed article own heading/body; descendants removed'})
 if not nodes and clean_url(url)!=clean_url(base):raise QualificationError('No typed legal articles in publication export')
 remainder=copy.deepcopy(main)
 for el in remainder.select('article,nav,.toc,.tocHeading,script,header h1,header h2,header h3,header h4,header h5,header h6'):el.decompose()
 strip_processing(remainder)
 if remainder.get_text(' ',strip=True) or has_owned_visual(str(remainder)) or asset_refs(str(remainder),url,base):raise QualificationError('Unowned publication text/visual outside typed legal articles: '+remainder.get_text(' ',strip=True)[:180])
 if clean_url(url)!=clean_url(base) and clean_url(url) not in {n['id'] for n in nodes}:raise QualificationError('Requested municipal node is absent from returned content')
 return {'nodes':nodes,'records':records,'dispositions':dispositions,'identity':got}
