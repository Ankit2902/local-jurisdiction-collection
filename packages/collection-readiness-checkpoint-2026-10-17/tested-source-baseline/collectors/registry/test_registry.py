"""Independent registry scope and dispatch fault tests; no publisher/network calls."""
import copy,json,subprocess,sys,tempfile,unittest,os
from pathlib import Path
from unittest.mock import patch
from dispatch import ROOT,read,bind_run,Unsupported,command,qualified
from verify import audit,HERE
class Tests(unittest.TestCase):
 def setUp(self):self.ts=read(HERE/'targets.json')['targets'];self.ps=read(HERE/'publications.json')['publications'];self.tb={t['id']:t for t in self.ts};self.pb={p['id']:p for p in self.ps}
 def test_exact_registry(self):self.assertTrue(audit()['passed'],audit()['errors'])
 def test_missing_duplicate_and_foreign_target_fail(self):
  for ts in [self.ts[:-1],self.ts+[self.ts[0]]]:self.assertFalse(audit(ts,self.ps)['passed'])
  ts=copy.deepcopy(self.ts);ts[0]['jurisdiction']=ts[1]['jurisdiction'];self.assertFalse(audit(ts,self.ps)['passed'])
 def test_numeric_ecode_and_wrong_product_fail(self):
  for seq,url in [('38','https://ecode360.com/123456')]:
   ps=copy.deepcopy(self.ps);next(p for p in ps if p['id']==seq+'-primary')['source_url']=url;self.assertFalse(audit(self.ts,ps)['passed'])
  ps=copy.deepcopy(self.ps);next(p for p in ps if p['publisher']=='municode')['publisher_product_id']=999999999;self.assertFalse(audit(self.ts,ps)['passed'])
 def test_coherent_but_unobserved_route_rejected(self):
  ts=copy.deepcopy(self.ts);ps=copy.deepcopy(self.ps);t=next(t for t in ts if t['publisher']=='municode');p=next(p for p in ps if p['id']==t['primary_publication_id']);p['source_url']='https://library.municode.com/nv/other_government/codes/code_of_ordinances';t['source_url']=p['source_url'];t['primary_publication']=p;self.assertFalse(audit(ts,ps)['passed'])
 def test_historical_sample_cannot_promote_full(self):
  ps=copy.deepcopy(self.ps);ps[0]['full_live_verified']=True;self.assertFalse(audit(self.ts,ps)['passed'])
 def metadata(self,p,t):
  q=qualified(p,t);i=p['expected_identity'];f=p['publisher']
  if f=='official':return 'config.json',q['config']
  if f=='encodeplus':return 'checkpoint.json',{'config':q['config']}
  if f=='municode':return 'checkpoint.json',{'source_url':p['source_url'],'binding':{'state':t['state'],'client_names':i['client_names'],'expected_client_id':i['publisher_client_id'],'product_ids':[q['product_id']]}}
  if f=='american-legal':return 'run.json',{'source_url':p['source_url'],'expected_jurisdiction':t['jurisdiction'],'expected_state':t['state'],'publication_selector':p.get('selector',{}).get('publication')}
  return 'checkpoint.json',{'config':{'family':p['source_family'],'url':p['source_url'],'jurisdiction':t['jurisdiction'],'state':t['state'],'subtree':False},'identity':{'customer_id':i.get('customer_id')},'publication_url':p['source_url']}
 def test_wrong_target_same_family_rejected_before_verifier(self):
  for family in ['municode','american-legal','ecode','encodeplus','official']:
   pubs=[p for p in self.ps if p['role']=='primary' and p['publisher']==family and p['runnable']];a,b=pubs[:2]
   with tempfile.TemporaryDirectory() as td:
    name,value=self.metadata(a,self.tb[a['target_id']]);(Path(td)/name).write_text(json.dumps(value));self.assertTrue(bind_run(a,self.tb[a['target_id']],td))
    with self.assertRaises(Unsupported,msg=family):bind_run(b,self.tb[b['target_id']],td)
 def test_wrong_publication_same_client_rejected(self):
  secondary=next(p for p in self.ps if p['publisher']=='municode' and p['role']=='secondary' and p['runnable']);t=self.tb[secondary['target_id']];primary=self.pb[t['primary_publication_id']]
  with tempfile.TemporaryDirectory() as td:
   name,value=self.metadata(primary,t);(Path(td)/name).write_text(json.dumps(value))
   with self.assertRaises(Unsupported):bind_run(secondary,t,td)
 def test_no_all_target_collection_and_cross_target_publication(self):
  for args in [['collect','--all','--out','x'],['collect','--target','1','--publication','2-primary','--out','x']]:
   r=subprocess.run([sys.executable,'-B',str(HERE/'collect.py'),*args],capture_output=True,text=True);self.assertNotEqual(r.returncode,0)
 def test_relative_output_resolved_before_subprocess(self):
  # Inspect wrapper at dispatch boundary without starting a family collector.
  import importlib.util
  spec=importlib.util.spec_from_file_location('registry_cli',HERE/'collect.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as td,patch.object(sys,'argv',['collect.py','collect','--target','1','--out',os.path.relpath(Path(td)/'relative')]),patch.object(m.subprocess,'run') as run:
   run.return_value.returncode=0
   with self.assertRaises(SystemExit):m.main()
   argv=run.call_args.args[0];self.assertEqual(Path(argv[argv.index('--out')+1]),(Path(td)/'relative').resolve())
if __name__=='__main__':unittest.main(verbosity=2)
