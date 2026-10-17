"""Synthetic exact Notes boundary regression; not live/source publication proof."""
import sys
sys.dont_write_bytecode=True
import unittest,tempfile,json,importlib.util
from pathlib import Path
from notes import sanitize_notes
from model import reconcile_publication
from verify import verify
from test_faults import run_fixture,replace_unit,save,FakeBrowser
BASE='https://library.municode.com/zz/fixture/codes/test_publication'
CONT='UElYRUxTX0NPTlRJTlVBVElPTl9NVVNUX05PVF9TVVJWSVZF'
QUOTED='Figure reference: "DATA:IMAGE/PNG;base64,QUJD\n'+CONT+'". Legal caption remains.'
class MultilineNotes(unittest.TestCase):
 def test_quoted_exact_qa_fixture_preserves_prefix_and_caption(self):
  clean,omissions,_=sanitize_notes({'NoteContent':QUOTED},BASE)
  self.assertEqual(clean['NoteContent'],'Figure reference: "[IMAGE]". Legal caption remains.')
  self.assertNotIn(CONT,json.dumps([clean,omissions]));self.assertFalse(any(o.get('qualification_error') for o in omissions))
 def test_parentheses_and_multiple_images_keep_outside_text(self):
  raw='Citation § 2 (data:image/png;base64,AAA\nBBB) retained; "data:image/svg+xml;base64,CCC\nDDD" ends.'
  clean,omissions,_=sanitize_notes(raw,BASE)
  self.assertEqual(clean,'Citation § 2 ([IMAGE]) retained; "[IMAGE]" ends.')
  self.assertFalse(any(o.get('qualification_error') for o in omissions))
 def test_unquoted_ambiguous_wrapping_cannot_qualify_text(self):
  raw='Citation before DATA:IMAGE/PNG;base64,QUJD\n'+CONT+' legal prose boundary unknown'
  clean,omissions,_=sanitize_notes(raw,BASE)
  self.assertTrue(clean.startswith('Citation before [IMAGE]'))
  self.assertNotIn(CONT,json.dumps([clean,omissions]))
  self.assertTrue(any(o.get('qualification_error') for o in omissions))
 def test_actual_reconcile_and_verifier_scoped_completion(self):
  for value,qualified in [(QUOTED,True),('Citation before data:image/png;base64,QUJD\n'+CONT+' ambiguous legal prose',False)]:
   with self.subTest(qualified=qualified),tempfile.TemporaryDirectory() as temp:
    folder=Path(temp)/'run';FakeBrowser.fail_after=None;cp=run_fixture(folder)
    replace_unit(folder,cp,'content-root:17',lambda a:[a[0],{**a[1],'Notes':[{'NoteContent':value}]},a[2]])
    save(folder,cp);records,report=reconcile_publication(folder,cp,17)
    encoded=json.dumps({'records':records,'coverage':report});self.assertNotIn(CONT,encoded)
    self.assertIn('notes_source_sha256',records[1]);self.assertEqual(report['publication_complete'],qualified)
    self.assertEqual(verify(folder)['publication_complete'],qualified)

def report():
 spec=importlib.util.spec_from_file_location('baseline_notes',Path(__file__).parent/'baseline/notes.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 baseline=old.sanitize_notes({'NoteContent':QUOTED},BASE)
 candidate=sanitize_notes({'NoteContent':QUOTED},BASE)
 result={'kind':'isolated synthetic regression, not live proof','baseline_continuation_leaks':CONT in json.dumps(baseline[:2]),'candidate_continuation_leaks':CONT in json.dumps(candidate[:2]),'candidate_quoted_note':candidate[0]['NoteContent'],'production_files_modified':False,'network_requests':0}
 (Path(__file__).parent/'focused-probe.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':report();unittest.main()
