import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from readiness_binding import assess,canonical,sha,current_components,selected_configuration,gate_qa_sources
class Binding(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.sources={'collectors/example/model.py':'abc'}
  self.row={'publisher':'official','publication_id':'20-primary','active_source_url':'https://example.test/code','configuration_qualified':True,'observed_access_advisories':[],'requirements':{key:{'status':'pass'} for key in ['owned_text','table_fidelity','image_policy']}}
  self.write('records.jsonl','records');manifest={'files':[{'path':'records.jsonl','sha256':sha(self.root/'records.jsonl')}]};self.write('manifest.json',manifest)
  self.write('runtime.json',{'pins':'actual'});proof={'runtime_receipt':'runtime.json','runtime_receipt_sha256':sha(self.root/'runtime.json'),'publication_id':self.row['publication_id'],'source_url':self.row['active_source_url'],'config_sha256':'config','component_sources':self.sources,'artifact_manifest':'manifest.json','artifact_manifest_sha256':sha(self.root/'manifest.json'),'verification_receipt':'verify.json'}
  receipt={**proof,'publication_accepted':True,'read_only':True,'source_before':self.sources,'source_after':self.sources};self.write('verify.json',receipt);proof['verification_receipt_sha256']=sha(self.root/'verify.json');proof['scope_id']=canonical({k:proof[k] for k in ['publication_id','source_url','config_sha256','component_sources','artifact_manifest_sha256','verification_receipt_sha256','runtime_receipt_sha256']})
  for v in self.row['requirements'].values():v['proof_scope_id']=proof['scope_id']
  for name in ['audit_normalized_images.py','audit_images.py','test_image_policy.py','test_all_family_image_metadata.py','test_official_image_transport.py']:
   p=self.root/'collectors/qa'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('qualified QA revision')
  for key in ['image_transport_regression','normalized_image_audit','acquired_bytes_image_audit']:
   self.write(key+'.json',{'passed':True,'component_sources':self.sources,'proof_scope_id':proof['scope_id'],'executed_qa_sources':gate_qa_sources(self.root,'official',key)});proof[key]={'path':key+'.json','sha256':sha(self.root/(key+'.json'))}
  self.row['active_runtime_proof']=proof
 def tearDown(self):self.temp.cleanup()
 def write(self,name,data):(self.root/name).write_text(data if isinstance(data,str) else json.dumps(data))
 def check(self):return assess(self.row,self.root,self.root,self.sources,'config')
 def test_single_bound_revision_positive(self):self.assertTrue(self.check()['accepted'])
 def test_all_green_without_proof_fails(self):self.row.pop('active_runtime_proof');self.assertFalse(self.check()['accepted'])
 def test_candidate_cannot_supply_active_pass(self):self.row['requirements']['table_fidelity']['status']='candidate_pass';self.assertFalse(self.check()['accepted'])
 def test_mixed_revision_green_fails(self):self.sources={'collectors/example/model.py':'new'};self.assertFalse(self.check()['accepted'])
 def test_wrong_config_fails(self):self.row['active_runtime_proof']['config_sha256']='other';self.assertFalse(self.check()['accepted'])
 def test_cross_publication_proof_fails(self):self.row['publication_id']='59-primary';self.assertFalse(self.check()['accepted'])
 def test_dimension_from_other_run_fails(self):self.row['requirements']['table_fidelity']['proof_scope_id']='other';self.assertFalse(self.check()['accepted'])
 def test_image_test_from_other_revision_fails(self):self.write('image_transport_regression.json',{'passed':True,'component_sources':{'old':'hash'},'proof_scope_id':'other'});self.row['active_runtime_proof']['image_transport_regression']['sha256']=sha(self.root/'image_transport_regression.json');self.assertFalse(self.check()['accepted'])
 def test_records_mutation_fails(self):self.write('records.jsonl','changed');self.assertFalse(self.check()['accepted'])
 def test_real_qualified_config_file_content_change_is_bound(self):
  self.write('config.json',{'id':'actual','pages':6});pub={'id':'82','source_url':'https://example.test/book'};plan={'qualified_config_path':'config.json','argv':['python','--config','config.json']};before=selected_configuration(self.root,pub,{},plan)['sha256'];self.write('config.json',{'id':'actual','pages':7});self.assertNotEqual(before,selected_configuration(self.root,pub,{},plan)['sha256'])
 def test_real_lock_and_dispatch_and_family_policy_changes_are_bound(self):
  for name in ['collectors/ops/requirements.txt','collectors/registry/dispatch.py','collectors/official/policies/exact.json']:
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('original');before=current_components(self.root,'official');p.write_text('changed');self.assertNotEqual(before,current_components(self.root,'official'),name)
 def test_old_auditor_revision_cannot_cover_new_output_scope(self):
  (self.root/'collectors/qa/audit_normalized_images.py').write_text('new stream coverage');self.assertFalse(self.check()['accepted'])
 def test_runtime_receipt_change_fails(self):self.write('runtime.json',{'pins':'changed'});self.assertFalse(self.check()['accepted'])
 def test_access_stop_is_not_released_by_green_proof(self):self.row['observed_access_advisories']=[{'status':403}];self.assertFalse(self.check()['accepted'])
if __name__=='__main__':unittest.main(verbosity=2)
