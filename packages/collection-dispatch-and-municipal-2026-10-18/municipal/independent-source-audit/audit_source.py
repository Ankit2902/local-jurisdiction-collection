"""Independent original Phoenix typed-article ownership census; no producer imports."""
import collections,copy,hashlib,json,pathlib,re,time,urllib.parse
from bs4 import BeautifulSoup,Tag,NavigableString
P=pathlib.Path(__file__).resolve().parents[4];O=pathlib.Path(__file__).resolve().parent
S=P/'outputs/collection-readiness-post-91f6c59-2026-10-17/ecode/phoenix-image-context-replay-v2'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().split('\n') if x]
def collapse(s):return ''.join(c for c in s if not c.isspace())
def sig(e):
 out=[]
 def walk(x):
  if isinstance(x,NavigableString):
   if collapse(str(x)):out.append(['text',collapse(str(x))])
  elif isinstance(x,Tag):
   out.append(['open',x.name,dict(x.attrs)])
   for c in x.children:walk(c)
   out.append(['close',x.name])
 walk(e);return out
cp=load(S/'checkpoint.json');cov=load(S/'coverage.json');rmap={r['id']:r for r in lines(S/'records.jsonl')};inv={n['id']:n for n in load(S/'inventory.json')};disps={d['id']:d for d in load(S/'dispositions.json')}
before={str(p.relative_to(S)):h(p) for p in S.rglob('*') if p.is_file()};t=time.monotonic();base='https://phoenix.municipal.codes/Charter'
articles={};witnesses=collections.defaultdict(list);raworder=[];tocentries=[];errors=[];counts=collections.Counter();all_ui=[];outside=[]
for a in cp['artifacts']:
 f=S/a['path'];assert h(f)==a['sha256'] and f.stat().st_size==a['bytes']
 if a['status']!=200:continue
 soup=BeautifulSoup(f.read_bytes(),'html.parser');main=soup.find('main')
 if a['role']=='contents-start':
  for li in main.find_all('li',attrs={'data-identifier':True}):
   if 'tocitem' not in li.get('class',[]):continue
   aa=li.find('a',recursive=False);assert aa
   u=urllib.parse.urljoin(a['url'],aa['href']);parent=li.find_parent('li',attrs={'data-identifier':True});pa=parent.find('a',recursive=False) if parent else None
   tocentries.append({'id':u,'heading':' '.join(aa.stripped_strings),'parent_id':urllib.parse.urljoin(a['url'],pa['href']) if pa else None,'source_classes':li.get('class',[]),'literal_identifier':li['data-identifier']})
 for source in main.find_all('article') if main else []:
  ident=source['id'];u=base+'#NT' if ident=='NT' else base+'/'+ident
  own=copy.deepcopy(source);parent=source.find_parent('article');parentid=base+'/'+parent['id'] if parent else base
  headers=own.find_all('header',recursive=False);assert len(headers)==1
  heading=' '.join(headers[0].stripped_strings);headerhtml=str(headers[0]);headers[0].decompose()
  # Independent identity boundary: only separately typed descendant articles have their own legal owner.
  for child in list(own.find_all('article')):
   if child.parent is not None:child.decompose()
  # Exact observed per-owner selection control, separately retained as UI witness.
  for child in list(own.find_all(recursive=False)):
   if child.name=='div' and set(child.get('class',[]))=={'track-indicator','selected','d-none'}:
    assert child.get_text(' ',strip=True).startswith('This ') and 'included in your selections.' in child.get_text(' ',strip=True)
    all_ui.append({'raw':a['path'],'owner':u,'html':str(child)});child.decompose()
  item={'heading':heading,'header_html':headerhtml,'body':own,'parent':parentid}
  if u in articles:
   assert articles[u]['heading']==heading and sig(articles[u]['body'])==sig(own),'Repeated own source differs'
  else:articles[u]=item;raworder.append(u)
  witnesses[u].append({'path':a['path'],'sha256':a['sha256'],'role':a['role']})
  # Actual scoped exclusions cannot hide legal source: no additional nav/script/control within retained own body.
  for x in own.find_all(True):
   if x.name in ['header','nav','script','style','button','input','form'] or 'track-indicator' in x.get('class',[]):errors.append(['unclassified_inside_owner',u,str(x)])
assert len(tocentries)==277 and len({n['id'] for n in tocentries})==277
for n in tocentries:
 d=inv[n['id']]
 for k in ['heading','parent_id','source_classes']:assert d.get(k)==n[k],(n['id'],k,d.get(k),n[k])
assert set(inv)=={n['id'] for n in tocentries}|{base,base+'#NT'}
record_witness=[]
for u,item in articles.items():
 own=item['body'];expectedtext=collapse(own.get_text());sourceids=[x['id'] for x in [own]+own.find_all(True) if x.get('id')];links=[[x.get_text(),x.get('href'),x.get('rel'),x.get('title')] for x in own.find_all('a')]
 if u not in rmap:
  assert not expectedtext and not own.find_all(['table','img','svg','object','picture']),('Unemitted nonempty original',u)
  assert disps[u]['classification']=='structural_empty';counts['source_proven_empty_articles']+=1
  continue
 r=rmap[u];rich=BeautifulSoup(r['content_html'],'html.parser').find();semantic=BeautifulSoup(r['semantic_html'],'html.parser').find()
 if collapse(item['heading'])!=collapse(r['heading']):errors.append(['heading',u,item['heading'],r['heading']])
 for kind,body in [('rich',rich),('canonical',semantic)]:
  if sig(own)!=sig(body):errors.append(['DOM_signature',u,kind])
  if collapse(body.get_text())!=expectedtext:errors.append(['body_text',u,kind])
  if [x['id'] for x in [body]+body.find_all(True) if x.get('id')]!=sourceids:errors.append(['source_IDs',u,kind])
  if [[x.get_text(),x.get('href'),x.get('rel'),x.get('title')] for x in body.find_all('a')]!=links:errors.append(['links',u,kind])
 if r['parent_id']!=item['parent']:errors.append(['own_parent',u,r['parent_id'],item['parent']])
 assert all(w in [x['path'] for x in witnesses[u]] for w in r['raw_witnesses'])
 notes=[str(x) for x in own.find_all(class_='note')]
 if notes!=r['notes_html']:errors.append(['notes',u])
 assert not own.find_all('table') and r['tables_html']==[]
 images=own.find_all(['img','picture','svg','object','embed','input']);assert not images and r['image_placeholder_count']==0 and r['image_references']==[]
 counts.update({'owned_records':1,'source_IDs':len(sourceids),'links':len(links),'notes':len(notes),'text_nonwhitespace_characters':len(expectedtext),'source_subsection_nodes':len(own.find_all('section'))})
 record_witness.append({'id':u,'heading':item['heading'],'source_nonwhitespace_sha256':hashlib.sha256(expectedtext.encode()).hexdigest(),'raw_witnesses':witnesses[u],'ids':sourceids,'links':links,'notes':len(notes),'own_parent':item['parent']})
assert set(rmap)<=set(articles)
assert set(disps)==set(articles)|{base} and len(disps)==81 and len(articles)==80,(len(disps),len(articles))
missing=set(inv)-set(disps);assert missing==set(cov['missing_ids']) and len(missing)==198
assert not cov['complete'] and not cov['start_end_inventory_consistent'] and cov['identity']['currency_raw']==['The Phoenix City Charter is current through the November 6, 2018 election.']
assert not errors,errors[:8]
after={str(p.relative_to(S)):h(p) for p in S.rglob('*') if p.is_file()};assert before==after
(O/'independent-source-order.json').write_text(json.dumps({'source_contents_sequence':tocentries,'first_acquired_article_sequence':raworder,'missing_ids_source_order':[n['id'] for n in tocentries if n['id'] in missing]},indent=2)+'\n')
(O/'owned-source-witnesses.json').write_text(json.dumps(record_witness,indent=2)+'\n')
r={'passed':True,'scope':'Retained partial PhoenixCharter acquired HTML only','raw_artifacts':len(cp['artifacts']),'successful_HTML':sum(a['status']==200 for a in cp['artifacts']),'original_unique_typed_articles':len(articles),'source_inventory':len(inv),'source_TOC_entries':len(tocentries),'dispositions':len(disps),'missing_ids':len(missing),'counts':dict(counts),'mismatches':errors,'same_source_signature_in_rich_and_canonical_HTML':True,'independent_original_header_text_all_compared':True,'UI_controls_separately_classified':len(all_ui),'required_pdf_or_table_source_applicability':'No source tables or images in the acquired original bodies; unacquired nodes remain unknown','original_input_files_unchanged':len(before),'input_checkpoint_sha256':h(S/'checkpoint.json'),'records_sha256':h(S/'records.jsonl'),'audit_source_sha256':h(pathlib.Path(__file__)),'producer_imports':0,'network_image_render_decode_extract_OCR_calls':0,'complete':False,'currentness_qualified':False,'seconds':time.monotonic()-t}
(O/'source-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
