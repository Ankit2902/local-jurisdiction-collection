"""Independent final byte bridge and all-row consumer; no producer imports or parsing calls."""
import csv, hashlib, json, pathlib, re, sys, time
P=pathlib.Path(__file__).resolve().parents[4]
B=P/'outputs/collection-readiness-post716cfcb-2026-10-17/ecode-recovery-audit-v1'
O=pathlib.Path(__file__).resolve().parent
Q=B/'corrected-corpus-v3'; I=Q/'evidence/input'
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def lines(p): return [json.loads(x) for x in p.read_text().split('\n') if x]
def tree(p): return {str(f.relative_to(p)):h(f) for f in p.rglob('*') if f.is_file()}
def require(b,msg):
 if not b: raise AssertionError(msg)
t=time.monotonic(); manifest=load(B/'FINAL-V3-MANIFEST.json')
require(h(B/'FINAL-V3-MANIFEST.json')=='fd2f54293862534c12d3b59b3a825a1168837a0c78e467723e609746dba4c92d','Wrong final manifest')
for name,d in manifest['files'].items():
 f=B/name;require(h(f)==d['sha256'] and f.stat().st_size==d['bytes'],'Manifest drift '+name)
require(len(manifest['files'])==567,'Wrong selected file count')
bridge=load(B/'v2-v3-whole-source-byte-bridge.json')
streams=['records.jsonl','records.csv','inventory.json','dispositions.json','image-omissions.json','link-ledger.json']
for name in streams:
 require(h(B/'albany-derived-v2'/name)==h(B/'albany-derived-v3'/name)==h(I/name),'Normalized byte bridge '+name)
raw2=tree(B/'albany-derived-v2/raw'); raw3=tree(B/'albany-derived-v3/raw')
require(raw2==raw3==tree(I/'raw') and len(raw2)==401,'Raw bridge')
proof=load(B/'actual-standard-proof-v3/read-only-proof.json');v=proof['verification']
require(h(B/'actual-standard-proof-v3/read-only-proof.json')=='9f76517165bfdc47405973aef976df8a6db28eb18a1a28f7a3c0306f77413c8b','Proof identity')
require(proof['evidence_sha256_before']==proof['evidence_sha256_after']==tree(I),'Input/proof complete byte maps')
require(len(tree(I))==470,'470 input bytes closure')
require(proof['collector_sources_before']==proof['collector_sources_after'],'Collector source drift')
require(v['runtime_before']==v['runtime_after'] and not v['forbidden_calls'] and proof['publisher_requests']==0,'Runtime/forbidden actions')
require(not proof['source_changed_during_run'] and not proof['runtime_changed_during_run'],'Changed runtime')
for n,d in proof['collector_sources_before'].items():require(h(I/'executed-source'/n)==d,'Actual selected source '+n)
fr=B/'actual-standard-proof-v3/family-verification.json';require(h(fr)==v['family_report_sha256'],'Family proof digest')
report=load(fr);cov=load(I/'coverage.json');require(report.pop('verified') is True and report==cov,'Actual family report vs inherited coverage')
for name in ['read-only-proof.json','family-verification.json']:
 require(h(Q/'evidence/proofs'/name)==h(B/'actual-standard-proof-v3'/name),'Packaged proof '+name)
require(load(Q/'inherited-coverage.json')==cov,'Inherited coverage changed')
cp=load(I/'checkpoint.json');arts={a['path']:a for a in cp['artifacts']}; inv={n['id']:n for n in load(I/'inventory.json')}; ds={d['id']:d for d in load(I/'dispositions.json')}
ir={r['id']:r for r in lines(I/'records.jsonl')};positions=load(O/'independent-publisher-positions.json')
rows=load(Q/'aggregate-fulltext.json')['provisions'];prs=lines(Q/'record-provenance.jsonl')
require(len(rows)==len(prs)==len(ir)==3006,'Canonical count')
require([p['locator']['id'] for p in prs]==sorted(ir,key=lambda k:positions[k]),'Independent raw publisher ordering')
fields=['jurisdiction','code_name','division','title','subtitle','chapter','subchapter','article','part','subpart','section_number','section_name','citation','full_text','source_url','scrape_date']
roles=fields[2:10]; counts={f:0 for f in roles};images=0;tables=0;notes=0;conflicts=0
for ordinal,(row,p) in enumerate(zip(rows,prs)):
 ident=p['locator']['id'];r=ir[ident];chain=[];k=ident;seen=set()
 while k:
  require(k in inv and k not in seen,'Ancestry unknown/cycle');seen.add(k);chain.insert(0,inv[k]);k=ir.get(k,{}).get('parent_id') or inv[k].get('parent_id')
 require(chain==p['hierarchy_chain'] and r['path']==[n['heading'] for n in chain],'Source hierarchy mismatch '+ident)
 expected={f:'' for f in fields};expected.update(jurisdiction=cp['config']['jurisdiction'],code_name=cp['identity']['name'],citation=r['heading'],full_text=r['semantic_html'],source_url='https://ecode360.com/'+ident,scrape_date=arts[r['raw_witnesses'][0]]['retrieved_at'],section_name=r['heading'].strip())
 for role in roles:
  labels=[]
  for n in chain:
   m=re.fullmatch(r'(?i)'+role+r'\.? (.+)',n['heading'].strip())
   if m and n['heading'].strip() not in labels:labels.append(n['heading'].strip())
  if len(labels)==1:expected[role]=labels[0];counts[role]+=1
  elif len(labels)>1:conflicts+=1
 if r['kind']=='section':
  m=re.fullmatch(r'(?:§|SECTION)\s*(\S+)\s*(.*)',r['heading'],re.S);require(bool(m),'Unlabelled section');expected['section_number']=m[1].rstrip(':');expected['section_name']=m[2]
 else:
  m=re.fullmatch(r'(?i)(?:sec\.|section\.?) (\S+)(?: (.*))?',r['heading'].strip(),re.S)
  if m and any(c.isdigit() for c in m[1]) and all(c.isalnum() or c in '.-()' for c in m[1]):expected['section_number']=m[1];expected['section_name']=(m[2] or '').removeprefix('- ')
 require(list(row)==fields and row==expected,'16-field mismatch '+ident)
 require(p['tables_html']==r['tables_html'] and p['notes_html']==r['notes_html'] and p['image_references']==r['image_references'] and p['links']==r['links'] and p['assets']==r['assets'],'Rich provenance '+ident)
 require(p['row_ordinal']==ordinal and p['raw_sha256']==arts[r['raw_witnesses'][0]]['sha256'],'Row/raw ordinal '+ident)
 require(p['image_placeholder_count']==r['image_placeholder_count']==row['full_text'].count('[IMAGE]'),'Image marker '+ident)
 require(p['parent_source_id']==r['parent_id'],'Parent source '+ident)
 images+=p['image_placeholder_count'];tables+=len(p['tables_html']);notes+=len(p['notes_html'])
 for witness in p['raw_witnesses']:
  a=arts[witness['path'].removeprefix('evidence/input/')];require(witness['sha256']==a['sha256'] and witness['retrieved_at']==a['retrieved_at'],'Raw provenance')
require(images==440 and tables==256 and notes==11704,'Body totals')
for prefix in ['', 'publications/albany-ecode-acquired-html/']:
 for kind,stem in [('fulltext','aggregate-fulltext'),('toc','aggregate-toc')]:
  j=Q/(prefix+kind+'.json' if prefix else stem+'.json');c=j.with_suffix('.csv');jr=load(j)['provisions'];cr=list(csv.DictReader(c.open(encoding='utf-8-sig',newline='')))
  require(c.read_bytes().startswith(b'\xef\xbb\xbf') and cr==jr,'CSV BOM/row values '+str(c))
  expect=rows if kind=='fulltext' else [dict(r,full_text='') for r in rows];require(jr==expect,'JSON/TOC '+str(j))
nodes=lines(Q/'source-nodes.jsonl');disp=lines(Q/'node-dispositions.jsonl');require(len(nodes)==len(disp)==len(inv)==3253,'Inventory/disposition closure')
require([n['locator']['guid'] for n in nodes]==['AL0934']+sorted(positions,key=lambda k:positions[k]),'Source node order')
for n,d in zip(nodes,disp):
 ident=n['locator']['guid'];require(n['publisher_descriptor']==inv[ident] and d['evidence']==ds[ident],'Literal inventory disposition '+ident)
 require(d['record_ids']==(['albany-ecode-acquired-html:'+ident] if ident in ir else []),'Disposition records '+ident)
require(cov['complete'] is False and len(cov['missing_assets'])==4 and cov['start_end_inventory_consistent'] is False,'Incomplete source gates lost')
vr=load(Q/'validation-report.json');rm=load(Q/'run-manifest.json')
require(vr['complete'] is False and vr['downstream_ready'] is False and rm['selected_publication_ready'] is False and rm['status']=='incomplete','Package gates changed')
require(rm['source_version']['closing_currency_raw'] is None and rm['source_version']['edition_complete'] is False,'False currentness')
result={'status':'PASS','final_manifest_sha256':h(B/'FINAL-V3-MANIFEST.json'),'selected_manifest_files_checked':567,'final_package_manifest_sha256':h(Q/'run-manifest.json'),'package_files':len(tree(Q)),'all_six_v2_v3_normalized_streams_and_401_raw_bytes_equal':True,'proof_sha256':h(B/'actual-standard-proof-v3/read-only-proof.json'),'actual_standard_report_sha256':h(fr),'input_files_all_bound':470,'all_source_runtime_before_after_maps_equal':True,'record_count':len(rows),'independent_fields_checked':len(rows)*16,'source_nodes_dispositions_checked':len(nodes),'source_order_basis':'Independent original publisher literal data-position census, not emitted IR order','image_markers':images,'tables':tables,'note_elements':notes,'nonblank_role_counts':counts,'repeated_role_conflicts_blank':conflicts,'complete':False,'missing_required_pdfs':cov['missing_assets'],'closing_checked':False,'network_image_native_parser_calls':0,'reader_or_producer_imports':0,'elapsed_seconds':time.monotonic()-t,'executed_source_sha256':h(pathlib.Path(__file__))}
(O/'final-package-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
