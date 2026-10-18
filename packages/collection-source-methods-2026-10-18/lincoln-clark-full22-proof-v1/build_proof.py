"""Package only after terminal producer + one successful strict verifier; no native parsing/network."""
import pathlib,json,hashlib,csv,collections,sys,shutil,importlib.metadata
P=pathlib.Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
status=load(P/'full-status.json');proof=load(P/'verify-status.json');assert status['exit_code']==proof['exit_code']==0 and not status['image_api_calls']and not proof['image_api_calls']and not proof['network_calls']
run=P/'run';cp=load(run/'checkpoint.json');cov=load(run/'coverage.json');inv=load(P/'clark-uncodified-inventory.json');capture=load(P/'capture-page-counts.json');assert len(cp['items'])==22 and cp['completed']
rows=[json.loads(s)for s in(run/'records.jsonl').read_text().splitlines()];assert len(rows)==198
aliases=[]
for src,item in zip(capture['documents'],cp['items']):
 assert src['url']==item['url']and src['sha256']==sha(run/item['raw_ref'])
 aliases.append({**src,'original_capture_path':'capture/'+src['raw_ref'],'final_run_path':'run/'+item['raw_ref'],'final_opening_receipt':'run/'+str(pathlib.Path(item['raw_ref']).with_suffix('.receipt.json')),'original_native_bytes_omitted_from_compact_mirror':True})
save(P/'capture-to-run-aliases.json',{'schema':1,'scope':'Authentic initial capture imported into standard producer, byte identity; originals preserved outside compact mirror','documents':aliases})
with(P/'ordinance-inventory.csv').open('w',newline='')as f:
 fields=['source_order','ordinance','title','adopted_literal','effective_literal','url','owner_source_url','owner_source_sha256','source_row_sha256'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(inv['uncodified_ordinances'])
q=[r['pdf_qualification']for r in rows];image_positions=[{'record_id':r['id'],'document_id':r['document_id'],'physical_page':r['physical_page'],'image_placeholder_count':r.get('image_placeholder_count',0)}for r in rows if r.get('image_placeholder_count')]
metadata={name:importlib.metadata.version(name)for name in ['beautifulsoup4','pypdf','pypdfium2','pdfplumber','pdfminer.six','Pillow']}
receipts=[load(p)for p in(run/'raw').glob('*.receipt.json')]
summary={'schema':1,'catalog_context':['67-b8a8412beb82','96-55b5a35f127a'],'clark':{'selected_scope':'Only22source-listeduncodifiedordinances5388–5409; source-owned printed dates, not countywidecurrency','documents':22,'physical_pages':198,'bytes_opening_native':sum(x['bytes']for x in capture['documents']),'source_word_count':sum(x['source_word_count']for x in q),'image_placeholder_count':sum(r.get('image_placeholder_count',0)for r in rows),'source_proven_no_glyph_pages':sum(x['text_glyph_comparison_applicability']=='not_applicable_source_has_no_text_glyph_characters'for x in q),'detected_tables':sum(x['detected_table_count']for x in q),'detected_cells':sum(x['detected_table_cells']for x in q),'independently_agreeing_cells':sum(x['independent_table_cells_agree']for x in q),'cell_disagreements':sum(x['detected_table_cells']-x['independent_table_cells_agree']for x in q),'page_review_conditions':{r['id']:r['pdf_qualification']['review_conditions']for r in rows if r['pdf_qualification']['review_conditions']},'file_pages_complete':cov['requested_coverage_complete'],'legal_semantic_coverage_complete':False,'jurisdiction_complete':False,'native_closing_pairs':len(cp['item_consistency']),'required_codified_publication':inv['codified_publication_reference'],'captured_ordinary_run_receipts':len(receipts)},'lincoln':{'source_url':load(P/'before.json')['catalog_entries'][0]['source_url'],'http_status':403,'refusal_receipt':'lincoln-comprehensive.receipt.json','full_inventory_acquired':False,'automatic_retry':False,'scope':'Exact observed route refusal; not every legitimate official route proven unavailable'},'proof':{'producer_exit':0,'strict_readonly_exit':0,'strict_source_file_count':proof['source_file_count'],'strict_source_unchanged':True,'all_live_image_api_calls':status['image_api_calls'],'strict_image_api_calls':proof['image_api_calls'],'strict_network_calls':proof['network_calls'],'full_source_tests':5,'python':sys.version,'dependencies':metadata,'runtime_scripts':cp['scripts'],'producer_driver_sha256':sha(P/'run_full.py'),'verifier_driver_sha256':sha(P/'verify_full.py')},'omitted_from_compact':['Redundant initialcapture native bytes, each bound by capture-to-run-aliases.json; original output remains unchanged','Transient cache/bytecode; none required for offline verification']}
save(P/'validation-summary.json',summary);save(P/'image-position-ledger.json',image_positions)
# Compact mirror, preserving original work and all standard final evidence.
mirror=P.parent/'lincoln-clark-full22-proof-v1';assert not mirror.exists(),'Refuse overwrite of proof mirror';mirror.mkdir()
for p in sorted(P.iterdir()):
 if p.name in ['capture','__pycache__','build.stdout','build.stderr']or p.name.startswith('.'):continue
 if p.is_dir():shutil.copytree(p,mirror/p.name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 else:shutil.copyfile(p,mirror/p.name)
# Historical capture checkpoint/config/receipts stay; only native .bin aliases omitted.
(mirror/'capture-metadata').mkdir()
for p in sorted((P/'capture').rglob('*')):
 if p.is_file()and p.suffix!='.bin':
  dest=mirror/'capture-metadata'/p.relative_to(P/'capture');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
files=[{'path':str(p.relative_to(mirror)),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(mirror.rglob('*'))if p.is_file()]
save(mirror/'MANIFEST.json',{'schema':1,'files':files,'file_count':len(files),'source':'Fresh22ordinarynativecapture→standardfull198producer→reallaterclosing→oneguardedreadonlyverification','scope':'file_pages only; legal/jurisdiction false','total_bytes':sum(x['bytes']for x in files)})
print(json.dumps({'mirror':str(mirror),'manifest_sha256':sha(mirror/'MANIFEST.json'),'files':len(files),'total_bytes':sum(x['bytes']for x in files),'largest_file':max(files,key=lambda x:x['bytes'])},indent=2))
