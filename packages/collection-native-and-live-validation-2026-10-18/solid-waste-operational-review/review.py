"""Independent capture-backed production workflow/export review; zero native reparse."""
import contextlib,copy,csv,gzip,hashlib,importlib,io,json,pathlib,socket,sys,tempfile,time,unittest
from unittest.mock import patch
from PIL import Image
from pypdf.generic import EncodedStreamObject,DecodedStreamObject
ROOT=pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');PACKET=ROOT/'outputs/collection-readiness-post1997ee1-2026-10-17/solid-waste-production-integration-candidate-v1';HERE=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(PACKET/'candidate'))
n=importlib.import_module('collectors.encodeplus.native_document');c=importlib.import_module('collectors.encodeplus.collect');s=importlib.import_module('collectors.encodeplus.solid_waste_logical');module=importlib.import_module('collectors.encodeplus.test_solid_waste_logical')
E=PACKET/'candidate/collectors/encodeplus';F=E/'fixtures/solid-waste-logical';sha=lambda b:hashlib.sha256(b).hexdigest();cfg=json.loads((E/'configs/native-82-4b983dc51ab6.json').read_text());data=(F/'source.pdf').read_bytes();rows=[json.loads(l) for l in gzip.decompress((F/'captured-records.jsonl.gz').read_bytes()).decode().splitlines()];details=json.loads((F/'captured-details.json').read_text());calls=[];operations=[]
def no(*a,**kw):calls.append('network/image/native-reparse');raise AssertionError('No network/images/new native parse')
@contextlib.contextmanager
def guards():
 with contextlib.ExitStack() as stack:
  for obj,key in [(socket,'socket'),(socket,'create_connection'),(Image,'open'),(s,'build_records')]:stack.enter_context(patch.object(obj,key,no))
  for cls in [EncodedStreamObject,DecodedStreamObject]:
   original=cls.get_data
   def imageguard(self,*a,_original=original,**kw):
    if str(self.get('/Subtype','')).lower()=='/image':return no()
    return _original(self,*a,**kw)
   stack.enter_context(patch.object(cls,'get_data',imageguard))
  yield

def workflow():
 fetches=[]
 def fake_fetch(url,path,timeout=120):
  assert url==cfg['url'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);meta={'url':url,'http_status':200,'sha256':sha(data),'challenge':False,'headers':{'Content-Type':'application/pdf'},'scope':'Independent offline capture-backed transfer fixture; no live request'};path.with_name(path.name+'.receipt.json').write_text(json.dumps(meta));fetches.append(str(path.relative_to(path.parents[1])));return data,meta
 with tempfile.TemporaryDirectory() as td,guards(),patch.object(c,'fetch',side_effect=fake_fetch),patch.object(n,'page_records',side_effect=lambda *a,**k:(copy.deepcopy(rows),copy.deepcopy(details))):
  base=pathlib.Path(td);fresh=base/'fresh';result=n.collect(copy.deepcopy(cfg),fresh)
  assert result['native_document_complete'] and result['physical_pages']==6 and result['normalized_record_count']==88 and result['publication_text_complete'] and result['source_logical_structure_qualified'];assert not any(result[k] for k in ['attachments_complete','publication_complete','edition_complete','jurisdiction_complete','required_external_legal_dependencies_complete']);assert 'Own exact native document text' in result['publication_text_scope'];assert result['pdf_details']['pdf_table_semantics_complete']==False
  assert len(fetches)==2;repeat=n.collect(copy.deepcopy(cfg),fresh,resume=True);assert repeat==result and len(fetches)==2
  (HERE/'standard-collect-verify.json').write_text(json.dumps(result,indent=2)+'\n');operations.append({'case':'fresh_standard_collect_and_finished_resume','passed':True,'simulated_transfer_calls':2,'actual_network_calls':0,'physical_pages':6,'primary_records':88,'dependencies_and_common_publication_false':True})
  interrupted=base/'interrupted';r=n.collect(copy.deepcopy(cfg),interrupted,interrupt_after_start=True);assert not r['native_document_complete'];assert json.loads((interrupted/'checkpoint.json').read_text())['phase']=='interrupted';before=len(fetches);r=n.collect(copy.deepcopy(cfg),interrupted,resume=True);assert r['native_document_complete'] and len(fetches)==before+1;operations.append({'case':'interrupt_after_normalize_then_resume','passed':True,'original_start_reused':True,'simulated_resume_end_transfers':1})
  # Source corruption cannot be promoted by the standard verifier, with same retained parser IR.
  (interrupted/'raw/start.pdf').write_bytes(data+b'\n');r=n.verify(interrupted);assert not r['native_document_complete'] and r['errors'];operations.append({'case':'actual_retained_source_byte_corruption','passed':True,'errors':r['errors']})
  # No route/identity fallback on the source-specific branch.
  for k,v in [('url','https://wrong.invalid/book.pdf'),('id','wrong'),('state','MO'),('expected_pages',88),('expected_sha256','0'*64)]:
   bad=copy.deepcopy(cfg);bad[k]=v
   try:s.matches(data,bad)
   except AssertionError:pass
   else:raise AssertionError('Wrongsource accepted: '+k)
  operations.append({'case':'exact_source_config_identity_refusals','passed':True})
  failed=base/'refusal'
  with patch.object(c,'fetch',side_effect=RuntimeError('simulated persisted access refusal; no request')):r=n.collect(copy.deepcopy(cfg),failed)
  assert not r['native_document_complete'] and r['errors'];assert json.loads((failed/'checkpoint.json').read_text())['phase']=='failed';operations.append({'case':'transport_refusal_no_native_acceptance','passed':True,'actual_requests':0,'errors':r['errors']})

def mixed():
 base=[json.loads(l) for l in gzip.decompress((PACKET/'source-mixed636.jsonl.gz').read_bytes()).decode().splitlines()];new=[json.loads(l) for l in (PACKET/'derivative-mixed718/records.jsonl').read_text().splitlines()];assert len(base)==636 and len(new)==718
 native=[r for r in base if r['raw_sha256']==cfg['expected_sha256']];logical=[r for r in new if r.get('unit')=='pdf_logical_unit'];others_before=[r for r in base if r['raw_sha256']!=cfg['expected_sha256']];others_after=[r for r in new if r.get('unit')!='pdf_logical_unit'];assert len(native)==6 and len(logical)==88 and len(others_before)==len(others_after)==630 and others_before==others_after
 assert logical[0]['mixed_source_diagnostic_lineage']['original_asset_page_records']==native
 images=lambda rs:[(r['id'],b) for r in rs for b in r.get('ordered_blocks',[]) if b['kind']=='image_placeholder'];assert images(base)==images(new) and len(images(new))==201;assert sum('canonical_structure_selection' in r for r in others_after)==17
 out=n.outputs(new)
 for name,body in out.items():assert body==(PACKET/'derivative-mixed718'/name).read_bytes(),'Export replay drift '+name
 csvrows=list(csv.DictReader(io.StringIO(out['records.csv'].decode())));assert len(csvrows)==718
 for r,x in zip(new,csvrows):
  assert x['text']==r['text'] and x['id']==r['id']
  if r.get('unit')=='pdf_logical_unit':assert x['physical_page']=='' and json.loads(x['source_pages'])==r['source_pages']
  else:assert x['physical_page']==str(r['physical_page'])
 return {'passed':True,'records':718,'unchanged_others':630,'logical':88,'physical_replaced':6,'canonical_selections_other_preserved':17,'image_ownership_positions_preserved':201,'all_export_files_recomputed_byte_equal':True,'source_sha256':sha((PACKET/'source-mixed636.jsonl.gz').read_bytes())}

before={str(p.relative_to(E)):sha(p.read_bytes()) for p in E.rglob('*') if p.is_file() and '__pycache__' not in p.parts};start=time.monotonic();suite=unittest.defaultTestLoader.loadTestsFromModule(module)
with guards(),(HERE/'nine-tests.log').open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
assert result.wasSuccessful() and result.testsRun==9
workflow()
with guards():mixed_result=mixed()
after={str(p.relative_to(E)):sha(p.read_bytes()) for p in E.rglob('*') if p.is_file() and '__pycache__' not in p.parts};assert before==after and not calls
report={'passed':True,'scope':'Independent exact candidate code+9fault rerun+standard fresh collect/interruption/resume/verify with mocked transfer and retained actual IR; mixed718 canonical export reserialization. No native reparse, no live requests.','candidate_runtime_files':before,'candidate_files_unchanged':True,'source_sha256':sha(data),'tests':9,'workflow_cases':operations,'mixed':mixed_result,'forbidden_calls':calls,'seconds':time.monotonic()-start,'own_native_text_qualified':True,'external_dependencies_edition_jurisdiction_publication_complete':False,'limitation':'The generic publication_text_complete boolean is explicitly scoped by publication_text_scope to own native text; it is not dependency closure. Legacypdf_table_semantics_complete remainsfalse/commonacceptancefalse. Full6source/glyph qualification is prior independent proof, not repeated by this review.'}
(HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='candidate_runtime_files'},indent=2))
