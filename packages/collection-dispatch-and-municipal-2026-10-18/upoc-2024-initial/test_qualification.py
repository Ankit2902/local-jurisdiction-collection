"""Pure registry qualification faults. No PDF/native or network imports."""
import copy,importlib.util,json,pathlib,shutil,tempfile,unittest
H=pathlib.Path(__file__).resolve().parent;HERE=H/'candidate/collectors/registry';spec=importlib.util.spec_from_file_location('historical',HERE/'historical_upoc_qualification.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
base={'id':m.IDENT,'validation_level':'mapped_only'};base.update(json.loads((H/'REGISTRY-OVERRIDE-PROPOSAL.json').read_text())['publications'][m.IDENT]);catalog={'publications':[base]}
class Qualification(unittest.TestCase):
 def test_exact_complete172_source_proof(self):self.assertEqual(m.audit(HERE,catalog),[])
 def test_scope_identity_alias_current_flags_failclosed(self):
  for key,value in [('id','wrong'),('source_url',m.ALIAS),('full_live_verified',True),('validation_level','live_pass'),('runnable',False),('adapter_mode','html'),('adapter_config_path','../../wrong')]:
   c=copy.deepcopy(catalog);c['publications'][0][key]=value
   with self.subTest(key=key):self.assertTrue(m.audit(HERE,c))
 def test_wrong_kind_sha_page_count(self):
  for key,value in [('kind','literal-current-publisher-anchor-and-pinned-original-native-file'),('native_sha256','0'*64),('physical_pages',171),('config_sha256','0'*64)]:
   c=copy.deepcopy(catalog);c['publications'][0]['qualification_evidence'][key]=value
   with self.subTest(key=key):self.assertTrue(m.audit(HERE,c))
 def test_archive_corruption_and_missing_proof(self):
  for mode in ['missing','corrupt']:
   with tempfile.TemporaryDirectory()as td:
    root=pathlib.Path(td);d=root/'collectors/registry';shutil.copytree(HERE,d);f=d/'historical-upoc-source-evidence.zip'
    if mode=='missing':f.unlink()
    else:f.write_bytes(f.read_bytes()+b'changed')
    with self.subTest(mode=mode):self.assertTrue(m.audit(d,catalog))
 def test_config_wrong_or_external_symlink_refused(self):
  for mode in ['changed','symlink']:
   with tempfile.TemporaryDirectory()as td:
    root=pathlib.Path(td);d=root/'collectors/registry';shutil.copytree(HERE,d);target=root/m.CONFIG_PATH;target.parent.mkdir(parents=True)
    if mode=='changed':target.write_text('{}')
    else:target.symlink_to(H/'candidate'/m.CONFIG_PATH)
    with self.subTest(mode=mode):self.assertTrue(m.audit(d,catalog))
if __name__=='__main__':unittest.main(verbosity=2)
