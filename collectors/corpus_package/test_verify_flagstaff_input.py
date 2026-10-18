"""Finite orchestration/refusal tests; fake common does not normalize or acquire."""
import sys
sys.dont_write_bytecode = True
import copy
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('helper', HERE / 'verify_flagstaff_input.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

class HelperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.source = self.base / 'evidence'
        self.collector = self.base / 'collector'
        self.runtime = self.base / 'runtime'
        self.out = self.base / 'proof'
        self.cfg = dict(profile='flagstaff_html', target_id=h.TARGET, source_url=h.SOURCE, required_formats=['html'])
        for folder in (self.source, self.collector, self.runtime / 'verifications'):
            folder.mkdir(parents=True)
        self.write(self.source / 'checkpoint.json', {'config': self.cfg})
        self.write(self.source / 'normalized/records.jsonl', {'text':'Legal caption [IMAGE] remains.'})
        self.write(self.runtime / 'runtime.json', {'owner':'test controlled fixture only'})
        for name in ('collect.py','collectors/ops/launcher.py','collectors/ops/browser_check.cjs','collectors/ops/requirements.txt','collectors/registry/collect.py','collectors/registry/dispatch.py','collectors/registry/catalog.py','collectors/originals/cli.py','collectors/originals/verify.py'):
            path=self.collector/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text('# controlled fixture\n')
        self.write(self.collector/'collectors/originals/configs/flagstaff.json', self.cfg)
        self.write(self.collector/'collectors/originals/profiles/source.json', {'raw_source_sha':'fixture'})
        self.write(self.collector/'collectors/registry/catalog.json', {'publication':h.PUBLICATION})
        self.log=self.runtime/'verifications/test.log'
        self.family={'full_raw_replay_equal':True,'input_files_modified':False,'source_route_ledger_verified':True,'opening_body_closing_chronology_verified':True,'publication_config':self.cfg,'publication_accepted':True,'complete':True,'literal_browser_fragment_health':False,'native_capture_verified':False,'edition_complete':None}
        self.receipt=self.make_receipt()
        self.mutate=None

    @staticmethod
    def write(path,value):
        path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False)+'\n')

    def make_receipt(self):
        source_map=h.files(self.source)
        sources=h.collector_files(self.collector)
        py=self.runtime/'venv/bin/python'
        return {'publication_id':h.PUBLICATION,'selected_config':copy.deepcopy(self.cfg),'output':str(self.source),'verification_exit':0,'evidence_read_only':True,'publisher_requests':0,'source_changed_during_run':False,'runtime_changed_during_run':False,'evidence_sha256_before':source_map,'evidence_sha256_after':source_map,'collector_sources_before':sources,'collector_sources_after':sources,'runtime_receipt_sha256':h.sha(self.runtime/'runtime.json'),'runtime_receipt_path':str(self.runtime/'runtime.json'),'log':str(self.log),'verification_argv':[str(py),'-B',str(self.collector/'collectors/registry/collect.py'),'verify','--target',h.TARGET,'--publication',h.PUBLICATION,'--out',str(self.source),'--python',str(py)],'family_verifier_passed':True,'status':'verified_publication','acceptance':{'publication_accepted':True,'jurisdiction_complete':False,'edition_complete':None,'native_capture_verified':False,'literal_browser_fragment_health':False}}

    def child(self, argv, **kwargs):
        self.assertEqual(argv,[sys.executable,'-B',str(self.collector/'collect.py'),'--runtime',str(self.runtime),'verify','--target',h.TARGET,'--publication',h.PUBLICATION,'--out',str(self.source)])
        self.assertEqual(kwargs['cwd'],self.collector)
        self.assertEqual(kwargs['env']['PYTHONDONTWRITEBYTECODE'],'1')
        self.write(self.log,self.family)
        self.write(self.log.with_suffix('.json'),self.receipt)
        if self.mutate: self.mutate()
        code=0 if self.receipt.get('acceptance',{}).get('publication_accepted') else 2
        return subprocess.CompletedProcess(argv,code,h.encoded(self.receipt),b'fixture stderr retained\n')

    def invoke(self):
        with patch.object(h.subprocess,'run',side_effect=self.child),patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')):
            return h.run(self.source,self.collector,self.runtime,self.out)

    def refuses(self, text=None):
        with self.assertRaises((ValueError,FileNotFoundError,json.JSONDecodeError)) as error:self.invoke()
        if text:self.assertIn(text,str(error.exception))
        self.assertFalse((self.out/'read-only-proof.json').exists())

    def test_exact_bytes_and_false_gates_preserved(self):
        terminal=self.invoke()
        proof=json.loads((self.out/'read-only-proof.json').read_text())
        original=json.loads((self.out/'common-readonly.json').read_text())
        self.assertEqual(proof['acceptance'],original['acceptance'])
        self.assertFalse(proof['acceptance']['jurisdiction_complete'])
        self.assertIsNone(proof['acceptance']['edition_complete'])
        self.assertEqual((self.out/'family-verification.json').read_bytes(),self.log.read_bytes())
        self.assertEqual(proof['family_verification_sha256'],h.sha(self.log))
        self.assertTrue(terminal['verification_adapter_complete'])
        self.assertFalse(terminal['publication_acceptance_added'])

    def test_valid_incomplete_result_stays_incomplete(self):
        self.receipt.update(verification_exit=2,family_verifier_passed=False,status='publication_acceptance_incomplete')
        self.receipt['acceptance']['publication_accepted']=False
        self.family.update(complete=False,publication_accepted=False)
        terminal=self.invoke()
        self.assertEqual(terminal['common_exit'],2)
        self.assertFalse(terminal['primary_publication_accepted'])

    def test_changed_evidence_truthful_failure(self):
        self.mutate=lambda:(self.source/'normalized/records.jsonl').write_text('changed')
        self.refuses('Input evidence changed')
        f=json.loads((self.out/'verification-failure.json').read_text())
        self.assertFalse(f['input_unchanged']);self.assertFalse(f['acceptance_proof_written'])
        self.assertNotIn('source_not_deleted_or_rewritten',f)

    def test_deleted_evidence_does_not_mask_failure(self):
        self.mutate=lambda:(self.source/'checkpoint.json').unlink()
        self.refuses('Input evidence changed')
        self.assertFalse(json.loads((self.out/'verification-failure.json').read_text())['input_unchanged'])

    def test_independent_source_change_detects_falsified_receipt(self):
        def mutation():
            (self.collector/'collectors/originals/verify.py').write_text('changed')
            new=h.collector_files(self.collector)
            self.receipt.update(collector_sources_before=new,collector_sources_after=new)
            self.write(self.log.with_suffix('.json'),self.receipt)
        self.mutate=mutation
        self.refuses('Independent collector source')

    def test_incomplete_source_map_refused(self):
        self.receipt['collector_sources_before'].pop('collectors/ops/requirements.txt')
        self.refuses('Independent collector source')

    def test_config_mismatch_refused_before_output(self):
        self.write(self.collector/'collectors/originals/configs/flagstaff.json',dict(self.cfg,publication='wrong'))
        self.refuses('configuration differs');self.assertFalse(self.out.exists())

    def test_wrong_identity_refused(self):
        self.receipt['publication_id']='wrong'
        self.refuses('another publication')

    def test_wrong_command_refused(self):
        self.receipt['verification_argv'][3]='collect'
        self.refuses('Unexpected common verification command')

    def test_saved_receipt_mismatch_refused(self):
        self.mutate=lambda:self.write(self.log.with_suffix('.json'),{})
        self.refuses('Saved common receipt')

    def test_nonjson_family_refused(self):
        self.mutate=lambda:self.log.write_text('not json')
        self.refuses()

    def test_family_config_and_raw_verification_refused(self):
        self.family['full_raw_replay_equal']=False
        self.refuses('not qualified')

    def test_family_false_cannot_be_accepted(self):
        self.family['publication_accepted']=False
        self.refuses('contradicts family')

    def test_contradictory_exit_refused(self):
        self.receipt['verification_exit']=2
        self.refuses('Contradictory family')

    def test_publication_false_even_with_successful_family_is_retained(self):
        self.receipt['acceptance']['publication_accepted']=False
        self.receipt['status']='publication_acceptance_incomplete'
        terminal=self.invoke()
        self.assertEqual(terminal['common_exit'],2)
        self.assertFalse(terminal['primary_publication_accepted'])
        self.assertEqual(json.loads((self.out/'read-only-proof.json').read_text())['verification_exit'],0)

    def test_family_config_mismatch_refused(self):
        self.family['publication_config']=dict(self.cfg,publication='foreign')
        self.refuses('configuration differs')

    def test_boolean_request_counter_is_not_evidence(self):
        self.receipt['publisher_requests']=False
        self.refuses('unchanged/read-only')

    def test_runtime_mutation_refused(self):
        self.mutate=lambda:self.write(self.runtime/'runtime.json',{})
        self.refuses('Runtime receipt changed')

    def test_source_symlink_refused(self):
        path=self.collector/'collectors/originals/profiles/source.json'
        target=self.base/'alias.json';path.rename(target);path.symlink_to(target)
        self.refuses('Symlink')

    def test_log_symlink_parent_refused(self):
        original=self.runtime/'verifications';original.rename(self.runtime/'real-logs');original.symlink_to(self.runtime/'real-logs',target_is_directory=True)
        self.refuses()

    def test_output_symlink_refused_without_writes(self):
        self.out.symlink_to(self.base/'notcreated')
        self.refuses('Symlink root');self.assertFalse((self.base/'notcreated').exists())

    def test_output_overlap_refused_without_subprocess(self):
        self.out=self.source/'proof'
        self.refuses('Fresh output');self.assertFalse(self.out.exists())

    def cli_control(self, accepted):
        entry = self.collector / 'collect.py'
        entry.write_text("""import sys
sys.dont_write_bytecode=True
import json,pathlib,socket
def forbidden(*args,**kwargs): raise AssertionError('network forbidden')
socket.socket.connect=forbidden
a=sys.argv
assert a[1:2]==['--runtime'] and a[3:4]==['verify'] and '--resume' not in a and 'run' not in a
r=pathlib.Path(a[2]); p=json.loads((r/'fixture-payload.json').read_text())
log=pathlib.Path(p['receipt']['log'])
log.write_bytes((json.dumps(p['family'],indent=2)+'\\n').encode())
log.with_suffix('.json').write_text(json.dumps(p['receipt']))
print(json.dumps(p['receipt']))
sys.exit(0 if p['receipt']['acceptance']['publication_accepted'] else 2)
""")
        self.receipt=self.make_receipt()
        if not accepted:
            self.receipt.update(verification_exit=2,family_verifier_passed=False,status='publication_acceptance_incomplete')
            self.receipt['acceptance']['publication_accepted']=False
            self.family.update(complete=False,publication_accepted=False)
        self.write(self.runtime/'fixture-payload.json',{'receipt':self.receipt,'family':self.family})
        before=h.files(self.source);code=h.files(self.collector)
        result=subprocess.run([sys.executable,str(HERE/'verify_flagstaff_input.py'),'--input',str(self.source),'--collector-root',str(self.collector),'--runtime',str(self.runtime),'--out',str(self.out)],capture_output=True,cwd=self.base)
        self.assertEqual(result.returncode,0,result.stderr.decode()+result.stdout.decode())
        terminal=json.loads(result.stdout)
        self.assertIs(terminal['primary_publication_accepted'],accepted)
        self.assertEqual(terminal['common_exit'],0 if accepted else 2)
        self.assertEqual(before,h.files(self.source));self.assertEqual(code,h.files(self.collector))
        self.assertFalse(list(self.collector.rglob('*.pyc')))
        self.assertEqual((self.out/'family-verification.json').read_bytes(),self.log.read_bytes())

    def test_ordinary_python_cli_accepted_control(self):
        self.cli_control(True)

    def test_ordinary_python_cli_incomplete_control(self):
        self.cli_control(False)

    def test_unsafe_file_references_refused(self):
        for name in ('../x','/tmp/x','a\\b','a//b','./x','a/../b'):
            with self.subTest(name=name), self.assertRaises(ValueError):h.rooted_file(self.collector,name)

if __name__=='__main__': unittest.main()
