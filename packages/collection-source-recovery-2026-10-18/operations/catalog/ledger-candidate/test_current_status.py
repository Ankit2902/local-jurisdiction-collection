"""Exhaustive225catalog rows; no readiness promotion or publisher/native APIs."""
import copy,hashlib,importlib.util,json,pathlib,socket,sys,unittest
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
sys.path[:0]=[str(REPO/'collectors/registry'),str(REPO/'collectors/qa')];sys.dont_write_bytecode=True
from catalog import load_catalog
from dispatch import command,Unsupported
spec=importlib.util.spec_from_file_location('candidate_followup',HERE/'build_followup_ledger.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CurrentCatalogStatus(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=load_catalog();cls.ledger=json.loads((REPO/'collectors/qa/followup-requirements.json').read_text());cls.by={r['publication_id']:r for r in cls.ledger['publications']};cls.prior={'path':'collectors/qa/readiness-requirements.json','sha256':hashlib.sha256((REPO/'collectors/qa/readiness-requirements.json').read_bytes()).hexdigest()}
 def setUp(self):
  p=patch.object(socket,'socket',side_effect=AssertionError('Network forbidden'));p.start();self.addCleanup(p.stop)
 def test_all225_current_dispatch_and_access_fields(self):
  out=[]
  for p in self.catalog['publications']:
   r=m.refresh_catalog_operational_state(copy.deepcopy(self.by[p['id']]),p,self.prior);out.append(r)
   self.assertIs(r['dispatchable_config'],p['runnable']);self.assertIs(r['configuration_qualified'],p['runnable']);self.assertIs(r['operational_access_prohibited'],bool(p['observed_access_advisories']));self.assertEqual(r['access_stop_evidence'],p['observed_access_advisories']);self.assertEqual(r['observed_access_advisories'],r['access_stop_evidence'])
  self.assertEqual(len(out),225);self.assertEqual(sum(r['dispatchable_config'] for r in out),195);self.assertEqual(sum(r['operational_access_prohibited'] for r in out),154)
 def test_only_status_and_explicit_history_change(self):
  fields={'dispatchable_config','configuration_qualified','operational_access_prohibited','access_stop_evidence','observed_access_advisories','historical_operational_state'}
  for p in self.catalog['publications']:
   old=copy.deepcopy(self.by[p['id']]);new=m.refresh_catalog_operational_state(copy.deepcopy(old),p,self.prior)
   self.assertEqual({k:v for k,v in old.items() if k not in fields},{k:v for k,v in new.items() if k not in fields});self.assertEqual(old['requirements'],new['requirements']);self.assertEqual(old['readiness_verified'],new['readiness_verified']);self.assertEqual(old['active_readiness_binding'],new['active_readiness_binding'])
 def test_all_prior_fields_preserved_with_ledger_binding(self):
  for p in self.catalog['publications']:
   old=self.by[p['id']];new=m.refresh_catalog_operational_state(copy.deepcopy(old),p,self.prior);prior={k:old[k] for k in ['dispatchable_config','operational_access_prohibited','access_stop_evidence'] if k in old}
   if prior:self.assertEqual(new['historical_operational_state']['values'],prior);self.assertEqual(new['historical_operational_state']['source_ledger'],self.prior)
 def test_new_row_gets_all_fields_without_false_history(self):
  p=next(p for p in self.catalog['publications'] if p['id']=='29-gridics-comprehensive-plan-94');r=m.refresh_catalog_operational_state({'requirements':{'owned_text':False},'readiness_verified':False},p,self.prior);self.assertTrue(r['dispatchable_config']);self.assertTrue(r['operational_access_prohibited']);self.assertTrue(r['access_stop_evidence']);self.assertNotIn('historical_operational_state',r);self.assertFalse(r['readiness_verified'])
 def test_all195_dispatch_plans_and30_refusals_agree(self):
  targets={t['id']:t for t in self.catalog['targets']};yes=no=0
  for p in self.catalog['publications']:
   if p['runnable']:self.assertTrue(command(p,targets[p['target_id']],'{OUT}')['argv']);yes+=1
   else:
    with self.assertRaises(Unsupported):command(p,targets[p['target_id']],'{OUT}')
    no+=1
  self.assertEqual((yes,no),(195,30))
 def test_deepcopy_prevents_history_or_advisory_alias_mutation(self):
  p=next(p for p in self.catalog['publications'] if p['id']=='59-primary');old=copy.deepcopy(self.by[p['id']]);before=copy.deepcopy(p);r=m.refresh_catalog_operational_state(copy.deepcopy(old),p,self.prior);r['access_stop_evidence'][0]['reason']='changed';self.assertEqual(p,before);self.assertEqual(r['observed_access_advisories'],before['observed_access_advisories']);r['historical_operational_state']['values']['operational_access_prohibited']=not old['operational_access_prohibited'];self.assertEqual(self.by[p['id']],old)
if __name__=='__main__':unittest.main(verbosity=2)
