"""Offline actual-config regression; touches temporary repositories only."""
import copy,importlib.util,json,socket,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class NamedBinding(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.network=patch.object(socket,'socket',side_effect=AssertionError('No network permitted'));self.network.start();self.addCleanup(self.network.stop)
  self.modules={}
  for version in ('baseline','candidate'):
   for key,rel in [('ops','ops/launcher.py'),('qa','qa/readiness_binding.py'),('dispatch','registry/dispatch.py')]:
    module=load(version+'_'+key,HERE/version/'collectors'/rel);module.ROOT=self.root;module.HERE=self.root/'collectors/ops';self.modules[version,key]=module
  for name in ['ops/launcher.py','ops/browser_check.cjs','ops/requirements.txt','registry/collect.py','registry/dispatch.py','registry/catalog.py','encodeplus/model.py','municode/model.py','official/model.py','originals/model.py','ecode/model.py','gridics/model.py','american-legal/model.py']:
   path=self.root/'collectors'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('constant source fixture')
  self.config=json.loads((HERE/'fixtures/targets.json').read_text());self.write_configs()
  self.pub=json.loads((HERE/'fixtures/publication.json').read_text());self.target=json.loads((HERE/'fixtures/target.json').read_text())
 def write_configs(self):
  (self.root/'collectors/encodeplus/targets.json').write_text(json.dumps(self.config,indent=2)+'\n')
 def m(self,name,version='candidate'):return self.modules[version,name]
 def plan(self,version='candidate'):return self.m('dispatch',version).command(self.pub,self.target,'OUTPUT')
 def mutate(self):self.config['overland']['scope']+=' [ACTUAL SCOPE MUTATION]';self.write_configs()
 def test_actual_overland_dispatch_and_exact_selected_content(self):
  old=self.plan('baseline');new=self.plan();self.assertEqual(old['argv'],new['argv']);self.assertEqual(new['named_config_key'],'overland');self.assertEqual(new['named_config_path'],'collectors/encodeplus/targets.json')
  for key in old:self.assertEqual(old[key],new[key],key)
  selected=self.m('qa').selected_configuration(self.root,self.pub,self.target,new)['descriptor']
  self.assertEqual(selected['qualified_config'],self.config['overland']);self.assertEqual(selected['qualified_config_file_sha256'],self.m('qa').sha(self.root/new['named_config_path']));self.assertEqual(self.m('ops').selected_runtime_config(new),self.config['overland'])
 def test_reproduces_baseline_omission_and_corrects_stale_plan(self):
  old=self.plan('baseline');new=self.plan();old_components=self.m('ops','baseline').code_binding('encodeplus');old_qa=self.m('qa','baseline').current_components(self.root,'encodeplus');old_selected=self.m('qa','baseline').selected_configuration(self.root,self.pub,self.target,old)
  new_components=self.m('ops').code_binding('encodeplus');new_qa=self.m('qa').current_components(self.root,'encodeplus');new_selected=self.m('qa').selected_configuration(self.root,self.pub,self.target,new)
  self.mutate()
  self.assertEqual(old_components,self.m('ops','baseline').code_binding('encodeplus'));self.assertEqual(old_qa,self.m('qa','baseline').current_components(self.root,'encodeplus'));self.assertEqual(old_selected,self.m('qa','baseline').selected_configuration(self.root,self.pub,self.target,old))
  self.assertNotEqual(new_components,self.m('ops').code_binding('encodeplus'));self.assertNotEqual(new_qa,self.m('qa').current_components(self.root,'encodeplus'));self.assertNotEqual(new_selected,self.m('qa').selected_configuration(self.root,self.pub,self.target,new));self.assertEqual(self.m('ops').selected_runtime_config(new),self.config['overland']);self.assertEqual(new,self.plan())
 def test_unselected_entry_and_file_bytes_are_bound(self):
  plan=self.plan();before=self.m('qa').selected_configuration(self.root,self.pub,self.target,plan);self.config['lincoln']['scope']='changed other entry';self.write_configs();after=self.m('qa').selected_configuration(self.root,self.pub,self.target,plan)
  self.assertEqual(before['descriptor']['qualified_config'],after['descriptor']['qualified_config']);self.assertNotEqual(before['sha256'],after['sha256'])
 def test_missing_named_file_fails_closed(self):
  plan=self.plan();(self.root/plan['named_config_path']).unlink()
  for call in [lambda:self.m('ops').code_binding('encodeplus'),lambda:self.m('qa').current_components(self.root,'encodeplus'),lambda:self.m('ops').selected_runtime_config(plan),lambda:self.m('qa').selected_configuration(self.root,self.pub,self.target,plan)]:
   with self.assertRaises((ValueError,OSError)):call()
 def test_missing_wrong_and_nondictionary_keys_fail(self):
  original=self.plan()
  for key in (None,'unknown','overland'):
   plan=copy.deepcopy(original);plan['named_config_key']=key
   if key=='overland':self.config[key]='not a config';self.write_configs()
   with self.assertRaises(self.m('ops').OperationError):self.m('ops').selected_runtime_config(plan)
   with self.assertRaises(ValueError):self.m('qa').selected_configuration(self.root,self.pub,self.target,plan)
 def test_alternate_and_ambiguous_sources_refused(self):
  for update in ({'named_config_path':'../targets.json'},{'qualified_config_path':'collectors/encodeplus/targets.json'}):
   plan=dict(self.plan(),**update)
   with self.assertRaises(self.m('ops').OperationError):self.m('ops').selected_runtime_config(plan)
   with self.assertRaises(ValueError):self.m('qa').selected_configuration(self.root,self.pub,self.target,plan)
 def test_other_family_components_do_not_bind_named_ep_input(self):
  for family in ('municode','american-legal','ecode','official','gridics','originals'):
   before=self.m('ops').code_binding(family);before_qa=self.m('qa').current_components(self.root,family)
   self.assertEqual(before,self.m('ops','baseline').code_binding(family));self.assertEqual(before_qa,self.m('qa','baseline').current_components(self.root,family));self.assertNotIn('collectors/encodeplus/targets.json',before)
   self.mutate();self.assertEqual(before,self.m('ops').code_binding(family));self.assertEqual(before_qa,self.m('qa').current_components(self.root,family))
 def test_non_ep_dispatch_plans_and_selected_descriptors_unchanged(self):
  examples=[('municode','https://library.municode.com/ks/example/codes/code_of_ordinances',{'publisher_product_id':1,'expected_identity':{'client_names':['Example']}}),('american-legal','https://codelibrary.amlegal.com/codes/example/latest/example/0-0-0',{}),('ecode','https://ecode360.com/AA0001',{'source_family':'ecode360','expected_identity':{'customer_id':'AA0001'}}),('official','https://example.gov/code.pdf',{'role':'secondary'})]
  for family,url,extras in examples:
   pub=dict(self.pub,publisher=family,source_url=url,**extras);old=self.m('dispatch','baseline').command(pub,self.target,'OUTPUT');new=self.m('dispatch').command(pub,self.target,'OUTPUT');self.assertEqual(old,new);self.assertEqual(self.m('qa','baseline').selected_configuration(self.root,pub,self.target,old),self.m('qa').selected_configuration(self.root,pub,self.target,new))
 def test_custom_ep_configuration_plan_remains_unchanged(self):
  pub=dict(self.pub,source_url='https://example.test/custom/',adapter_config={'identity':'Exact custom book','base':'https://example.test/custom/','scope':'Exact custom scope'})
  old=self.m('dispatch','baseline').command(pub,self.target,'OUTPUT');new=self.m('dispatch').command(pub,self.target,'OUTPUT');self.assertEqual(old,new);self.assertNotIn('named_config_path',new);self.assertEqual(self.m('ops').selected_runtime_config(new),pub['adapter_config'])
 def test_native_ep_configuration_plan_remains_unchanged(self):
  rel='collectors/encodeplus/configs/native.json';path=self.root/rel;path.parent.mkdir(parents=True,exist_ok=True)
  native={'id':self.pub['id'],'mode':'native_document','url':'https://example.test/exact.pdf','state':self.target['state'],'expected_sha256':'a'*64,'expected_pages':4};path.write_text(json.dumps(native));pub=dict(self.pub,source_url=native['url'],adapter_config_path=rel)
  old=self.m('dispatch','baseline').command(pub,self.target,'OUTPUT');new=self.m('dispatch').command(pub,self.target,'OUTPUT');self.assertEqual(old,new);self.assertNotIn('named_config_path',new);self.assertEqual(self.m('ops').selected_runtime_config(new),native)
 def test_existing_qualified_and_staged_selection_unchanged(self):
  path=self.root/'config.json';path.write_text('{"exact":"qualified"}')
  for plan in ({'qualified_config_path':'config.json'},{'staged_config':{'exact':'staged'}},{}):
   self.assertEqual(self.m('qa','baseline').selected_configuration(self.root,self.pub,self.target,plan),self.m('qa').selected_configuration(self.root,self.pub,self.target,plan));self.assertEqual(self.m('ops').selected_runtime_config(plan),json.loads(path.read_text()) if plan.get('qualified_config_path') else plan.get('staged_config'))

if __name__=='__main__':unittest.main(verbosity=2)
