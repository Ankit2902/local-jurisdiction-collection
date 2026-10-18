"""Independent actual73-row package consumer and original header/callout/raw/proof checks."""
import csv,hashlib,json,pathlib,re,time
from bs4 import BeautifulSoup
P=pathlib.Path(__file__).resolve().parents[5];O=pathlib.Path(__file__).resolve().parent;A=O.parent
B=P/'outputs/collection-readiness-post9ef7220-2026-10-17/municipal-corpus-reader-v1';Q=B/'package-v3';I=Q/'evidence/input';S=P/'outputs/collection-readiness-post-91f6c59-2026-10-17/ecode/phoenix-image-context-replay-v2'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().split('\n') if x]
def tree(p):return {str(f.relative_to(p)):h(f) for f in p.rglob('*') if f.is_file()}
source_before=tree(S);package_before=tree(Q);candidate_before=tree(B/'source');t=time.monotonic()
assert tree(I)==source_before and len(source_before)==73
proof=load(B/'actual-standard-proof/read-only-proof.json');family=load(B/'actual-standard-proof/family-verification.json');v=proof['verification'];cov=load(S/'coverage.json')
assert proof['evidence_sha256_before']==proof['evidence_sha256_after']==source_before
assert proof['collector_sources_before']==proof['collector_sources_after']
assert v['runtime_before']==v['runtime_after'] and not v['forbidden_calls'] and proof['publisher_requests']==0
assert family.pop('verified') is True and family==cov
for name in ['read-only-proof.json','family-verification.json']:assert h(Q/'evidence/proofs'/name)==h(B/'actual-standard-proof'/name)
assert load(Q/'inherited-coverage.json')==cov
rs=lines(S/'records.jsonl');ir={r['id']:r for r in rs};inv={n['id']:n for n in load(S/'inventory.json')};ds={d['id']:d for d in load(S/'dispositions.json')};cp=load(S/'checkpoint.json');arts={a['path']:a for a in cp['artifacts']};base=cp['publication_url']
raworder=load(A/'independent-source-order.json');order=[base,base+'#NT']+[n['id'] for n in raworder['source_contents_sequence']];assert len(order)==len(set(order))==279
rows=load(Q/'aggregate-fulltext.json')['provisions'];ps=lines(Q/'record-provenance.jsonl');ns=lines(Q/'source-nodes.jsonl');disp=lines(Q/'node-dispositions.jsonl')
assert [n['source_url'] for n in ns]==order and len(disp)==279
assert [p['locator']['canonical_url'] for p in ps]==[u for u in order if u in ir] and len(rows)==len(ps)==73
fields=['jurisdiction','code_name','division','title','subtitle','chapter','subchapter','article','part','subpart','section_number','section_name','citation','full_text','source_url','scrape_date'];roles=fields[2:10]
headings={x['id']:x for x in load(A/'original-heading-witnesses.json')};callouts=[];counts={x:0 for x in roles}
for row,p in zip(rows,ps):
 u=p['locator']['canonical_url'];r=ir[u];chain=[];k=u;seen=set()
 while k:
  assert k in inv and k not in seen;seen.add(k);chain.insert(0,inv[k]);k=ir.get(k,{}).get('parent_id') or inv[k].get('parent_id')
 assert chain==p['hierarchy_chain'] and [x['heading'] for x in chain]==r['path']
 e={f:'' for f in fields};e.update(jurisdiction='Phoenix',code_name=cp['identity']['name'],citation=r['heading'],section_name=r['heading'].strip(),full_text=r['semantic_html'],source_url=u,scrape_date=arts[r['raw_witnesses'][0]]['retrieved_at'])
 for role in roles:
  labels=[]
  for n in chain:
   if re.fullmatch('(?i)'+role+r'\.? (.+)',n['heading'].strip()) and n['heading'].strip() not in labels:labels.append(n['heading'].strip())
  if len(labels)==1:e[role]=labels[0];counts[role]+=1
 m=re.fullmatch(r'(?i)(?:sec\.|section\.?) (\S+)(?: (.*))?',r['heading'].strip(),re.S)
 if m and any(x.isdigit() for x in m[1]) and all(x.isalnum() or x in '.-()' for x in m[1]):e['section_number']=m[1];e['section_name']=(m[2] or '').removeprefix('- ')
 assert list(row)==fields and row==e,u
 for f in ['notes_html','tables_html','links','assets','image_references','image_placeholder_count']:assert p[f]==r[f],(u,f)
 assert p['source_heading_image_placeholders']==0
 original=headings[u];assert BeautifulSoup(p['source_heading_html'],'html.parser')==BeautifulSoup(original['html'],'html.parser'),u
 a=arts[r['raw_witnesses'][0]];raw=(S/a['path']).read_text();articleid=original['id'].split('#')[-1] if '#' in u else u.rsplit('/',1)[-1]
 match=re.search(r'<article\b[^>]*\sid="'+re.escape(articleid)+r'"[^>]*>',raw);assert match
 mh=re.search(r'<header\b[^>]*>.*?</header>',raw[match.end():],re.S);assert mh
 headerraw=mh[0];assert hashlib.sha256(headerraw.encode()).hexdigest()==p['source_heading_raw_html_sha256']
 assert p['source_heading_html']==headerraw and p['source_heading_html_sha256']==hashlib.sha256(headerraw.encode()).hexdigest()
 assert len(p['source_heading_links'])==len(original['links'])
 for got,want in zip(p['source_heading_links'],original['links']):
  assert got['source_href']==want['literal_href'] and got['resolved_url']==want['resolved_url'] and got['label']==want['visible_label']
  assert got['same_owner_fragment'] is True and got['target_count_in_own_article']==1 and got['target_id']==want['target_note_id']
  target=re.search(r'<div\b[^>]*\sid="'+re.escape(want['target_note_id'])+r'"[^>]*>.*?</div>',raw,re.S);assert target and '<div' not in target[0][1:]
  assert hashlib.sha256(target[0].encode()).hexdigest()==got['source_target_html_sha256']
  callouts.append({'owner':u,'href':got['source_href'],'target':got['target_id'],'accessible':'record-provenance.jsonl:source_heading_links/source_heading_html','note_once_in_canonical_body':r['semantic_html'].count('id="'+got['target_id']+'"')==1})
assert len(callouts)==3 and all(x['note_once_in_canonical_body'] for x in callouts)
for prefix in ['', 'publications/'+proof['publication_id']+'/']:
 for kind,stem in [('fulltext','aggregate-fulltext'),('toc','aggregate-toc')]:
  jf=Q/(prefix+kind+'.json' if prefix else stem+'.json');cf=jf.with_suffix('.csv');actual=load(jf)['provisions'];csvrows=list(csv.DictReader(cf.open(encoding='utf-8-sig',newline='')))
  assert cf.read_bytes().startswith(b'\xef\xbb\xbf') and csvrows==actual
  assert actual==(rows if kind=='fulltext' else [dict(r,full_text='') for r in rows])
for n,d,u in zip(ns,disp,order):
 assert n['publisher_descriptor']==inv[u] and d['node_id']==n['node_id']
 if u not in ds:assert d['disposition']=='unresolved' and not d['record_ids']
 else:assert d['evidence']==ds[u] and d['record_ids']==([proof['publication_id']+':'+u] if u in ir else [])
assert sum(d['disposition']=='unresolved' for d in disp)==198 and sum(d['disposition']=='structural' for d in disp)==8
vr=load(Q/'validation-report.json');rm=load(Q/'run-manifest.json');assert vr['complete'] is False and vr['downstream_ready'] is False and vr['selected_publication_ready'] is False and rm['status']=='incomplete'
assert not cov['edition_complete'] and not cov['attachments_complete'] and not cov['publication_text_complete'] and not cov['start_end_inventory_consistent'] and not cov['identity_binding']['state_source_verified']
assert '429' in str(cov['errors']) and not cov['resumable']
assert tree(S)==source_before and tree(Q)==package_before and tree(B/'source')==candidate_before
result={'passed':True,'source_files_unchanged':73,'package_files_unchanged':len(package_before),'candidate_files_unchanged':len(candidate_before),'records':73,'canonical_field_values':73*16,'source_inventory_dispositions':279,'missing_explicitly_unresolved':198,'source_empty_and_root_structural':8,'heading_raw_html_and_hashes_checked':73,'heading_note_links_accessible':callouts,'source_order_basis':'Independent original source contents DOM preorder after explicit root preface','source_proof_sha256':h(B/'actual-standard-proof/read-only-proof.json'),'family_report_sha256':h(B/'actual-standard-proof/family-verification.json'),'package_manifest_sha256':h(Q/'run-manifest.json'),'reader_source_sha256':h(B/'source/municipal_codes_html.py'),'reader_sources':candidate_before,'role_counts':counts,'source_notes_once':3,'tables':0,'IMAGE':0,'complete':False,'edition_complete':False,'state_source_verified':False,'source429_and_missing_closing_preserved':True,'network_image_render_decode_native_parse_producer_import_calls':0,'seconds':time.monotonic()-t,'executed_source_sha256':h(pathlib.Path(__file__))}
(O/'package-consumer-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='reader_sources'},indent=2))
