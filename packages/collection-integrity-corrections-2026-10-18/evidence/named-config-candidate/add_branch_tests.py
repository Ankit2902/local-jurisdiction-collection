from pathlib import Path
p=Path('test_named_binding.py');s=p.read_text();needle=' def test_existing_qualified_and_staged_selection_unchanged(self):'
addition=''' def test_custom_ep_configuration_plan_remains_unchanged(self):
  pub=dict(self.pub,source_url='https://example.test/custom/',adapter_config={'identity':'Exact custom book','base':'https://example.test/custom/','scope':'Exact custom scope'})
  old=self.m('dispatch','baseline').command(pub,self.target,'OUTPUT');new=self.m('dispatch').command(pub,self.target,'OUTPUT');self.assertEqual(old,new);self.assertNotIn('named_config_path',new);self.assertEqual(self.m('ops').selected_runtime_config(new),pub['adapter_config'])
 def test_native_ep_configuration_plan_remains_unchanged(self):
  rel='collectors/encodeplus/configs/native.json';path=self.root/rel;path.parent.mkdir(parents=True,exist_ok=True)
  native={'id':self.pub['id'],'mode':'native_document','url':'https://example.test/exact.pdf','state':self.target['state'],'expected_sha256':'a'*64,'expected_pages':4};path.write_text(json.dumps(native));pub=dict(self.pub,source_url=native['url'],adapter_config_path=rel)
  old=self.m('dispatch','baseline').command(pub,self.target,'OUTPUT');new=self.m('dispatch').command(pub,self.target,'OUTPUT');self.assertEqual(old,new);self.assertNotIn('named_config_path',new);self.assertEqual(self.m('ops').selected_runtime_config(new),native)
'''
assert needle in s;p.write_text(s.replace(needle,addition+needle))
