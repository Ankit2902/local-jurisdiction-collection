"""Independent launcher fail-closed acceptance; temporary gates/state only, no network."""
import copy,hashlib,importlib.util,json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('readiness_ops',ROOT/'collectors/ops/launcher.py');ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)
class OpsAcceptance(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.patch=patch.object(ops,'STATE_ROOT',self.root/'durable');self.patch.start()
 def tearDown(self):self.patch.stop();self.t.cleanup()
 def save(self,p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v))
 def pub(self,family='encodeplus',url='https://online.encodeplus.com/regs/test/'):
  return {'publisher':family,'source_family':family,'source_url':url}
 def output(self,url,required=True):
  folder=self.root/('required' if required else 'reference');self.save(folder/'coverage.json',{'required_assets_unresolved':[{'url':url}] if required else [],'references':[] if required else [{'url':url,'kind':'external_family_boundary','required':False}]});return folder
 def test_durable_publisher_refusal_survives_missing_tmp_and_new_output(self):
  gate=self.root/'gate';stop=gate/'browser-stop.json';self.save(stop,{'url':'https://library.municode.com/api/test','reason':'HTTP403'});env={'MUNICODE_GATE_DIR':str(gate)};pub=self.pub('municode','https://library.municode.com/zz/test/codes/code')
  self.assertTrue(ops.access_state(pub,env));stop.unlink();self.assertTrue(ops.access_state(pub,env,self.root/'new-output'));self.assertFalse(stop.exists())
 def test_external_host_stop_does_not_block_unrelated_pub(self):
  gate=self.root/'gate';host='required.example.test';stop=gate/('external-stop-'+hashlib.sha256(host.encode()).hexdigest()+'.json');self.save(stop,{'host':host,'url':'https://'+host+'/appendix.pdf','reason':'HTTP403'});env={'MUNICODE_GATE_DIR':str(gate)};pub=self.pub('municode','https://library.municode.com/zz/test/codes/code');out=self.output('https://'+host+'/appendix.pdf')
  self.assertTrue(ops.access_state(pub,env,out));stop.unlink();self.assertFalse(ops.access_state(pub,env));self.assertTrue(ops.access_state(pub,env,out))
 def test_external_cooldown_without_url_is_host_scoped_and_expires(self):
  gate=self.root/'gate';host='appendix.example.test';stop=gate/'hosts'/hashlib.sha256(host.encode()).hexdigest()/'state.json';self.save(stop,{'last_start':time.time(),'cooldown_until':time.time()+30});env={'ENCODEPLUS_GATE_DIR':str(gate)};pub=self.pub();out=self.output('https://'+host+'/appendix.pdf')
  self.assertTrue(ops.access_state(pub,env,out));stop.unlink();self.assertFalse(ops.access_state(pub,env), 'External cooldown was promoted to global publisher stop')
  with patch.object(ops.time,'time',return_value=time.time()+60):self.assertFalse(ops.access_state(pub,env,out),'Temporary cooldown never expired')
 def test_reference_only_external_stop_is_not_required_source(self):
  gate=self.root/'gate';host='other-family.example.test';stop=gate/('external-stop-'+hashlib.sha256(host.encode()).hexdigest()+'.json');self.save(stop,{'host':host,'url':'https://'+host+'/code','reason':'HTTP403'});pub=self.pub('municode','https://library.municode.com/zz/test/codes/code');env={'MUNICODE_GATE_DIR':str(gate)}
  self.assertFalse(ops.access_state(pub,env,self.output('https://'+host+'/code',False)))
 def test_ecode_and_municipal_stops_are_independent(self):
  gate=self.root/'gate';stop=gate/'ecode360'/'STOP.json';self.save(stop,{'url':'https://ecode360.com/123','status':403});env={'ICC_GATE_DIR':str(gate)};ecode={'publisher':'ecode','source_family':'ecode360','source_url':'https://ecode360.com/XX1234'};mc={'publisher':'ecode','source_family':'municipal.codes','source_url':'https://test.municipal.codes/Code'}
  self.assertTrue(ops.access_state(ecode,env));self.assertFalse(ops.access_state(mc,env));stop.unlink();self.assertTrue(ops.access_state(ecode,env))
 def test_exact_pins_reject_compatible_version_drift(self):
  packages=[{'name':line.split('==')[0],'version':line.split('==')[1]} for line in (ops.HERE/'requirements.txt').read_text().splitlines() if line and not line.startswith('#')];ops.check_pins(packages);changed=copy.deepcopy(packages);next(x for x in changed if x['name']=='pypdf')['version']='6.20.0'
  with self.assertRaises(ops.OperationError):ops.check_pins(changed)
 def test_checkpoint_advisory_blocks_fresh_home_without_gate_files(self):
  pub=self.pub('municode','https://library.municode.com/zz/test/codes/code');pub['observed_access_advisories']=[{'operator_review_required':True,'reason':'Observed malformed source-relative route403; not a claim every legitimate URL is denied','observed_stop':{'operator_release_required':True}}]
  stops=ops.access_state(pub,{'MUNICODE_GATE_DIR':str(self.root/'missing-gate')});self.assertTrue(any(x.get('checkpoint_access_advisory') for x in stops));self.assertFalse((self.root/'missing-gate').exists())
 def test_unknown_target_and_no_all_execution(self):
  import subprocess,sys
  with self.assertRaisesRegex(ops.OperationError,'Unknown target ID'):ops.registry_plan('unknown',None,sys.executable)
  for args in [('run','--target','unknown','--out',str(self.root/'out')),('run','--all','--out',str(self.root/'out'))]:
   r=subprocess.run([sys.executable,'-B',str(ROOT/'collect.py'),'--runtime',str(self.root/'no-runtime'),*args],capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertFalse((self.root/'out').exists())
 def job_context(self, output, versions, coverage=None, family="municode"):
  from contextlib import ExitStack
  from types import SimpleNamespace
  runtime=self.root/'runtime';runtime.mkdir(exist_ok=True);self.save(runtime/'runtime.json',{'packages':[],'requirements_sha256':'synthetic','browser_driver_sha256':{}})
  pub={'id':'synthetic-primary','publisher':family,'source_url':'https://library.municode.com/zz/synthetic/codes/code'}
  def child(*args,**kwargs):
   output.mkdir(exist_ok=True);self.save(output/'coverage.json',coverage if coverage is not None else {'publication_complete':True,'publication_text_complete':True,'publication_attachments_complete':True,'jurisdiction_complete':False});return SimpleNamespace(returncode=0)
  stack=ExitStack();stack.enter_context(patch.object(ops,'runtime_env',return_value=(Path('/synthetic/python'),Path('/synthetic/node'),{})));stack.enter_context(patch.object(ops,'registry_plan',return_value={'publication_id':pub['id'],'staged_config':None}));stack.enter_context(patch.object(ops,'catalog_publication',return_value=pub));stack.enter_context(patch.object(ops,'doctor',return_value={'runtime_ready':True,'ready':True,'issues':[]}));stack.enter_context(patch.object(ops,'code_binding',side_effect=versions));stack.enter_context(patch.object(ops,'access_state',return_value=[]));stack.enter_context(patch.object(ops.subprocess,'run',side_effect=child));return runtime,stack
 def test_concurrent_source_change_never_claims_current_complete(self):
  output=self.root/'out';runtime,stack=self.job_context(output,[{'model.py':'before'},{'model.py':'after'}])
  with stack:code,result=ops.execute_job(runtime,'synthetic',None,output)
  self.assertEqual(code,2);self.assertEqual(result['status'],'source_changed_during_run');self.assertFalse(result['selected_scope_verifier_passed']);job=ops.read(Path(result['job']));self.assertFalse(job['complete']);self.assertEqual(job['attempts'][0]['acquisition_exit'],0);self.assertEqual(job['attempts'][0]['verification_exit'],0);self.assertEqual(job['attempts'][0]['collector_sources_before'],{'model.py':'before'});self.assertEqual(job['attempts'][0]['collector_sources_after'],{'model.py':'after'})
 def test_stable_source_collect_and_verifier_can_complete_selected_scope(self):
  output=self.root/'out';runtime,stack=self.job_context(output,[{'model.py':'same'},{'model.py':'same'}])
  with stack:code,result=ops.execute_job(runtime,'synthetic',None,output)
  self.assertEqual(code,0);self.assertFalse(result['jurisdiction_complete']);self.assertFalse(result['source_changed_during_run'])
 def test_source_change_during_readonly_verification_is_reported(self):
  output=self.root/'out';runtime,stack=self.job_context(output,[{'model.py':'before'},{'model.py':'after'}])
  with stack:code,result=ops.execute_job(runtime,'synthetic',None,output,True)
  self.assertEqual(code,2);self.assertEqual(result['status'],'source_changed_during_verification');self.assertTrue(result['source_changed_during_run']);self.assertTrue(Path(result['log']).with_suffix('.json').is_file())
 def test_zero_exit_native_capture_cannot_claim_publication_accepted(self):
  output=self.root/'out';runtime,stack=self.job_context(output,[{'model.py':'same'},{'model.py':'same'}],{'native_document_complete':True,'source_page_traversal_complete':True,'publication_text_complete':False,'attachments_complete':False,'jurisdiction_complete':False})
  with stack:code,result=ops.execute_job(runtime,'synthetic',None,output)
  self.assertEqual(code,2);self.assertFalse(ops.read(Path(result['job']))['complete']);self.assertTrue(result['acceptance']['native_capture_verified']);self.assertFalse(result['publication_accepted'])
 def test_required_dependency_remains_explicitly_unaccepted(self):
  output=self.root/'out';self.save(output/'coverage.json',{'publication_text_complete':True,'publication_attachments_complete':True});pub=self.pub('municode');pub['required_publication_dependencies']=['100-fairfax-public-facilities-manual'];report=ops.publication_acceptance(pub,output);self.assertFalse(report['publication_coverage_accepted']);self.assertEqual(report['unresolved_required_publication_dependencies'],pub['required_publication_dependencies'])
 def test_official_native_pages_and_unsegmented_html_are_not_semantic_publications(self):
  output=self.root/'out';pub=self.pub('official')
  for coverage in [{'publication_file_coverage_complete':True,'pdf_page_extraction_complete':True,'publication_html_text_coverage_complete':False,'legal_semantic_coverage_complete':False},{'publication_file_coverage_complete':True,'publication_html_text_coverage_complete':True,'legal_semantic_coverage_complete':False}]:
   self.save(output/'coverage.json',coverage);r=ops.publication_acceptance(pub,output);self.assertFalse(r['publication_coverage_accepted']);self.assertTrue(r['native_capture_verified'])
 def test_retained_required_pdf_does_not_hide_false_semantic_dimensions(self):
  output=self.root/'out';coverage={'publication_text_complete':True,'attachment_complete':True,'pdf_text_layer_pages_parsed':2,'pdf_retained_asset_document_count':1,'pdf_semantic_text_completeness_qualified':False,'pdf_table_completeness_qualified':False}
  self.save(output/'coverage.json',coverage);r=ops.publication_acceptance(self.pub('american-legal'),output);self.assertTrue(r['required_nonimage_documents_complete']);self.assertFalse(r['legal_structure_qualified']);self.assertFalse(r['publication_coverage_accepted']);self.assertEqual(len(r['pdf_structure_dimensions']),2)
  runtime,stack=self.job_context(output,[{'model.py':'same'},{'model.py':'same'}],coverage,family='american-legal')
  with stack:code,result=ops.execute_job(runtime,'synthetic',None,output,True)
  self.assertEqual(code,2);self.assertTrue(result['family_verifier_passed']);self.assertFalse(result['acceptance']['publication_accepted']);self.assertTrue(result['acceptance']['required_nonimage_documents_complete'])
  # The same adapter publishes false PDF dimensions even for books with no PDFs.
  coverage['pdf_text_layer_pages_parsed']=0;coverage['pdf_retained_asset_document_count']=0;self.save(output/'coverage.json',coverage);self.assertTrue(ops.publication_acceptance(self.pub('american-legal'),output)['publication_coverage_accepted'])
 def test_shim_tamper_is_detected_and_browser_not_executed(self):
  runtime=self.root/'runtime';runtime.mkdir();packages=[{'name':line.split('==')[0],'version':line.split('==')[1]} for line in (ops.HERE/'requirements.txt').read_text().splitlines() if line and not line.startswith('#')]
  for name in ('package.json','node_modules/playwright/package.json','node_modules/playwright/index.cjs'):
   p=runtime/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}' if name.endswith('.json') else 'safe shim')
  self.save(runtime/'runtime.json',{'owner':ops.MARKER,'setup_complete':True,'packages':packages,'requirements_sha256':ops.sha(ops.HERE/'requirements.txt'),'browser_driver_sha256':{'node':'same'},'shim_sha256':ops.shim_hashes(runtime)})
  (runtime/'node_modules/playwright/index.cjs').write_text('changed shim')
  def captured(argv,*args,**kwargs):
   if '--format=json' in argv:return json.dumps(packages)
   if str(ops.HERE/'browser_check.cjs') in [str(x) for x in argv]:raise AssertionError('Tampered alias must never execute')
   return ''
  with patch.object(ops,'runtime_env',return_value=(Path('/synthetic/python'),Path('/synthetic/node'),{})),patch.object(ops,'driver_hashes',return_value={'node':'same'}),patch.object(ops,'captured',side_effect=captured):report=ops.doctor(runtime,browser=True)
  self.assertFalse(report['ready']);self.assertIn('alias',str(report['issues']));self.assertIn('browser_skipped',report)
if __name__=='__main__':unittest.main(verbosity=2)
