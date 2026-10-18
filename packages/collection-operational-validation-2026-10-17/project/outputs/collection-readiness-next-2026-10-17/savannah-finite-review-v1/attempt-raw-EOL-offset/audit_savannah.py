"""Bounded independent Savannah source/native/qualification review; no network/pixels."""
import sys;sys.dont_write_bytecode=True
import json,hashlib,copy,tempfile,shutil,socket,io,re
from pathlib import Path
from html.parser import HTMLParser
from unittest.mock import patch,PropertyMock
from pypdf import PdfReader,PageObject
from pypdf.generic import EncodedStreamObject,DecodedStreamObject
B=Path(__file__).resolve().parent;ROOT=B.parents[2];EP=ROOT/'outputs/collection-readiness-next-2026-10-17/encodeplus';POST=EP/'post-91f6c59';C=POST/'final-primary-candidate';sys.path.insert(0,str(C))
from collectors.encodeplus import savannah_reference as ar,savannah_empty_qualification as em
from collectors.encodeplus.publication_references import reconcile,qualify_bound_document
from collectors.encodeplus.util import hash_json
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def deny(*a,**kw):raise AssertionError('Network/image access prohibited')
socket.socket.connect=deny;socket.create_connection=deny
checks=[]
def check(name,condition):assert condition,name;checks.append({'name':name,'passed':True})
A=C/'collectors/encodeplus/fixtures/savannah-adopted-reference';E=C/'collectors/encodeplus/fixtures/savannah-source-empty6451';q=ar.ALTERNATIVE;cfg=read(A/'config.json');owner=read(A/'owner.json')
original=EP/'savannah-primary';raw=(original/q['source_owner_raw_path']).read_bytes();text=raw.decode('utf-8');binding=read(POST/'savannah-alternative-discovery/owner-source-binding.json');row=(POST/'savannah-alternative-discovery/owner-6459-observed-row.html').read_text()
check('original_parent_response_SHA_exact',sha(raw)==q['owner']['raw_sha256']==binding['source_sha256'])
check('exact_native_source_table_row',text[binding['exact_text_slice_start']:binding['exact_text_slice_end']]==row and sha(row.encode())==binding['row_sha256'])
class Ancestors(HTMLParser):
 def __init__(self):super().__init__();self.stack=[]
 def handle_starttag(self,tag,attrs):
  if tag=='section':self.stack.append(dict(attrs).get('data-secid'))
 def handle_endtag(self,tag):
  if tag=='section' and self.stack:self.stack.pop()
p=Ancestors();p.feed(text[:binding['exact_text_slice_start']]);check('table_row_owned_by_actual6459_section','6459' in p.stack and p.stack[-1]=='6459')
check('row_literal_label_section_and_range',q['original_literal_href'] in row and '4-12-2018(3)' in row and '1 Added' in row and '8-3370&mdash;8-3379' in row)
old=original/q['original_failure']['raw_path'];oldmeta=old.with_name(old.name+'.receipt.json');receipt=read(oldmeta);check('old404_body_and_pinned_refusal_receipt_retained',old.is_file() and sha(oldmeta.read_bytes())==q['original_failed_receipt_sha256'] and receipt['http_status']==404)
search=A/'observed-url-provenance.json';check('full_UUID_observed_URL_and_receipt_bound',sha(search.read_bytes())==q['search_provenance_sha256'] and read(search)['result_url']==q['url'] and sha((A/'adopted-2018-04-12-3.pdf.receipt.json').read_bytes())==q['native_receipt_sha256'])
origE=EncodedStreamObject.get_data;origD=DecodedStreamObject.get_data;image_calls=[]
def image_guard(fn):
 def wrapped(obj,*args,**kwargs):
  if str(obj.get('/Subtype',''))=='/Image':image_calls.append(str(obj));raise AssertionError('Image stream decode')
  return fn(obj,*args,**kwargs)
 return wrapped
with patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=deny),patch.object(EncodedStreamObject,'get_data',image_guard(origE)),patch.object(DecodedStreamObject,'get_data',image_guard(origD)):
 native=(A/'adopted-2018-04-12-3.pdf').read_bytes();reader=PdfReader(io.BytesIO(native),strict=True);texts=[p.extract_text() or '' for p in reader.pages];joined='\n'.join(texts)
 check('actual_native_city_article_sections_adoption',len(texts)==4 and 'City of Savannah, Georgia' in joined and 'Article Q.' in joined and all('8-'+str(n) in joined for n in range(3370,3380)) and re.search(r'ADOPTED AND APPROVED:\s*APRIL\s+12,\s*2018',joined) is not None)
 check('all_native_pages_exact_content_pins',sha(native)==q['expected_sha256'] and [sha(''.join(c.casefold() for c in t if c.isalnum()).encode()) for t in texts]==q['page_text_sha256'])
 records={'6459':copy.deepcopy(owner)};projected=reconcile(records,cfg);check('only_reference_disposition_changes_and_original_link_retained',projected['6459']['assets'][0]['url']==q['url'] and projected['6459']['links']==owner['links'] and qualify_bound_document(projected,q['url'],native)==q)
 full=read(E/'full-source-record.json');source=read(E/'source-record.json');before=(E/'source-before.html').read_bytes();after=(E/'source-after.html').read_bytes();w=em.QUALIFICATION
 check('empty_full_and_fresh_owned_body_exact',source['body_sha256']==full['body_sha256']==w['fresh_selected_body_sha256'] and sha(before)==sha(after)==w['fresh_source_before_after_sha256'] and full['text']=='' and source['text']=='')
 small=(E/'native/attempt-0/publication.pdf').read_bytes();r2=PdfReader(io.BytesIO(small),strict=True);t2=[p.extract_text() or '' for p in r2.pages]
 check('empty_native_two_pages_exact_heading_header_pagination_witness',sha(small)==w['selected_native_sha256'] and len(t2)==2 and t2==w['selected_native_text'] and [sha(t.encode()) for t in t2]==w['selected_native_page_text_sha256'])
 nativeReceipt=read(E/'native/attempt-0/publication.pdf.receipt.json');check('empty_native_control6451_receipt_and_toc_scope',nativeReceipt['http_status']==200 and nativeReceipt['url'].endswith('tocid=001.004.008.004.009.009.011') and nativeReceipt['sha256']==w['selected_native_sha256'])
 check('all29_empty_source_native_witness_pins',len(w['fixture_witnesses'])==29 and all(sha((C/'collectors/encodeplus'/f['path']).read_bytes())==f['sha256'] for f in w['fixture_witnesses']))
 qual=em.qualify({'6451':copy.deepcopy(full)},read(E/'config.json'))['6451'];check('exact_empty_kind_only_source_disposition_no_fabricated_text',qual['kind']=='confirmed_source_empty' and qual['text']=='' and qual['path']==full['path'] and set(k for k in full if full[k]!=qual[k])=={'kind','disposition'})
 # Root-requested actual-source/config/owner/native refusal mutations; copies only.
 for label,field in [('owner','id'),('body','body_sha256'),('raw','raw_sha256'),('hierarchy','path')]:
  mutated=copy.deepcopy(owner);mutated[field]='altered';out=reconcile({'6459':copy.deepcopy(mutated)},cfg);check('adopted_'+label+'_mutation_refuses',out['6459']==mutated)
 mutatedcfg=dict(cfg,identity='Other publication');check('adopted_config_mutation_refuses',reconcile({'6459':copy.deepcopy(owner)},mutatedcfg)['6459']==owner)
 try:qualify_bound_document(projected,q['url'],native+b'altered')
 except ValueError:refused=True
 else:refused=False
 check('adopted_native_mutation_refuses',refused)
 for label,field in [('owner','id'),('body','body_sha256'),('raw','raw_sha256'),('hierarchy','path')]:
  mutated=copy.deepcopy(full);mutated[field]='altered';check('empty_'+label+'_mutation_refuses',em.qualify({'6451':copy.deepcopy(mutated)},read(E/'config.json'))['6451']==mutated)
 check('empty_config_mutation_refuses',em.qualify({'6451':copy.deepcopy(full)},dict(read(E/'config.json'),identity='Different'))['6451']==full)
 for relative in ['source-before.html','native/attempt-0/publication.pdf']:
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);dest=td/'fixtures/savannah-source-empty6451';shutil.copytree(E,dest);fp=dest/relative;fp.write_bytes(fp.read_bytes()+b' altered source')
   with patch.object(em,'HERE',td):out=em.qualify({'6451':copy.deepcopy(full)},read(E/'config.json'))
   check('empty_changed_'+relative+'_refuses',out['6451']==full)
check('no_image_stream_decode_or_network',not image_calls)
modules={n:sha((C/'collectors/encodeplus'/n).read_bytes()) for n in ('savannah_reference.py','savannah_empty_qualification.py','publication_references.py','test_savannah_reference.py','test_savannah_empty.py')}
report={'schema_version':1,'passed':True,'candidate':str(C.relative_to(ROOT)),'source_hashes':modules,'check_count':len(checks),'checks':checks,'network_requests':0,'image_stream_decode_calls':image_calls,'render_OCR_extraction_operations':0,'source_table_ancestor_ids':p.stack,'adopted_alternative_sha256':q['expected_sha256'],'heading_only_native_sha256':w['selected_native_sha256'],'no_generic_heading_or_empty_waiver':True,'whole_publication_live_complete_claimed':False,'scope':'Selected actualsource/native witnesses and exact finite qualification only; exhaustive5674/707 replay and final50suite are owner proofs, not repeated here.'};(B/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
