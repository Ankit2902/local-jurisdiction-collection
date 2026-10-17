"""Exact dependency proof acceptance through launcher entrypoints; no network."""
import copy,json,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from test_ops_acceptance import ops

class DependencyAcceptance(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.catalog={
   'parent':{'id':'parent','target_id':'P','publisher':'municode','source_url':'https://library.municode.com/zz/parent/codes/code','required_publication_dependencies':['dependency']},
   'dependency':{'id':'dependency','target_id':'D','publisher':'municode','source_url':'https://library.municode.com/zz/dependency/codes/code'}}
  self.runtime=self.root/'runtime';self.runtime.mkdir();self.save(self.runtime/'runtime.json',{'packages':[],'requirements_sha256':'fixed'})
 def tearDown(self):self.tmp.cleanup()
 def save(self,p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d))
 def coverage(self,p,complete=True):self.save(p/'coverage.json',{'publication_text_complete':complete,'publication_attachments_complete':complete})
 def context(self,wrong=False,mutate=False,partial=False):
  stack=ExitStack()
  stack.enter_context(patch.object(ops,'STATE_ROOT',self.root/'state'))
  stack.enter_context(patch.object(ops,'runtime_env',return_value=(Path('/synthetic/python'),Path('/synthetic/node'),{})))
  stack.enter_context(patch.object(ops,'registry_plan',side_effect=lambda target,pub,python:{'publication_id':pub or 'parent','staged_config':{'id':pub or 'parent'}}))
  stack.enter_context(patch.object(ops,'catalog_publication',side_effect=lambda ident:copy.deepcopy(self.catalog[ident])))
  stack.enter_context(patch.object(ops,'doctor',return_value={'runtime_ready':True,'ready':True,'issues':[]}))
  stack.enter_context(patch.object(ops,'code_binding',return_value={'source':'stable'}))
  stack.enter_context(patch.object(ops,'access_state',return_value=[]))
  def child(argv,**kwargs):
   ident=argv[argv.index('--publication')+1];action=argv[3]
   output=Path(argv[argv.index('--out')+1])
   if ident=='dependency':
    self.assertEqual(action,'verify','Dependency proof must never acquire')
    if wrong:return SimpleNamespace(returncode=2)
    if mutate:(output/'raw.bin').write_bytes(b'changed during verify')
    if partial:self.coverage(output,False)
   else:self.coverage(output)
   return SimpleNamespace(returncode=0)
  stack.enter_context(patch.object(ops.subprocess,'run',side_effect=child))
  return stack
 def test_exact_current_dependency_proof_can_close_parent(self):
  dep=self.root/'dep';self.coverage(dep);(dep/'raw.bin').write_bytes(b'original source')
  with self.context():code,result=ops.execute_job(self.runtime,'P','parent',self.root/'parent',dependency_proofs={'dependency':str(dep)})
  self.assertEqual(code,0);self.assertTrue(result['publication_accepted']);proof=result['acceptance']['dependency_proofs'][0]
  self.assertTrue(proof['accepted']);self.assertTrue(proof['evidence_unchanged']);self.assertIn('raw.bin',proof['evidence_sha256']);self.assertEqual(proof['current_verification']['publication']['id'],'dependency');self.assertTrue(proof['current_verification']['runtime_receipt_sha256']);self.assertEqual(proof['current_verification']['selected_config'],{'id':'dependency'})
 def test_wrong_same_family_scope_or_partial_proof_cannot_close(self):
  for kind in ('wrong','partial','mutate'):
   dep=self.root/('dep-'+kind);self.coverage(dep);(dep/'raw.bin').write_bytes(b'original')
   with self.context(**{kind:True}):code,result=ops.execute_job(self.runtime,'P','parent',self.root/('parent-'+kind),dependency_proofs={'dependency':str(dep)})
   self.assertEqual(code,2,kind);self.assertEqual(result['acceptance']['unresolved_required_publication_dependencies'],['dependency']);self.assertFalse(result['publication_accepted'])
 def test_missing_proof_remains_gap_and_can_close_without_reacquisition(self):
  out=self.root/'parent';dep=self.root/'dep';self.coverage(dep)
  with self.context():
   code,result=ops.execute_job(self.runtime,'P','parent',out)
   self.assertEqual(code,2);self.assertTrue(ops.read(Path(result['job']))['capture_verified'])
   code,result=ops.execute_job(self.runtime,'P','parent',out,dependency_proofs={'dependency':str(dep)})
  self.assertEqual(code,0);job=ops.read(Path(result['job']));self.assertEqual([x['action'] for x in job['attempts']],['collect','verify'])
 def test_dependency_input_unknown_duplicate_and_cycles_fail_closed(self):
  with patch.object(ops,'catalog_publication',side_effect=lambda ident:copy.deepcopy(self.catalog[ident])):
   for values in (['unrelated=/proof'],['dependency=/a','dependency=/b'],['not-a-binding']):
    with self.assertRaises(ops.OperationError):ops.dependency_inputs(values,self.catalog['parent'])
   self.catalog['dependency']['required_publication_dependencies']=['parent']
   with self.assertRaisesRegex(ops.OperationError,'Cyclic'):ops.dependency_inputs([],self.catalog['parent'])
 def test_missing_and_symlink_evidence_never_accepted(self):
  dep=self.root/'dep';self.coverage(dep);(dep/'linked').symlink_to(self.runtime/'runtime.json')
  with self.context():
   for path in (self.root/'absent',dep):
    reports=ops.verify_dependencies(self.runtime,self.catalog['parent'],{'dependency':str(path)},['parent']);self.assertFalse(reports[0]['accepted'])

if __name__=='__main__':unittest.main(verbosity=2)
