"""Independent all original raw statutory-anchor census; no producer imports/stripping."""
import collections,hashlib,json,pathlib,re,time,urllib.parse
from bs4 import BeautifulSoup
P=pathlib.Path(__file__).resolve().parents[4];R=P/'github/local-jurisdiction-collection';S=R/'packages/collection-source-recovery-2026-10-18/ecode/corrected-corpus-v3/evidence/input';O=pathlib.Path(__file__).resolve().parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cp=json.loads((S/'checkpoint.json').read_text());cov=json.loads((S/'coverage.json').read_text());before={str(f.relative_to(S)):h(f) for f in S.rglob('*') if f.is_file()};t=time.monotonic();rows=[];bodycount=0;pdfs=collections.defaultdict(list);seen=set();names={'ABC':'Alcoholic Beverage Control Law','COR':'Correction Law','MHY':'Mental Hygiene Law','STF':'State Finance Law','PBL':'Public Lands Law','NPC':'Not-for-Profit Corporation Law','RPP':'Real Property Law','HAY':'Highway Law'}
for a in cp['artifacts']:
 f=S/a['path'];assert h(f)==a['sha256'] and f.stat().st_size==a['bytes']
 if a['status']!=200:continue
 soup=BeautifulSoup(f.read_bytes(),'html.parser');code=soup.find(id='codeContent')
 if code is None:continue
 for anchor in code.find_all('a',href=True):
  u=urllib.parse.urljoin(a['url'],anchor['href']);parts=urllib.parse.urlsplit(u);owner=next((x for x in anchor.parents if x.name is not None and 'content'in x.get('class',[]) and re.fullmatch(r'[0-9]+_content',x.get('id',''))),None)
  if owner is None:continue
  ownerid=owner['id'][:-8]
  if re.search(r'\.pdf(?:[?#]|$)',u,re.I):pdfs[u].append({'owner_id':ownerid,'raw_path':a['path'],'raw_sha256':a['sha256'],'literal_href':anchor['href'],'label':anchor.get_text(' ',strip=True)})
  if 'statref' not in anchor.get('class',[]) or parts.netloc!='municipal.codes':continue
  seg=parts.path.strip('/').split('/')
  if not ((len(seg)==3 and seg[0]=='NY' and seg[1]in names) or re.fullmatch('/US/USC/[0-9]+',parts.path)):continue
  assert parts.scheme=='https' and not parts.query and not parts.fragment
  context=anchor.find_parent('p');assert context is not None,'Actual witness must have semantic paragraph, no broaddiv fallback';txt=context.get_text(' ',strip=True);label=anchor.get_text(' ',strip=True)
  assert not anchor.has_attr('download') and not anchor.get('type','').strip()
  if seg[0]=='NY':
   assert names[seg[1]].casefold() in txt.casefold();article=seg[1]=='RPP' and seg[2].startswith('A');target=seg[2][1:] if article else seg[2];assert label==target
   if article:assert re.search(r'(?i)\bArticle\s+'+re.escape(target)+r'\b',txt)
  else:assert label==seg[2] and (re.search(r'(?i)\bTitle\s+'+re.escape(label)+r'\s+of\s+the\s+United\s+States\s+Code\b',txt) or re.search(r'\b'+re.escape(label)+r'\s+U\.S\.C\.',txt))
  assert not re.search(r'data\s*:\s*image/',txt,re.I)
  rows.append({'owner_id':ownerid,'url':u,'label':label,'raw_path':a['path'],'raw_sha256':a['sha256'],'source_anchor_html':str(anchor),'anchor_sha256':hashlib.sha256(str(anchor).encode()).hexdigest(),'source_context_html':str(context),'context_sha256':hashlib.sha256(str(context).encode()).hexdigest(),'context_text':txt,'typed_statref':True,'context_kind':'source paragraph','explicit_law_name_verified':True,'external_law_acquired':False,'source_owner_unique':len(code.find_all(id=owner['id']))==1})
assert len(rows)==21 and len({x['url'] for x in rows})==18 and all(x['source_owner_unique'] for x in rows)
required=set(cov['missing_assets']);assert len(required)==4 and required<=set(pdfs)
assert len(cp['artifacts'])==401 and sum(a['status']==200 for a in cp['artifacts'])==400
assert not [a for a in cp['artifacts'] if a['role']in ['root-end','contents-end']]
assert cov['complete'] is False and cov['attachments_complete'] is False and cov['edition_complete'] is False and cov['start_end_inventory_consistent'] is False
assert '403'in str(cov['errors'])
assert before=={str(f.relative_to(S)):h(f) for f in S.rglob('*') if f.is_file()}
report={'passed':True,'raw_hashes_checked':401,'successful_original_HTML':400,'typed_source_occurrences':len(rows),'distinct_forwarding_URLs':len({x['url'] for x in rows}),'source_owners':len({x['owner_id'] for x in rows}),'all_source_contexts_are_paragraphs_with_explicit_law_name_and_target_label':True,'actual_context_image_payload_exposure':False,'source_records':rows,'required_PDF_references':{u:pdfs[u] for u in sorted(required)},'recorded_access_stops':[a for a in cp['artifacts'] if a['status']in [403,429]],'errors':cov['errors'],'closing_artifacts':0,'complete':False,'source_files_before_after_equal':len(before),'original_records_sha256':h(S/'records.jsonl'),'new_publisher_requests_image_native_operations':0,'producer_imports':0,'seconds':time.monotonic()-t,'executed_source_sha256':h(pathlib.Path(__file__))}
(O/'source-census.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['source_records','required_PDF_references','recorded_access_stops']},indent=2))
