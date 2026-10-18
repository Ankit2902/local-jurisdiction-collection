"""Compact source-schema fault fixtures; actual full Cleveland proof is separate."""
import sys
sys.dont_write_bytecode=True
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import american_legal_html as al
from common import canonical,encoded,sha,artifacts

class SourceFixture:
 def __init__(self,root):
  self.root=root;self.requests={};self.identity={'client_slug':'fixture','jurisdiction':'Fixture','state':'OH','version_uuid':'v1','version_name':'2026 S-1','currency_info':'Current through fixture date','code_uuid':'book1','code_slug':'fixture_oh','code_title':'Fixture Code','is_pdf':False}
  self.nodes=[self.node('1',1,'PART I: CODE',None,True),self.node('2',2,'CHAPTER 1 - RULES','1',True),self.node('3',3,'1.01 Rule.','2',False),self.node('4',4,'1.02 Reserved.','2',False)]
  self.nodes[0]['path']=['PART I: CODE'];self.nodes[1]['path']=self.nodes[0]['path']+[self.nodes[1]['heading']]
  for n in self.nodes[2:]:n['path']=self.nodes[1]['path']+[n['heading']]
  self.inv={'nodes':self.nodes,'complete':True,'pending':[],'expanded':['1','2']}
  self.meta={'status':'acquired','strategy':'native','max_items':None,'identity':self.identity,'end_identity':self.identity,'source_url':'https://codelibrary.amlegal.com/codes/fixture/latest/overview','overview_url':'https://codelibrary.amlegal.com/codes/fixture/latest/overview','publication_selector':'fixture_oh','resume_count':0,'image_policy':al.IMAGE_POLICY,'started_at':'2026-01-01T00:00:00Z','finished_at':'2026-01-01T00:01:00Z'}
  book={'uuid':'book1','slug':'fixture_oh','title':'Fixture Code','is_pdf':False,'sections':[self.raw(self.nodes[0])]}
  redux={'codes':{'currClient':{'slug':'fixture','name':'Fixture','region':{'slug':'oh'}},'selectedVersion':{'uuid':'v1','client_slug':'fixture','name':'2026 S-1','currency_info':self.identity['currency_info'],'toc':[book]}}}
  overview=('window._redux_state = JSON.parse('+json.dumps(json.dumps(redux))+');').encode()
  for phase in ['start','end:0']:
   self.request('overview-start' if phase=='start' else 'overview-end:0',overview,self.meta['overview_url'])
   for n,children in [(self.nodes[0],[self.nodes[1]]),(self.nodes[1],self.nodes[2:])]:self.request(phase+':toc:'+n['document_id'],encoded({'doc_id':n['document_id'],'id':n['internal_id'],'code_uuid':'book1','children':[self.raw(x) for x in children]}),'https://codelibrary.amlegal.com/api/section-toc/'+str(n['internal_id'])+'/')
  htmls=['<div id="rid-1">PART I: CODE</div>','<div id="rid-2">CHAPTER 1 - RULES</div>','<div id="rid-3"><h2>1.01 Rule.</h2><p>Legal\u2028line\u0085text [IMAGE]<sup>1</sup></p><table><tr><th rowspan="2">A</th><td colspan="2">B</td></tr><tr><td>C</td><td>D</td></tr></table><aside>Note 1: exact note.</aside></div>','<div id="rid-4">1.02 Reserved.</div>']
  export=self.request('native-export',(''.join(htmls)).encode(),'https://codelibrary.amlegal.com/codes/fixture/v1/fixture_oh/0-0-0-1')
  export['response'].update(url='https://export.amlegal.com/api/export-requests/job1/download/',payload={'version':'v1','output_format':'html','for_print':False,'scope':'[{"code_slug":"fixture_oh"}]'},job={'version':'v1','for_print':False,'uuid':'job1'})
  self.records=[]
  for n,body in zip(self.nodes,htmls):
   d=n['document_id'];self.records.append(dict(n,kind='publisher-native-html-owned-range',publication_identity=self.identity,html=body,text=n['heading'],body_block_ids=[d],tables=[[[{'text':'A','rowspan':2},{'text':'B','colspan':2}],[{'text':'C'},{'text':'D'}]]] if d=='3' else [],links=[],notes=['Note 1: exact note.'] if d=='3' else [],assets=[],image_placeholders=[{'placeholder':'[IMAGE]'}] if d=='3' else [],image_policy=al.IMAGE_POLICY,source_sha256=export['sha256'],source_url=export['requested_url'],content_classification='reserved-heading-only' if d=='4' else 'operative-or-front-matter-body'))
  self.family={'publication_identity':self.identity,'inventory_complete':True,'source_consistent_at_end':True,'native_bulk_html_file_complete':True,'missing_ids':[],'extra_ids':[],'duplicate_ids':[],'independently_recomputed_branch_count':2,'acquired_count':4,'inventory_count':4,'owned_source_block_count':4,'table_count':1,'table_cell_count':4,'publication_complete':True,'jurisdiction_complete':False}
  self.assets=[];self.pages=[];self.sync()
 def node(self,d,i,h,p,children):return {'document_id':d,'internal_id':i,'heading':h,'parent_id':p,'path':[],'has_children':children,'orig_doc_id':d,'orig_doc_idx':0,'passthru_doc_id':None,'type':'section'}
 def raw(self,n):return {'doc_id':n['document_id'],'id':n['internal_id'],'title':n['heading'],'has_children':n['has_children'],'parent_doc_id':n['parent_id'],'type':'section'}
 def request(self,key,body,url):
  name='raw/'+sha(key.encode())+'.bin';(self.root/'raw').mkdir(exist_ok=True);(self.root/name).write_bytes(body);entry={'file':name,'sha256':sha(body),'requested_url':url,'response':{'status':200},'retrieved_at':'2026-01-01T00:00:30Z'};self.requests[key]=entry;return entry
 def sync(self):
  h=sha(canonical(self.inv));self.meta.update(inventory_sha256=h,inventory_end_sha256=h)
  for n,v in [('run.json',self.meta),('inventory.json',self.inv),('inventory-end.json',self.inv),('requests.json',self.requests),('coverage.json',self.family),('assets.json',self.assets),('checkpoint.json',{'acquired_ids':[r['document_id'] for r in self.records],'inventory_sha256':h})]:(self.root/n).write_bytes(encoded(v))
  for n,v in [('sections.jsonl',self.records),('pdf-pages.jsonl',self.pages)]:(self.root/n).write_bytes(b''.join(canonical(x)+b'\n' for x in v))
  self.proof={'schema':'offline-family-readonly-proof-1','family':'american-legal','publication_id':'fixture-primary','evidence_read_only':True,'publisher_requests':0,'source_changed_during_run':False,'runtime_changed_during_run':False,'evidence_sha256_before':{'fixture':'bound'},'evidence_sha256_after':{'fixture':'bound'},'collector_sources_before':{'verify.py':'fixture'},'collector_sources_after':{'verify.py':'fixture'},'verification':{'family_report_sha256':sha(encoded(self.family)),'forbidden_calls':[]},'selected_config':{'source_url':self.meta['source_url'],'publication_selector':'fixture_oh'}}
 def projection(self):self.sync();return al.read_projection(self.root,self.proof,self.family)

class ALReaderTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.f=SourceFixture(Path(self.tmp.name))
 def tearDown(self):self.tmp.cleanup()
 def refused(self):
  with self.assertRaises((ValueError,KeyError,AssertionError)):self.f.projection()
 def test_exact_html_notes_tables_sourceorder_and_16_fields(self):
  p=self.f.projection();self.assertEqual(len(p.rows),4);self.assertEqual(p.rows[2]['full_text'],self.f.records[2]['html']);self.assertEqual(p.provenance[2]['source_notes'],['Note 1: exact note.']);self.assertEqual(p.provenance[2]['source_tables'],self.f.records[2]['tables']);self.assertEqual(p.rows[2]['section_number'],'1.01');self.assertFalse(json.loads(artifacts(p)['validation-report.json'])['complete'])
 def test_middle_branch_missing_with_roots_present_refuses(self):del self.f.requests['start:toc:2'];self.refused()
 def test_end_source_changed_refuses(self):
  e=self.f.requests['end:0:toc:2'];body=json.loads((self.f.root/e['file']).read_text());body['children'].pop();e['sha256']=sha(encoded(body));(self.f.root/e['file']).write_bytes(encoded(body));self.refused()
 def test_duplicate_source_block_refuses(self):
  e=self.f.requests['native-export'];data=(self.f.root/e['file']).read_bytes()+b'<p id="rid-3">dup</p>';e['sha256']=sha(data);(self.f.root/e['file']).write_bytes(data);self.refused()
 def test_raw_native_order_swap_refuses(self):
  e=self.f.requests['native-export'];data=(self.f.root/e['file']).read_text().replace('rid-1','rid-X').replace('rid-2','rid-1').replace('rid-X','rid-2').encode();e['sha256']=sha(data);(self.f.root/e['file']).write_bytes(data);self.refused()
 def test_unowned_middle_native_block_refuses(self):
  e=self.f.requests['native-export'];data=(self.f.root/e['file']).read_bytes()+b'<p id="rid-unknown">missing</p>';e['sha256']=sha(data);(self.f.root/e['file']).write_bytes(data);self.refused()
 def test_ir_omission_refuses(self):self.f.records.pop(2);self.refused()
 def test_wrong_native_scope_refuses(self):self.f.requests['native-export']['response']['payload']['scope']='[]';self.refused()
 def test_wrong_edition_refuses(self):self.f.meta['end_identity']=dict(self.f.identity,version_uuid='other');self.refused()
 def test_pdf_page_mode_refuses(self):self.f.meta['identity']=dict(self.f.identity,is_pdf=True);self.refused()
 def test_limited_mode_refuses(self):self.f.meta['max_items']=4;self.refused()
 def test_table_omission_refuses(self):self.f.records[2]['tables']=[];self.refused()
 def test_declared_image_payload_refuses_without_decoder(self):
  self.f.records[2]['html']+='<object type=" IMAGE/PNG" data="data:application/octet-stream;base64,PIXELS"></object>'
  with patch('socket.socket.connect',side_effect=AssertionError('network')) as net,patch('base64.b64decode',side_effect=AssertionError('decode')) as dec:
   self.refused();net.assert_not_called();dec.assert_not_called()
 def test_active_image_anchor_refuses(self):self.f.records[2]['html']+='<a href="https://example.test/a.png">map</a>';self.refused()
 def test_same_type_ancestry_conflict_blank_retained(self):
  fields,_,_,_,conflicts=al.literal_components([{'id':'x','heading':'PART I: CODE'},{'id':'y','heading':'PART II: SUBCODE'}],'Rule');self.assertEqual(fields['part'],'');self.assertEqual(len(conflicts),1)
 def test_unicode_jsonl_literals_preserved(self):self.assertIn('\u2028',self.f.projection().rows[2]['full_text']);self.assertIn('\u0085',self.f.projection().rows[2]['full_text'])
 def test_required_nonimage_unprojected_stays_unresolved(self):
  data=b'%PDF fixture';(self.f.root/'raw/doc.bin').write_bytes(data);self.f.records[2]['assets']=[{'url':'https://example.test/doc.pdf'}];self.f.assets=[{'url':'https://example.test/doc.pdf','required':True,'status':'retained','file':'raw/doc.bin','sha256':sha(data)}];p=self.f.projection();self.assertEqual(p.dispositions[-1]['disposition'],'unresolved');self.assertEqual(p.inherited_coverage,self.f.family)
 def test_zero_glyph_policy_na_does_not_invent_legal_units(self):
  data=b'%PDF fixture';(self.f.root/'raw/doc.bin').write_bytes(data);self.f.records[2]['assets']=[{'url':'https://example.test/doc.pdf'}];self.f.assets=[{'url':'https://example.test/doc.pdf','required':True,'status':'retained','file':'raw/doc.bin','sha256':sha(data)}];owner='attachment:'+sha(data);self.f.assets[0].update(validation={'kind':'pdf','qualified':True,'pages':1},normalized_pdf_owner_id=owner,normalized_pdf_document_pages=1,normalized_pdf_page_ids=[owner+':page:1']);self.f.pages=[{'document_id':owner+':page:1','owner_id':owner,'page':1,'image_policy':al.IMAGE_POLICY,'source_url':'https://example.test/doc.pdf','text':'[IMAGE]','native_source_evidence':{'glyph_count':0},'source_qualification':{'policy_not_applicable_to_text_glyph_fidelity':True,'source_text_glyph_count':0}}];p=self.f.projection();self.assertEqual(len(p.rows),4);self.assertEqual(p.dispositions[-1]['disposition'],'excluded_by_scope')
 def test_structural_passthrough_uses_own_toc_not_descendant_body(self):
  f=self.f;n=f.nodes[0];n['passthru_doc_id']='2'
  for phase in ['overview-start','overview-end:0']:
   e=f.requests[phase];body=(f.root/e['file']).read_text();state=al.redux(body.encode());state['selectedVersion']['toc'][0]['sections'][0]['passthru_doc_id']='2';data=('window._redux_state = JSON.parse('+json.dumps(json.dumps({'codes':state}))+');').encode();(f.root/e['file']).write_bytes(data);e['sha256']=sha(data)
  e=f.requests['native-export'];data=(f.root/e['file']).read_text().replace('<div id="rid-1">PART I: CODE</div>','').encode();(f.root/e['file']).write_bytes(data);e['sha256']=sha(data)
  for r in f.records:r['source_sha256']=e['sha256']
  r=f.records[0];r.update(kind='publisher-toc-passthrough-container',passthru_target_id='2',body_block_ids=[],html=None,content_classification='structural-heading-only',source_sha256=f.requests['start:toc:1']['sha256'],source_url=f.requests['start:toc:1']['requested_url']);f.family['owned_source_block_count']=3
  p=f.projection();self.assertEqual(p.rows[0]['full_text'],'PART I: CODE');self.assertEqual(p.dispositions[0]['disposition'],'structural');self.assertNotIn('Rule.',p.rows[0]['full_text'])
 def test_asset_image_only_boolean_alone_does_not_qualify(self):
  self.test_zero_glyph_policy_na_does_not_invent_legal_units();self.f.pages[0]['native_source_evidence']['glyph_count']=1;p=self.f.projection();self.assertEqual(p.dispositions[-1]['disposition'],'unresolved')
 def test_portable_helper_refuses_pdf_before_output(self):
  import verify_input
  self.f.meta['identity']=dict(self.f.identity,is_pdf=True);self.f.sync();out=self.f.root.parent/(self.f.root.name+'-proof')
  with self.assertRaises(ValueError):verify_input.main(['--reader',al.READER,'--input',str(self.f.root),'--collector-root',str(Path(al.__file__).parent.parent/'verification-source'),'--publication-id','fixture','--out',str(out)])
  self.assertFalse(out.exists())
 def test_package_interruption_resume_and_relocated_verify(self):
  import package
  from common import files
  self.f.sync();self.f.proof['evidence_sha256_before']=files(self.f.root);self.f.proof['evidence_sha256_after']=files(self.f.root)
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);proof=d/'proof.json';proof.write_bytes(encoded(self.f.proof));family=d/'family.json';family.write_bytes(encoded(self.f.family));out=d/'package'
   with self.assertRaises(package.InterruptedPackage):package.run(self.f.root,proof,family,out,al.READER,interrupt_after=1)
   result=package.run(self.f.root,proof,family,out,al.READER,resume=True);self.assertTrue(result['package_verified']);self.assertFalse(result['complete'])
   before=files(out);result=package.verify(out);self.assertEqual(files(out),before)
   (out/'unknown.bin').write_bytes(b'foreign')
   with self.assertRaises(ValueError):package.verify(out)
 def test_required_asset_without_source_owner_refuses(self):
  self.test_required_nonimage_unprojected_stays_unresolved();self.f.records[2]['assets']=[];self.refused()
 def test_missing_middle_image_only_pdf_page_stays_unresolved(self):
  self.test_zero_glyph_policy_na_does_not_invent_legal_units();a=self.f.assets[0];a['validation']['pages']=2;a['normalized_pdf_document_pages']=2;a['normalized_pdf_page_ids'].append(a['normalized_pdf_owner_id']+':page:2');self.assertEqual(self.f.projection().dispositions[-1]['disposition'],'unresolved')
 def test_image_only_page_owner_wrong_source_sha_stays_unresolved(self):
  self.test_zero_glyph_policy_na_does_not_invent_legal_units();self.f.pages[0]['owner_id']='attachment:wrong';self.assertEqual(self.f.projection().dispositions[-1]['disposition'],'unresolved')
 def test_duplicate_image_only_page_ids_stay_unresolved(self):
  self.test_zero_glyph_policy_na_does_not_invent_legal_units();a=self.f.assets[0];a['validation']['pages']=2;a['normalized_pdf_document_pages']=2;a['normalized_pdf_page_ids']*=2;self.f.pages*=2;self.assertEqual(self.f.projection().dispositions[-1]['disposition'],'unresolved')
 def test_unqualified_pdf_validation_stays_unresolved(self):
  self.test_zero_glyph_policy_na_does_not_invent_legal_units();self.f.assets[0]['validation']['qualified']=False;self.assertEqual(self.f.projection().dispositions[-1]['disposition'],'unresolved')
 def test_missing_normalized_page_ids_stay_unresolved(self):
  self.test_zero_glyph_policy_na_does_not_invent_legal_units();self.f.assets[0]['normalized_pdf_page_ids']=[];self.assertEqual(self.f.projection().dispositions[-1]['disposition'],'unresolved')
 def test_retained_pdf_bytes_drift_refuses(self):
  self.test_zero_glyph_policy_na_does_not_invent_legal_units();(self.f.root/'raw/doc.bin').write_bytes(b'corrupt');self.refused()
 def test_complete_two_page_zero_glyph_control(self):
  self.test_zero_glyph_policy_na_does_not_invent_legal_units();a=self.f.assets[0];a['validation']['pages']=2;a['normalized_pdf_document_pages']=2;second=copy.deepcopy(self.f.pages[0]);second['page']=2;second['document_id']=a['normalized_pdf_owner_id']+':page:2';self.f.pages.append(second);a['normalized_pdf_page_ids'].append(second['document_id']);self.assertEqual(self.f.projection().dispositions[-1]['disposition'],'excluded_by_scope')
 def test_complete_two_page_one_text_page_not_image_only(self):
  self.test_complete_two_page_zero_glyph_control();self.f.pages[1]['native_source_evidence']['glyph_count']=1;self.f.pages[1]['text']='Substantive text';self.assertEqual(self.f.projection().dispositions[-1]['disposition'],'unresolved')
 def test_no_third_party_reader_imports(self):
  import ast
  tree=ast.parse(Path(al.__file__).read_text());imports=[n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module]+[a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names];self.assertFalse(set(imports)&{'bs4','pypdf','pdfminer','fitz','PIL','playwright'})
if __name__=='__main__':unittest.main()
