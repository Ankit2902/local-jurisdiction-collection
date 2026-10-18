"""Independent retained-HTML/receipt/normalized-output audit. No collector/PDF/image imports."""
import pathlib,json,hashlib,csv,collections,datetime,sys,re
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse
P=pathlib.Path(sys.argv[1]).resolve();O=pathlib.Path(sys.argv[2]);h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());norm=lambda s:' '.join(s.split())
assert h(P/'MANIFEST.json')=='f138e7116c4552c242c79177fae024b6eb0158617b821c72a8818db539008537'
manifest=read(P/'MANIFEST.json')['files'];assert all(h(P/n)==x['sha256']and(P/n).stat().st_size==x['bytes']for n,x in manifest.items())
class N:
 def __init__(self,tag,attrs,parent=None):self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.parts=[]
 def text(self):return ''.join(x if isinstance(x,str)else x.text()for x in self.parts)
 def walk(self):
  yield self
  for x in self.parts:
   if isinstance(x,N):yield from x.walk()
class T(HTMLParser):
 def __init__(self):super().__init__();self.root=N('root',[]);self.st=[self.root]
 def handle_starttag(self,t,a):
  n=N(t,a,self.st[-1]);self.st[-1].parts.append(n)
  if t not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.st.append(n)
 def handle_endtag(self,t):
  for i in range(len(self.st)-1,0,-1):
   if self.st[i].tag==t:self.st=self.st[:i];break
 def handle_data(self,d):self.st[-1].parts.append(d)
def groups(data,source_url):
 t=T();t.feed(data.decode('utf-8'));centers=[n for n in t.root.walk()if'document-center'in n.attrs.get('class','').split()and any(p.tag=='main'for p in ancestors(n))];assert len(centers)==1
 out=[]
 for g in centers[0].parts:
  if not isinstance(g,N)or g.tag!='div':continue
  ds=[x for x in g.parts if isinstance(x,N)and x.tag=='div'];assert len(ds)>=2
  label=norm(ds[0].text());anchors=[(urljoin(source_url,n.attrs['href']),norm(n.text()))for n in ds[1].walk()if n.tag=='a'and n.attrs.get('href')];out.append((label,anchors))
 return out
def ancestors(n):
 while n.parent:n=n.parent;yield n
cfg=read(P/'config.json');state=read(P/'run/checkpoint.json');cov=read(P/'run/coverage.json');inventory=read(P/'source-inventory.json');source_url=cfg['source_url'];assert cfg['jurisdiction']=='Clark County'and cfg['state']=='NV'and cfg['mode']=='pdf_set'and cfg['coverage_level']=='file_pages'
opening=P/'run'/state['identity']['source_ref'];closing=P/'run'/state['consistency']['raw_ref'];assert opening.read_bytes()==closing.read_bytes()and h(opening)==inventory['source_html_sha256']==state['identity']['source_sha256']
gs=groups(opening.read_bytes(),source_url);current=[a for label,a in gs if label=='Title 30 - Effective 9/17/2026'];assert len(current)==1 and len(current[0])==30
legacy=[(label,a)for label,a in gs if label!='Title 30 - Effective 9/17/2026'];assert len(legacy)==1 and '12/31/2023'in legacy[0][0]and len(legacy[0][1])==66
expected=current[0];assert expected==[(x['url'],x['heading'])for x in state['items']]==[(x['url'],x['label'])for x in inventory['current_documents']]
assert legacy[0][1]==[(x['url'],x['label'])for x in inventory['historical_documents_explicitly_outside_current_group']]
assert set(u for u,l in expected).isdisjoint(u for u,l in legacy[0][1])
assert all(re.fullmatch(cfg['include_url_regex'],u)and urlparse(u).hostname=='www.clarkcountynv.gov'for u,l in expected)
assert all(token in norm(opening.read_text())for token in []) # identity checked against actual source text below
page_tree=T();page_tree.feed(opening.read_text());page_text=norm(page_tree.root.text());assert all(token in page_text for token in cfg['source_identity_tokens'])
assert hashlib.sha256(json.dumps(cfg,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==state['config_sha256']and cfg==read(P/'run/config.json');assert state['completed']and len(state['items'])==len(state['done'])==30 and not state['limits_history']
# Compact duplicate opening-body aliases retain all exact original receipt hashes.
aliases=read(P/'compact-body-aliases.json')['aliases'];assert len(aliases)==31
aliasmap={x['omitted_duplicate']:x for x in aliases}
for x in aliases:assert h(P/x['retained_byte_identical_alias'])==x['sha256']and(P/x['retained_byte_identical_alias']).stat().st_size==x['bytes']
receipts={};unique={}
for folder in ['capture/raw','run/raw']:
 for rp in(P/folder).glob('*.receipt.json'):
  m=read(rp);body=rp.with_suffix('.bin');rel=body.relative_to(P).as_posix()
  if not body.exists():assert rel in aliasmap;body=P/aliasmap[rel]['retained_byte_identical_alias']
  assert h(body)==m['sha256']and body.stat().st_size==m['bytes'];assert m['status']==200 and not m.get('access_stop')and not m.get('policy_omitted_image')and m['final_url']==m['url']and urlparse(m['url']).hostname=='www.clarkcountynv.gov'
  mime=next(v for k,v in m['headers'].items()if k.lower()=='content-type').split(';')[0].lower().strip();assert mime in ['application/pdf','text/html']
  receipts[rp.relative_to(P).as_posix()]=m;unique[h(rp)]=m
assert len(unique)==63
# All30initial native responses match all30later actual distinct requests/receipts.
checks={x['id']:x for x in state['item_consistency']};assert len(checks)==30
allrows=[];initial_times=[];closing_times=[]
for i in state['items']:
 ident=i['id'];doc=read(P/'run/items'/(hashlib.sha256(ident.encode()).hexdigest()[:24]+'.json'));assert doc['item']==i
 raw=P/'run'/doc['raw_ref'];initial=read(raw.with_suffix('.receipt.json'));end=P/'run'/checks[ident]['raw_ref'];later=read(end.with_suffix('.receipt.json'))
 assert checks[ident]['matches_initial_content']and initial['url']==later['url']==checks[ident]['url']==i['url']and initial['status']==later['status']==200
 assert h(raw)==h(end)==doc['raw_sha256']==initial['sha256']==later['sha256']==checks[ident]['sha256']and raw.read_bytes().startswith(b'%PDF-')
 assert datetime.datetime.fromisoformat(later['started_at'])>datetime.datetime.fromisoformat(initial['finished_at'])and initial['started_at']!=later['started_at'];initial_times.append(initial['started_at']);closing_times.append(later['started_at'])
 assert [x['physical_page']for x in doc['records']]==list(range(1,len(doc['records'])+1))
 for x in doc['records']:assert x['document_id']==ident and x['raw_sha256']==doc['raw_sha256']and x['unit']=='pdf_page'and x['raw_ref']==doc['raw_ref']
 allrows.extend(doc['records'])
for body in(opening,closing):m=read(body.with_suffix('.receipt.json'));assert m['url']==source_url and m['status']==200
assert read(closing.with_suffix('.receipt.json'))['started_at']>read(opening.with_suffix('.receipt.json'))['finished_at']
assert len(allrows)==381 and len(allrows[:352])==352
stored=[json.loads(x)for x in(P/'run/records.jsonl').read_text().splitlines()];assert stored==allrows
csv.field_size_limit(32_000_000);cs=list(csv.DictReader((P/'run/records.csv').open()));assert len(cs)==381
for x,c in zip(allrows,cs):assert x['id']==c['id']and x['text']==c['text']
assert len({x['id']for x in allrows})==381
assert 'Clark County' in allrows[0]['text']and'Title 30: Unified Development Code'in allrows[0]['text']and'EFFECTIVE SEPTEMBER 17, 2026'in allrows[0]['text']
qs=[x['pdf_qualification']for x in allrows];assert all(q[k]is True for q in qs for k in ['source_word_ownership_complete','normalized_source_word_characters_agree','source_words_cover_deduplicated_glyph_characters','independent_text_engine_characters_agree'])
assert sum(q['source_word_count']for q in qs)==149304
assert sum(q['detected_table_count']for q in qs)==226 and sum(q['detected_table_cells']for q in qs)==7488 and sum(q['independent_table_cells_agree']for q in qs)==7292
assert sum(bool(q['review_conditions'])for q in qs)==43
private=[(x['physical_page'],x['pdf_qualification']['unmapped_or_private_use_codepoints'])for x in allrows if x['pdf_qualification']['unmapped_or_private_use_codepoints']];assert [x[0]for x in private]==[225,226]
assert sum(q.get('text_glyph_comparison_applicability')=='not_applicable_source_has_no_text_glyph_characters'for q in qs)==27
assert sum(x['text'].count('[IMAGE]')for x in allrows)==229
assert cov['requested_level']=='file_pages'and cov['requested_coverage_complete']and cov['publication_file_coverage_complete']and cov['pdf_page_extraction_complete']and cov['source_consistency_complete']
assert cov['legal_semantic_coverage_complete']is False and cov['jurisdiction_complete']is False and cov['manual_review_required']is True
for s in cov['pdf_files'].values():assert s['acquired_page_ids']==list(range(1,s['expected_pages']+1))and not s['page_gaps']and s['duplicates']==0
ver=read(P/'verify.stdout');runhashes={x.relative_to(P/'run').as_posix():h(x)for x in(P/'run').rglob('*')if x.is_file()};assert len(runhashes)==177 and hashlib.sha256(json.dumps(runhashes,sort_keys=True).encode()).hexdigest()==ver['run_manifest_sha256']and ver['all_run_files_unchanged']and not ver['forbidden_calls']
bind=read(P/'source-binding.json');vb=read(P/'verification-source-binding.json');assert vb['verification_entrypoint_sha256']==h(P/'verify_guarded.py')and vb['runtime_scripts_sha256']==bind['scripts']
for n,s in bind['scripts'].items():assert h(P/'runtime'/n)==s
for n,s in state['scripts'].items():assert h(P/'runtime'/n)==h(P/'run/executed'/n)==s
assert read(P/'status.json')['collection_exit']==0 and not read(P/'status.json')['image_calls']
assert all(h(P/n)==x['sha256']for n,x in manifest.items())
times=sorted(datetime.datetime.fromisoformat(x['started_at'])for x in unique.values());minimum=min((b-a).total_seconds()for a,b in zip(times,times[1:]))
report={'passed':True,'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'packet_manifest_sha256':h(P/'MANIFEST.json'),'packet_files_unchanged':len(manifest),'source_config_sha256':h(P/'config.json'),'source_identity':'Clark County,NV;Title30 currentgroup effective9/17/2026','current_group_documents':30,'core_code_documents':1,'associated_maps':29,'legacy_group_documents_explicitly_excluded':66,'legacy_group_label':legacy[0][0],'initial_native_HTTP200':30,'actual_later_native_HTTP200':30,'all_opening_later_native_hashes_equal':True,'actual_unique_HTTP200_receipt_witnesses':len(unique),'retained_HTML_byte_equal_opening_closing':True,'initial_capture_duplicate_body_aliases_verified':31,'source_group_and_native_core_cover_effective_date':'9/17/2026;opaque10.7filename not interpreted','record_units':'physicalPDFpages,notlegalprovisions','physical_pages':381,'unique_page_records':381,'detected_tables':226,'detected_cells':7488,'independently_agreeing_cells':7292,'cell_disagreements':196,'review_pages':43,'unmapped_codepoint_pages':[225,226],'unmapped_distinct_codepoint':'U+F0FC','source_words':149304,'source_proven_no_native_glyph_pages':27,'literal_IMAGE_occurrences':229,'strict_readonly_files_unchanged':177,'strict_readonly_forbidden_calls':[],'source_runtime_bindings_equal':True,'nominal_gate_seconds':3.5,'minimum_recorded_request_start_interval':minimum,'requested_file_pages_complete':True,'legal_semantic_coverage_complete':False,'jurisdiction_complete':False,'catalog_promoted':False,'new_native_parse_network_or_image_operations':False,'scope':'Independent retainedrawHTML/config/inventory/HTTPnativehash/code/normalizedoutputmetrics review. Actual381page parsing/guard qualification belongs to capturedproducer+single strictreadonly; no new semantic/currentlaw dependency or imagecontent qualification.'}
O.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
