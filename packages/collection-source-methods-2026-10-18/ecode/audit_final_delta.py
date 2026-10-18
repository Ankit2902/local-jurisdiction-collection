import sys
sys.dont_write_bytecode=True
import argparse,json,hashlib,collections,re
from pathlib import Path
from bs4 import BeautifulSoup
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);args=ap.parse_args();B=Path(__file__).resolve().parent;O=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection/packages/collection-source-recovery-2026-10-18/ecode/corrected-corpus-v3/evidence/input');N=args.input.resolve();L=lambda p:[json.loads(x) for x in p.read_text().split('\n') if x];old=L(O/'records.jsonl');new=L(N/'records.jsonl');assert len(old)==len(new)==3006;deltas=[];count=0;labels=0;links=0;placeholder_spacing=[]
for a,b in zip(old,new):
 assert a['id']==b['id'];changes=[k for k in a if a[k]!=b[k]]
 if changes:assert changes==['links'];deltas.append({'owner_id':a['id'],'changed_fields':changes})
 assert len(a['links'])==len(b['links']);anchors=[x for x in BeautifulSoup(a['content_html'],'html.parser').find_all('a',href=True) if x.get('href')];assert len(anchors)==len(b['links']),(a['id'],len(anchors),len(b['links']))
 for before,after,anchor in zip(a['links'],b['links'],anchors):
  links+=1;assert before['url']==after['url'] and before['owner_id']==after['owner_id'];visible=anchor.get_text(' ',strip=True)
  if after['label']!=visible:
   image_spacing=lambda text:re.sub(r'\s*\[IMAGE\]\s*','[IMAGE]',text)
   assert after['label'].count('[IMAGE]')==visible.count('[IMAGE]') and image_spacing(after['label'])==image_spacing(visible),(a['id'],after['label'],visible)
   placeholder_spacing.append({'owner_id':a['id'],'url':after['url'],'metadata_label':after['label'],'serialized_body_anchor_label':visible,'projection':'Only whitespace directly adjacent to inserted literal IMAGE markers; no ordinary-text/case normalization'})
  if before['label']!=after['label']:labels+=1;assert '[IMAGE]' in after['label'];assert re.fullmatch('[0-9a-f]{64}',after['processed_owner_anchor_html_sha256'])
  if 'source_statutory_evidence' in after:count+=1
assert count==21
stable={}
for name in ['inventory.json','dispositions.json','image-omissions.json','records.csv']:
 assert (O/name).read_bytes()==(N/name).read_bytes();stable[name]=hashlib.sha256((N/name).read_bytes()).hexdigest()
a=json.loads((O/'coverage.json').read_text());b=json.loads((N/'coverage.json').read_text());unchanged=['required_assets','missing_assets','errors','publication_text_complete','attachments_complete','edition_complete','start_end_inventory_consistent','complete','resumable','jurisdiction_complete','missing_ids','extra_ids','unresolved_ids'];assert all(a[k]==b[k] for k in unchanged);assert len(a['unresolved_links'])==21 and b['unresolved_links']==[] and b['required_assets']==4
ol=json.loads((O/'link-ledger.json').read_text());nl=json.loads((N/'link-ledger.json').read_text());assert len(ol)==len(nl);classdelta=[]
for x,y in zip(ol,nl):
 if x['classification']!=y['classification']:assert x['classification']=='unresolved_hyperlink' and y['classification']=='external_statutory_reference';classdelta.append({'owner_id':y['owner_id'],'url':y['url'],'old':x['classification'],'new':y['classification'],'source_evidence':y['source_statutory_evidence']})
assert len(classdelta)==21
raws={str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (O/'raw').rglob('*') if p.is_file()};assert raws=={str(p.relative_to(N)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (N/'raw').rglob('*') if p.is_file()}
# Match distinct occurrences, not first-match-by-URL. One processed context has
# two preexisting local fragment href absolutizations; retain that lineage.
census=json.loads((B/'corrected-statref-source-census.json').read_text())['records'];groups=collections.defaultdict(list)
for item in classdelta:groups[(item['owner_id'],item['url'])].append(item['source_evidence'])
direct=0;transformed=[]
for row in census:
 e=groups[(row['owner_id'],row['url'])][row['owner_URL_label_occurrence_ordinal']];assert e['source_context_text']==row['source_parent_context'];assert e['source_anchor_html_sha256']==row['source_anchor_html_sha256']
 if e['processed_owner_context_html_sha256']==row['source_context_html_sha256']:direct+=1;continue
 doc=BeautifulSoup((O/row['raw_path']).read_bytes(),'html.parser');root=doc.find(id=row['owner_id']+'_content');matches=[]
 for anchor in root.find_all('a',href=True):
  nearest=next((p for p in anchor.parents if p.get('id') and re.fullmatch(r'[0-9]+_content',p['id'])),None)
  if nearest is root and anchor['href']==row['url'] and anchor.get_text(' ',strip=True)==row['label']:matches.append(anchor)
 anchor=matches[row['owner_URL_label_occurrence_ordinal']];context=anchor.find_parent(['p','li','dd','td','div']) or anchor.parent;clone=BeautifulSoup(str(context),'html.parser');updates=[]
 for local in clone.select('a[href^="#"]'):updates.append({'original_href':local['href'],'processed_href':'https://ecode360.com/'+row['owner_id']+local['href']});local['href']=updates[-1]['processed_href']
 assert hashlib.sha256(str(clone).encode()).hexdigest()==e['processed_owner_context_html_sha256'];transformed.append({'owner_id':row['owner_id'],'url':row['url'],'source_raw_context_sha256':row['source_context_html_sha256'],'processed_owner_context_sha256':e['processed_owner_context_html_sha256'],'preexisting_local_fragment_href_absolutizations':updates})
assert direct==20 and len(transformed)==1 and len(transformed[0]['preexisting_local_fragment_href_absolutizations'])==2
report={'passed':True,'canonical_bodies_byte_exact':3006,'rich_record_changes':deltas,'added_link_source_evidence':count,'all_source_link_URLs_and_owners_unchanged':links,'image_normalized_label_changes':labels,'all_labels_preserve_canonical_anchor_text_and_IMAGE_positions':True,'placeholder_adjacency_spacing_projection':placeholder_spacing,'raw_hashes_identical':len(raws),'stable_artifacts':stable,'classification_changes':classdelta,'raw_context_hash_direct_matches':direct,'processed_context_hash_lineage':transformed,'unchanged_coverage_fields':{k:b[k] for k in unchanged},'old_unresolved_statrefs':21,'new_unresolved_statrefs':0,'required_PDFs':4,'complete':False,'external_law_acquired':False,'new_requests':0};args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k in ['passed','canonical_bodies_byte_exact','added_link_source_evidence','all_source_link_URLs_and_owners_unchanged','image_normalized_label_changes','raw_hashes_identical','raw_context_hash_direct_matches','required_PDFs','complete']}))
