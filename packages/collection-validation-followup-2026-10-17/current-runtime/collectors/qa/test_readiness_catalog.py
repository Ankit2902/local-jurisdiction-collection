"""All-publication dispatch and real CLI refusal acceptance, no publisher requests."""
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'collectors/registry'))
from catalog import load_catalog
from verify_catalog import audit
from dispatch import command,Unsupported
class ReadinessCatalog(unittest.TestCase):
 def test_exact_130_source_audit(self):self.assertTrue(audit()['passed'],audit()['errors'])
 def test_original_omission_wrong_customer_and_wrong_source_fail(self):
  for mutate in ['omit','customer','source','dependency']:
   c=load_catalog()
   if mutate=='omit':c['targets']=[t for t in c['targets'] if t['id']!='original-daly-city-ca']
   elif mutate=='customer':next(p for p in c['publications'] if p['id']=='original-burlingame-ca-primary')['expected_identity']['customer_id']='AL0934'
   elif mutate=='dependency':next(p for p in c['publications'] if p['id']=='100-0506c8bf0a84')['required_publication_dependencies']=['1-primary']
   else:next(p for p in c['publications'] if p['id']=='original-daly-city-ca-primary')['source_url']='https://library.municode.com/ca/other/codes/code_of_ordinances'
   self.assertFalse(audit(c)['passed'],mutate)
 def test_all_publication_dispatch_truth(self):
  c=load_catalog();tb={t['id']:t for t in c['targets']}
  for p in c['publications']:
   if p['runnable']:
    plan=command(p,tb[p['target_id']],'/fresh/output');self.assertFalse(plan['jurisdiction_complete']);self.assertEqual(plan['publication_id'],p['id']);self.assertIn('/fresh/output',plan['argv'])
   else:
    with self.assertRaises(Unsupported,msg=p['id']):command(p,tb[p['target_id']],'/fresh/output')
 def test_observed_al_strategy_and_alias(self):
  c=load_catalog();tb={t['id']:t for t in c['targets']}
  for p in c['publications']:
   if p['publisher']=='american-legal' and p['runnable']:
    argv=command(p,tb[p['target_id']],'/fresh/output')['argv'];self.assertEqual(argv[argv.index('--strategy')+1],'traverse' if p['observed_is_pdf'] else 'native')
  alias=next(p for p in c['publications'] if p['id']=='23-a722039b19bf');self.assertEqual(alias['configuration_alias_of'],'23-6a2adb9cc064')
 def cli(self,*args):
  # Execute the actual CLI with a hard adapter-launch tripwire. Refusal tests
  # must remain offline when a formerly unsupported catalog entry is qualified.
  harness="import pathlib,runpy,subprocess,sys; sys.path.insert(0,str(pathlib.Path(sys.argv[1]).parent)); subprocess.run=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('QA_ADAPTER_LAUNCH_FORBIDDEN')); sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')"
  result=subprocess.run([sys.executable,'-B','-c',harness,str(ROOT/'collectors/registry/collect.py'),*args],capture_output=True,text=True,timeout=30)
  self.assertNotIn('QA_ADAPTER_LAUNCH_FORBIDDEN',result.stderr,'CLI crossed its expected refusal boundary')
  return result
 def test_cli_cohort_and_original_string_id(self):
  for cohort,count in [('expansion',100),('original',30),('all',130)]:
   r=self.cli('plan','--cohort',cohort,'--all');self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['targets'],count)
  r=self.cli('plan','--target','original-daly-city-ca');self.assertEqual(r.returncode,0,r.stderr);self.assertIn('16311',json.loads(r.stdout)['plans'][0]['argv'])
 def test_checkpoint_stop_visible_and_blocks_collection_before_adapter(self):
  r=self.cli('plan','--target','60');plan=json.loads(r.stdout)['plans'][0];self.assertTrue(plan['observed_access_advisories']);self.assertIn('Malformed',plan['observed_access_advisories'][0]['reason'])
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'unused';r=self.cli('collect','--target','60','--out',str(out));self.assertNotEqual(r.returncode,0);self.assertIn('operator review',r.stderr);self.assertFalse(out.exists())
 def test_gridics_current_refusal_visible_and_collect_stops_before_adapter(self):
  r=self.cli('plan','--target','29','--publication','29-2153491435c1');plan=json.loads(r.stdout)['plans'][0];advisory=plan['observed_access_advisories'][0];self.assertEqual(advisory['family'],'gridics');self.assertEqual(advisory['raw_refusal_witness']['http_status'],403);self.assertEqual(advisory['raw_refusal_witness']['body_bytes_saved'],0);self.assertIn('untested',advisory['reason'])
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'unused';r=self.cli('collect','--target','29','--publication','29-2153491435c1','--out',str(out));self.assertNotEqual(r.returncode,0);self.assertIn('operator review',r.stderr);self.assertFalse(out.exists())
 def test_missing_shipped_advisory_catalog_is_not_ready(self):
  import shutil
  with tempfile.TemporaryDirectory() as td:
   for source in (ROOT/'collectors/registry').glob('*.json'):
    if source.name!='access-advisories.json':shutil.copyfile(source,Path(td)/source.name)
   with self.assertRaisesRegex(ValueError,'Access advisory catalog missing'):load_catalog(here=td)
 def test_cli_refuses_all_unknown_foreign_and_unsupported_without_output(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'never-created'
   c=load_catalog();unsupported=next(t for t in c['targets'] if not next(p for p in c['publications'] if p['id']==t['primary_publication_id'])['runnable'])
   for args in [('collect','--all'),('collect','--target','unknown'),('collect','--target','original-daly-city-ca','--publication','1-primary'),('collect','--target',unsupported['id'])]:
    r=self.cli(*args,'--out',str(out));self.assertNotEqual(r.returncode,0,(args,r.stdout));self.assertFalse(out.exists(),args)
 def test_adapter_tripwire_blocks_a_runnable_target_before_execution(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'never-created'
   with self.assertRaisesRegex(AssertionError,'refusal boundary'):
    self.cli('collect','--target','67','--out',str(out))
   self.assertFalse(out.exists())
 def test_cli_protects_existing_unowned_output(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'keep.txt';p.write_text('unchanged');r=self.cli('collect','--target','original-daly-city-ca','--out',td);self.assertNotEqual(r.returncode,0);self.assertEqual(p.read_text(),'unchanged');self.assertEqual(list(Path(td).iterdir()),[p])
 def test_cli_wrong_retained_target_refuses_before_adapter(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'checkpoint.json';p.write_text(json.dumps({'source_url':'https://library.municode.com/nv/henderson/codes/code_of_ordinances','binding':{'state':'NV','client_names':['Henderson'],'expected_client_id':11734,'product_ids':[14896]}}));before=p.read_bytes();r=self.cli('verify','--target','original-daly-city-ca','--out',td);self.assertNotEqual(r.returncode,0);self.assertIn('does not match',r.stderr);self.assertEqual(before,p.read_bytes())
if __name__=='__main__':unittest.main(verbosity=2)
