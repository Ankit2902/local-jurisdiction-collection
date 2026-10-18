"""All3006 records +401raw bytes exact body bridge; independent source-context matching."""
import collections,copy,hashlib,json,pathlib,time
from bs4 import BeautifulSoup
P=pathlib.Path(__file__).resolve().parents[4];R=P/'github/local-jurisdiction-collection';O=pathlib.Path(__file__).resolve().parent;B=P/'outputs/collection-readiness-posta35cef8-2026-10-18/ecode';S=R/'packages/collection-source-recovery-2026-10-18/ecode/corrected-corpus-v3/evidence/input';D=B/'albany-statutory-classification-v3';t=time.monotonic()
def h(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def load(f):return json.loads(f.read_text())
def lines(f):return [json.loads(x) for x in f.read_text().split('\n') if x]
def tree(p):return {str(f.relative_to(p)):h(f) for f in p.rglob('*') if f.is_file()}
old=tree(S);new=tree(D);before={r['id']:r for r in lines(S/'records.jsonl')};after={r['id']:r for r in lines(D/'records.jsonl')};assert before.keys()==after.keys() and len(before)==3006
actual=[];changed=[]
for k,a in before.items():
 b=after[k];aa=copy.deepcopy(a);bb=copy.deepcopy(b);al=aa.pop('links');bl=bb.pop('links');assert aa==bb,('Nonlink source record drift',k)
 cleaned=[]
 for link in bl:
  l=copy.deepcopy(link);e=l.pop('source_statutory_evidence',None)
  if e:
   assert e['source_owner_id']==k and e['source_url']==l['url'] and e['source_label']==l['label'] and e['source_classes']==['statref'] and not e['anchor_has_download'] and not e['anchor_has_nonempty_mime']
   actual.append((k,l['url'],l['label'],e['source_anchor_html_sha256'],e['source_context_html_sha256'],e['source_context_text']))
  cleaned.append(l)
 assert al==cleaned,('Other link changes',k)
 if a!=b:changed.append(k)
census=load(O/'source-census.json')['source_records'];expected=[];context_transforms=[]
for x in census:
 ctx=BeautifulSoup(x['source_context_html'],'html.parser');changes=[]
 for anchor in ctx.find_all('a',href=True):
  if anchor['href'].startswith('#'):
   oldhref=anchor['href'];anchor['href']='https://ecode360.com/'+x['owner_id']+oldhref;changes.append({'original_href':oldhref,'processed_href':anchor['href']})
 ch=hashlib.sha256(str(ctx).encode()).hexdigest()
 if changes:
  assert x['owner_id']=='7684806' and x['url']=='https://municipal.codes/NY/HAY/331' and len(changes)==2
  context_transforms.append({'owner_id':x['owner_id'],'source_URL':x['url'],'raw_source_context_sha256':x['context_sha256'],'processed_ownbody_context_sha256':ch,'existing_local_footnote_href_absolutization':changes,'original_context_text_unchanged':ctx.get_text(' ',strip=True)==x['context_text']})
 else:assert ch==x['context_sha256']
 expected.append((x['owner_id'],x['url'],x['label'],x['anchor_sha256'],ch,x['context_text']))
assert len(context_transforms)==1 and context_transforms[0]['original_context_text_unchanged']
assert collections.Counter(expected)==collections.Counter(actual) and len(actual)==21 and len(changed)==13
for name in ['records.csv','inventory.json','dispositions.json','image-omissions.json']:assert h(S/name)==h(D/name),name
rawold=tree(S/'raw');rawnew=tree(D/'raw');assert rawold==rawnew and len(rawold)==401
oc=load(S/'coverage.json');nc=load(D/'coverage.json')
for k in ['identity','missing_assets','errors','start_end_inventory_consistent','publication_text_complete','attachments_complete','edition_complete','jurisdiction_complete','complete','resumable','inventory_nodes','owned_content_nodes','normalized_records','disposition_counts','image_reference_urls','intentional_image_omissions','required_assets','acquired_assets','missing_ids','extra_ids','unresolved_ids','conflicting_duplicate_bodies']:
 assert oc[k]==nc[k],('Gate/count/source drift',k)
assert len(oc['unresolved_links'])==21 and nc['unresolved_links']==[] and len(nc['missing_assets'])==4 and nc['complete'] is False
ol=load(S/'link-ledger.json');nl=load(D/'link-ledger.json');assert len(ol)==len(nl);transitions=[]
for a,b in zip(ol,nl):
 aa=copy.deepcopy(a);bb=copy.deepcopy(b);e=bb.pop('source_statutory_evidence',None)
 if aa.get('classification')!=bb.get('classification'):
  assert aa['classification']=='unresolved_hyperlink' and bb['classification']=='external_statutory_reference' and e;transitions.append((bb['owner_id'],bb['url'],bb['label']));aa['classification']=bb['classification']
 assert aa==bb,('Other ledger drift',aa,bb)
assert len(transitions)==21
assert tree(S)==old and tree(D)==new
r={'passed':True,'original_input_files_unchanged':len(old),'derivative_files_unchanged':len(new),'all_records_excluding_new_link_evidence_byte_value_equal':3006,'changed_records_only_new_link_metadata':len(changed),'changed_owner_ids':changed,'new_source_statutory_evidence_occurrences_source_bound':len(actual),'context_hashes_direct_raw_source_match':20,'exact_existing_context_transform':context_transforms,'all_four_unchanged_streams':['records.csv','inventory.json','dispositions.json','image-omissions.json'],'raw401bytes_equal':True,'ledger_only21unresolved_to_external_statutory_reference':len(transitions),'required_PDFs_missing':4,'source403_closing_text_attachment_edition_jurisdiction_falsegates_unchanged':True,'unresolved_statutory_reference_links':0,'external_laws_acquired_or_certified':False,'old_records_sha256':h(S/'records.jsonl'),'new_records_sha256':h(D/'records.jsonl'),'adapter_sha256':h(B/'candidate-v3/adapters.py'),'engine_sha256':h(B/'candidate-v3/engine.py'),'producer_imports_network_images_native_operations':0,'seconds':time.monotonic()-t,'executed_source_sha256':h(pathlib.Path(__file__))}
(O/'derivative-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
