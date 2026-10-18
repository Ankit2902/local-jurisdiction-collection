"""All-body exact bridge plus independently enumerated original-source graphic labels."""
import argparse,collections,copy,hashlib,json,pathlib,re,time,urllib.parse
from bs4 import BeautifulSoup,NavigableString
ap=argparse.ArgumentParser();ap.add_argument('--revision',required=True);args=ap.parse_args()
P=pathlib.Path(__file__).resolve().parents[4];R=P/'github/local-jurisdiction-collection';O=pathlib.Path(__file__).resolve().parent;B=P/'outputs/collection-readiness-posta35cef8-2026-10-18/ecode';S=R/'packages/collection-source-recovery-2026-10-18/ecode/corrected-corpus-v3/evidence/input';D=B/('albany-statutory-classification-'+args.revision);C=B/('candidate-'+args.revision);t=time.monotonic()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().split('\n') if x]
def tree(p):return {str(f.relative_to(p)):h(f) for f in p.rglob('*') if f.is_file()}
oldfiles=tree(S);newfiles=tree(D);before={r['id']:r for r in lines(S/'records.jsonl')};after={r['id']:r for r in lines(D/'records.jsonl')};assert before.keys()==after.keys() and len(before)==3006
census=load(O/'source-census.json')['source_records'];actual=[];expected=[];context_transforms=[]
for x in census:
 ctx=BeautifulSoup(x['source_context_html'],'html.parser');changes=[]
 for anchor in ctx.find_all('a',href=True):
  if anchor['href'].startswith('#'):
   oldhref=anchor['href'];anchor['href']='https://ecode360.com/'+x['owner_id']+oldhref;changes.append([oldhref,anchor['href']])
 ch=hashlib.sha256(str(ctx).encode()).hexdigest()
 if changes:
  assert x['owner_id']=='7684806' and len(changes)==2
  context_transforms.append({'owner_id':x['owner_id'],'raw_source_context_sha256':x['context_sha256'],'processed_owner_context_sha256':ch,'existing_href_changes':changes})
 else:assert ch==x['context_sha256']
 expected.append((x['owner_id'],x['url'],x['label'],x['anchor_sha256'],ch,x['context_text']))
assert len(context_transforms)==1
soups={};source_anchors={};graphic=[];changedowners=[];all_new_metadata_owners=set()
def anchors_for(r):
 ident=r['id']
 if ident in source_anchors:return source_anchors[ident]
 rp=r['raw_witnesses'][0]
 if rp not in soups:soups[rp]=BeautifulSoup((S/rp).read_bytes(),'html.parser')
 matches=soups[rp].find_all(id=ident+'_content');assert len(matches)==1;body=matches[0]
 assert not [b for b in body.find_all(id=re.compile('^[0-9]+_content$')) if 'content'in b.get('class',[])]
 aa=[a for a in body.find_all('a',href=True) if a['href']];source_anchors[ident]=aa;return aa
for ident,a in before.items():
 b=after[ident];aa=copy.deepcopy(a);bb=copy.deepcopy(b);al=aa.pop('links');bl=bb.pop('links');assert aa==bb,('Nonlink/body drift',ident);assert len(al)==len(bl)
 cleaned=[]
 for index,(previous,current) in enumerate(zip(al,bl)):
  link=copy.deepcopy(current);e=link.pop('source_statutory_evidence',None)
  if e:
   assert e['source_owner_id']==ident and e['source_url']==link['url'] and e['source_label']==link['label'] and e['source_classes']==['statref']
   assert not e['anchor_has_download'] and not e['anchor_has_nonempty_mime']
   assert 'local-fragment href absolutization' in e['context_hash_lineage']
   actual.append((ident,link['url'],link['label'],e['source_anchor_html_sha256'],e['processed_owner_context_html_sha256'],e['source_context_text']));all_new_metadata_owners.add(ident)
  if previous['label']!=link['label']:
   srcs=anchors_for(a);assert len(srcs)==len(al);src=srcs[index];source_label=src.get_text(' ',strip=True);assert source_label==previous['label'];rawsha=hashlib.sha256(str(src).encode()).hexdigest()
   absolute=copy.deepcopy(src)
   for node in [absolute]+absolute.find_all('a',href=True):
    if node.get('href','').startswith('#'):node['href']='https://ecode360.com/'+ident+node['href']
   processsha=hashlib.sha256(str(absolute).encode()).hexdigest();assert link.pop('processed_owner_anchor_html_sha256')==processsha;assert 'literal [IMAGE]' in link.pop('label_policy')
   assert urllib.parse.urljoin(a['source_url'],src['href'])==previous['url']
   norm=copy.deepcopy(absolute);markers=0
   # All observed source graphic label contexts are img descendants and image-href anchors.
   assert not norm.find_all(['svg','picture','object','embed','input','source'])
   for img in norm.find_all('img'):
    assert not img.get('alt','');img.replace_with(NavigableString('[IMAGE]'));markers+=1
   typ=norm.get('type','').strip().lower();isimage=typ.startswith('image/') or bool(re.search(r'\.(?:png|jpe?g|gif|svg|webp|avif|bmp|tiff?|ico)(?:[?#]|$)',norm.get('href',''),re.I))
   if isimage:norm.append(NavigableString('[IMAGE]'));markers+=1
   assert markers>0 and norm.get_text(' ',strip=True)==link['label'],('Graphic source label mismatch',ident,index)
   graphic.append({'owner_id':ident,'link_ordinal':index,'source_url':previous['url'],'original_available_label':source_label,'normalized_label':link['label'],'IMAGE_positions':markers,'source_raw_path':a['raw_witnesses'][0],'source_raw_sha256':h(S/a['raw_witnesses'][0]),'original_source_anchor_sha256':rawsha,'processed_owner_anchor_sha256':processsha})
   link['label']=previous['label']
  assert link==previous,('Other link drift',ident,index)
  cleaned.append(link)
 if a!=b:changedowners.append(ident)
assert collections.Counter(expected)==collections.Counter(actual) and len(actual)==21
assert len(graphic)>0
for n in ['records.csv','inventory.json','dispositions.json','image-omissions.json']:assert h(S/n)==h(D/n),n
assert tree(S/'raw')==tree(D/'raw') and len(tree(S/'raw'))==401
oc=load(S/'coverage.json');nc=load(D/'coverage.json')
for k in ['identity','missing_assets','errors','start_end_inventory_consistent','publication_text_complete','attachments_complete','edition_complete','jurisdiction_complete','complete','resumable','inventory_nodes','owned_content_nodes','normalized_records','disposition_counts','image_reference_urls','intentional_image_omissions','required_assets','acquired_assets','missing_ids','extra_ids','unresolved_ids','conflicting_duplicate_bodies']:assert oc[k]==nc[k],k
assert len(oc['unresolved_links'])==21 and nc['unresolved_links']==[] and len(nc['missing_assets'])==4 and nc['complete'] is False
ol=load(S/'link-ledger.json');nl=load(D/'link-ledger.json');assert len(ol)==len(nl);changes=[]
for a,b in zip(ol,nl):
 aa=copy.deepcopy(a);bb=copy.deepcopy(b);e=bb.pop('source_statutory_evidence',None)
 if aa['classification']!=bb['classification']:
  assert aa['classification']=='unresolved_hyperlink' and bb['classification']=='external_statutory_reference' and e;changes.append([bb['owner_id'],bb['url'],bb['label']]);aa['classification']=bb['classification']
 if aa['label']!=bb['label']:
  assert 'processed_owner_anchor_html_sha256'in bb and 'label_policy'in bb;bb.pop('processed_owner_anchor_html_sha256');bb.pop('label_policy');bb['label']=aa['label']
 assert aa==bb,('Unexpected ledger change',aa,bb)
assert len(changes)==21
assert tree(S)==oldfiles and tree(D)==newfiles
report={'passed':True,'revision':args.revision,'canonical_body_text_tables_notes_IDs_all_other_fields_exact':3006,'new_statutory_metadata_occurrences':21,'statutory_metadata_owners':len(all_new_metadata_owners),'graphic_label_changes':len(graphic),'graphic_label_owners':len({x['owner_id'] for x in graphic}),'graphic_label_source_IMAGE_positions':sum(x['IMAGE_positions'] for x in graphic),'graphic_label_original_source_witnesses':graphic,'all_changed_record_owners':changedowners,'context_hashes_direct_raw':20,'exact_existing_processed_context_transform':context_transforms,'all_401_raw_bytes_equal':True,'four_unchanged_streams':['records.csv','inventory.json','dispositions.json','image-omissions.json'],'ledger_only21classification_changes':changes,'four_missingPDF403_closing_and_all_falsegates_preserved':True,'external_laws_acquired_or_certified':False,'old_records_sha256':h(S/'records.jsonl'),'new_records_sha256':h(D/'records.jsonl'),'original_input_files_unchanged':len(oldfiles),'derivative_files_unchanged':len(newfiles),'adapter_sha256':h(C/'adapters.py'),'engine_sha256':h(C/'engine.py'),'producer_imports_network_image_native_operations':0,'executed_source_sha256':h(pathlib.Path(__file__)),'seconds':time.monotonic()-t}
(O/('final-derivative-review-'+args.revision+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['graphic_label_original_source_witnesses','all_changed_record_owners','ledger_only21classification_changes']},indent=2))
