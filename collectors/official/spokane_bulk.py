"""Source-derived Select All/View Selected workflow; never guessed section IDs."""
import copy,re
from urllib.parse import urljoin,urlsplit,parse_qs
from bs4 import BeautifulSoup,Tag,NavigableString

def clean(text):return re.sub(r'\s+',' ',text).strip()
def form(data,url,kind):
 soup=BeautifulSoup(data,'html.parser');node=soup.find('form',attrs={'name':'formSMC'})
 if node is None or node.get('method','').lower()!='post':raise ValueError('Observed Spokane View Selected POST form absent')
 target=urljoin(url,node.get('action',''))
 if urlsplit(target).scheme!='https' or urlsplit(target).hostname!=urlsplit(url).hostname or urlsplit(target).path!='/smc/':raise ValueError('Observed Spokane form target changed')
 controls=node.select('input[name="'+kind+'"]');fields=[[kind,e.get('value','')] for e in controls if not e.has_attr('disabled')];disabled=[e.get('value','') for e in controls if e.has_attr('disabled')]
 if not fields or any(not re.fullmatch(r'[0-9A-Za-z.]+',v.strip()) for _,v in fields):raise ValueError('Empty/unqualified observed Spokane selection '+kind)
 fields=[list(pair) for pair in dict.fromkeys(tuple(pair) for pair in fields)]
 labels={}
 for e in controls:
  parent=e.find_parent('tr');a=parent.find('a',href=True) if parent else None
  if parent:labels[e.get('value','').strip()]=clean(a.parent.get_text(' ',strip=True)) if a else clean(parent.get_text(' ',strip=True))
 return target,fields,disabled,labels

def acquire(run,config,fetch_raw,start,source_ref,prefix=''):
 import hashlib,collections
 current=start;current_url=config['source_url'];phases=[];paths={}
 for kind in ['Title','Chapter']:
  target,fields,disabled,labels=form(current,current_url,kind);paths[kind]=labels
  data,meta,ref=fetch_raw(run,prefix+'spokane-select-'+kind,target,{**config,'post_fields':fields},kind='html',fresh=bool(prefix));phases.append({'selection_kind':kind,'form_source_ref':source_ref,'target':target,'fields':fields,'disabled':disabled,'response_ref':ref,'post_body_sha256':meta.get('post_body_sha256')});current=data;current_url=target;source_ref=ref
 target,fields,disabled,labels=form(current,current_url,'Section');paths['Section']=labels;by_title=collections.OrderedDict();seen=set();aliases=[]
 for field in fields:
  ident=field[1].strip()
  if ident in seen:aliases.append({'source_value':field[1],'canonical_id':ident});continue
  seen.add(ident);by_title.setdefault(ident.split('.')[0],[]).append(field)
 size=config.get('source_selection_batch_size',150);items=[]
 for title,source_fields in by_title.items():
  for offset in range(0,len(source_fields),size):
   selection=source_fields[offset:offset+size];part=offset//size+1;ident=config['source_url']+'::selected:Title-'+title+'-part-'+str(part);units=[]
   if offset==0:
    units=[{'id':v.strip(),'heading':labels.get(v.strip(),''),'raw_ref':source_ref,'raw_sha256':hashlib.sha256(current).hexdigest()} for v in disabled if v.strip().split('.')[0]==title]
   items.append({'id':ident,'url':target,'kind':'html','heading':'Observed View Selected Title '+title+' batch '+str(part),'post_fields':selection,'expected_sections':[v.strip() for _,v in selection],'heading_labels':{'Title':paths['Title'],'Chapter':paths['Chapter']},'disabled_status_units':units})
 identity={'kind':'spokane_inventory','source_url':config['source_url'],'phases':phases,'expected_sections':[v.strip() for fields in by_title.values() for _,v in fields],'heading_labels':paths,'section_inventory_ref':source_ref,'disabled_section_ids':disabled,'selection_aliases':aliases,'selection_batches':len(items)}
 return items,source_ref,identity

def parse(data,item,config):
 from model import semantics,sha
 soup=BeautifulSoup(data,'html.parser');node=soup.select_one('#hideRepealed')
 if node is None:raise ValueError('Spokane full View Selected legal container absent')
 expected=item['expected_sections'];expected_set=set(expected);labels=item['heading_labels'];markers={};sections=[];containers=[]
 for a in node.select('a[href]'):
  q=parse_qs(urlsplit(urljoin(item['url'],a['href'])).query)
  if 'Section' in q and q['Section'][0].strip() in expected_set and clean(a.get_text(' ',strip=True))=='Section '+q['Section'][0].strip():
   sections.append((a,q['Section'][0].strip(),clean(str(a.next_sibling))));markers[id(a)]=('section',len(sections)-1)
 for p in node.find_all('p'):
  if not any(a.name in ['li','td','th'] for a in list(p.parents)[:list(p.parents).index(node)]) and re.match(r'^(?:Part|Article|Division|Subchapter)\s+[A-Z0-9IVX]+\s*[.–—:-]\s*\S',clean(p.get_text(' ',strip=True)),re.I):
   label=clean(p.get_text(' ',strip=True));markers[id(p)]=('subdivision',label);containers.append({'node_id':item['id']+'::subdivision:'+str(len(containers)),'disposition':'structural','heading':label});continue
  a=p.find('a',href=True)
  if not a:continue
  q=parse_qs(urlsplit(urljoin(item['url'],a['href'])).query)
  for kind in ['Title','Chapter']:
   if kind in q and labels.get(kind,{}).get(q[kind][0])==clean(p.get_text(' ',strip=True)):
    markers[id(p)]=(kind,clean(p.get_text(' ',strip=True)));containers.append({'node_id':item['url']+'::'+kind+':'+q[kind][0],'disposition':'structural','heading':clean(p.get_text(' ',strip=True))});break
 actual=[s[1] for s in sections]
 if set(actual)!=expected_set:raise ValueError('Full native Spokane legal headings do not equal exact observed Section form inventory')
 buckets=[[] for _ in sections];paths={};current=None;title=None;chapter=None;subdivision=None;preamble=[];container_bodies={}
 def walk(el):
  nonlocal current,title,chapter,subdivision
  marker=markers.get(id(el))
  if marker:
   kind,value=marker
   if kind=='Title':title=value;chapter=None;subdivision=None;current=None
   elif kind=='Chapter':chapter=value;subdivision=None;current=None
   elif kind=='subdivision':subdivision=value;current=None
   else:current=value;paths[value]=[v for v in [config['publication'],title,chapter,subdivision] if v]
  elif isinstance(el,Tag) and any(id(d) in markers for d in el.descendants):
   for child in el.children:walk(child)
  elif current is None:
   if clean(el.get_text(' ',strip=True) if isinstance(el,Tag) else str(el)):
    if title is None:preamble.append(str(el))
    else:container_bodies.setdefault((title,chapter,subdivision),[]).append(copy.copy(el))
  else:buckets[current].append(copy.copy(el))
 for child in node.children:walk(child)
 if preamble:raise ValueError('Unknown unowned text in Spokane full native response')
 rows=[]
 for context,body in container_bodies.items():
  semantic=semantics(BeautifulSoup(''.join(str(x) for x in body),'html.parser'),item['url']);rows.append(dict(semantic,id=item['id']+'::container-owned:'+sha(str(context).encode())[:16],heading=next(v for v in reversed(context) if v),path=[config['publication']]+[v for v in context if v],source_url=item['url'],unit='container_owned_body',document_id=item['id'],raw_ref=item['raw_ref'],raw_sha256=sha(data),jurisdiction=config['jurisdiction'],state=config['state'],publication=config['publication']))
 for i,((anchor,ident,heading),body) in enumerate(zip(sections,buckets)):
  for n,el in enumerate(body):
   if clean(str(el)):
    if isinstance(el,NavigableString) and clean(str(el))==heading:body[n]=NavigableString('')
    break
  fragment=BeautifulSoup(''.join(str(x) for x in body),'html.parser');s=semantics(fragment,item['url']);status=bool(re.search(r'REPEALED|RESERVED',heading,re.I)) and len(s['text'])<30
  if not s['text'] and not status:raise ValueError('Empty native Spokane operative body '+ident)
  rows.append(dict(s,id=ident,heading=heading,path=paths[i],source_url=config['source_url']+'?Section='+ident,unit='legal_status' if status else 'legal_section',document_id=item['id'],raw_ref=item['raw_ref'],raw_sha256=sha(data),jurisdiction=config['jurisdiction'],state=config['state'],publication=config['publication']))
 grouped={}
 for row in rows:grouped.setdefault(row['id'],[]).append(row)
 unique=[]
 for citation,versions in grouped.items():
  seen={}
  for order,row in enumerate(versions):
   bodyhash=sha(row['html'].encode())
   if bodyhash in seen:
    containers.append({'node_id':citation+'::duplicate-source-occurrence:'+str(order),'disposition':'identical_source_duplicate','heading':row['heading'],'body_sha256':bodyhash,'canonical_record_id':seen[bodyhash]['id']});continue
   if len(versions)>1:
    row.update(id=citation+'::source-version:'+bodyhash[:20],citation=citation,unit='legal_section_version',semantic_review_required=True,source_version_history=re.findall(r'(?:Date Passed:|Effective Date:|(?:Recodification )?ORD ).*?(?=Date Passed:|Effective Date:|(?:Recodification )?ORD |$)',row['text']),version_limit='Native ViewSelected renders multiple substantive versions of this same citation. All distinct source bodies retained; no current-version selection inferred.')
    containers.append({'node_id':row['id'],'disposition':'multiple_source_versions','heading':row['heading'],'citation':citation,'body_sha256':bodyhash})
   seen[bodyhash]=row;unique.append(row)
 rows=unique
 for status in item.get('disabled_status_units',[]):
  if not re.search(r'REPEALED|RESERVED|DELETED',status['heading'],re.I):raise ValueError('Unqualified disabled native source section '+status['id'])
  import html
  ident=status['id'];rows.append({'id':ident,'heading':status['heading'],'text':status['heading'],'html':'<p>'+html.escape(status['heading'])+'</p>','path':[config['publication'],labels['Title'].get(ident.split('.')[0]),labels['Chapter'].get('.'.join(ident.split('.')[:2]))],'source_url':config['source_url']+'?Section='+ident,'unit':'legal_status','document_id':item['id'],'raw_ref':status['raw_ref'],'raw_sha256':status['raw_sha256'],'jurisdiction':config['jurisdiction'],'state':config['state'],'publication':config['publication'],'tables':[],'links':[],'assets':[],'image_placeholder_count':0,'source_status_evidence':'Exact disabled Section control and REPEALED label in native full section inventory; no operative body invented.'})
 return rows,containers

def validate_chain(out,phases,initial):
 import json,hashlib,urllib.parse
 if len(phases)!=2:return False
 for kind,phase,pinned in zip(['Title','Chapter'],phases,initial['phases']):
  if phase.get('selection_kind')!=kind:return False
  source=(out/phase['form_source_ref']).read_bytes();url=initial['source_url'];target,fields,disabled,labels=form(source,url,kind)
  if target!=phase['target'] or fields!=phase['fields'] or disabled!=phase['disabled'] or fields!=pinned['fields'] or disabled!=pinned['disabled']:return False
  receipt=json.loads((out/phase['response_ref']).with_suffix('.receipt.json').read_text());body=urllib.parse.urlencode([(k,v) for k,v in fields]).encode()
  if receipt.get('url')!=target or receipt.get('post_fields')!=fields or receipt.get('post_body_sha256')!=hashlib.sha256(body).hexdigest():return False
  if not (out/phase['response_ref']).exists():return False
 target,fields,disabled,labels=form((out/phases[-1]['response_ref']).read_bytes(),initial['source_url'],'Section')
 actual=list(dict.fromkeys(v.strip() for _,v in fields))
 return actual==initial['expected_sections'] and disabled==initial['disabled_section_ids']
