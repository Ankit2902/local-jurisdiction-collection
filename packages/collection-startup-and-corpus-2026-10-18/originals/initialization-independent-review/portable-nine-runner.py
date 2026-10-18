"""Nine source-bound originals regressions; standalone QA outside the runtime fingerprint.

Run with --source collectors/originals, or ORIGINALS_QA_SOURCE=/path/to/family.
No network, browser startup or separate image decoding is permitted by this runner.
"""
import argparse,base64,datetime,hashlib,json,os,socket,sys,unittest,urllib.request
from pathlib import Path
from unittest.mock import patch

def blocked(*args,**kwargs):raise AssertionError('Network/browser startup forbidden in originals legal-structure QA')

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',default=os.environ.get('ORIGINALS_QA_SOURCE',str(Path(__file__).resolve().parents[1]/'originals')))
parser.add_argument('--receipt',type=Path)
args=parser.parse_args()
source=Path(args.source).resolve()
required=['model.py','king_normalize.py','flagstaff_html_normalize.py']
if any(not(source/name).is_file() for name in required):parser.error('--source must be an originals runtime directory')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.name:sha(p) for p in source.iterdir() if p.is_file() and p.suffix in ['.py','.json']}
sys.path.insert(0,str(source))
patches=[patch.object(socket.socket,'connect',blocked),patch.object(socket,'create_connection',blocked),patch.object(urllib.request.OpenerDirector,'open',blocked),patch('playwright.sync_api.sync_playwright',blocked)]
for guard in patches:guard.start()
from bs4 import BeautifulSoup
from model import semantics
from king_normalize import blocks
from flagstaff_html_normalize import parse
for name in ['model','king_normalize','flagstaff_html_normalize']:
 if Path(sys.modules[name].__file__).resolve().parent!=source:raise AssertionError('QA source import binding differs: '+name)
class CandidateNotes(unittest.TestCase):
 def test_root_footnote_and_historynote_are_owned(self):
  for kind in ['Footnote','HistoryNote','Note','TableFootnote','CellBodyNote','CellBodyFootnote']:
   with self.subTest(kind=kind):
    node=BeautifulSoup('<p class="'+kind+'" id="source-note">Legal source note.</p>','html.parser').p;r=semantics(node,'https://example.invalid/code');self.assertEqual(len(r['notes']),1);self.assertIn(kind,r['notes'][0]);self.assertIn('source-note',r['notes'][0]);self.assertEqual(r['text'],'Legal source note.')
 def test_overlapping_source_note_classes_do_not_duplicate(self):
  node=BeautifulSoup('<p class="Footnote HistoryNote" role="note">One occurrence.</p>','html.parser').p;self.assertEqual(len(semantics(node,'https://example.invalid/code')['notes']),1)
 def test_identical_separate_notes_remain_separate_occurrences(self):
  node=BeautifulSoup('<div><p class="Note">Same words.</p><p class="Note">Same words.</p></div>','html.parser').div;self.assertEqual(len(semantics(node,'https://example.invalid/code')['notes']),2)
 def test_exact_source_backlink_keeps_one_block_and_root_link(self):
  soup=BeautifulSoup('<div><a name="409" href="#wwfootnote_inline_409">1</a></div>','html.parser');units=list(blocks(soup.div));self.assertEqual(len(units),1);self.assertEqual(units[0].name,'a');r=semantics(units[0],'https://example.invalid/code');self.assertEqual(r['text'],'1');self.assertEqual(len(r['links']),1);self.assertEqual(r['links'][0]['attributes']['name'],'409');self.assertIn('href="#wwfootnote_inline_409"',r['html'])
 def test_unsupported_source_backlink_shape_reports_gap(self):
  soup=BeautifulSoup('<div><a name="409" href="#wwfootnote_inline_409"><span>1</span></a></div>','html.parser');before=str(soup)
  with self.assertRaisesRegex(ValueError,'Unqualified source footnote backlink wrapper shape'):list(blocks(soup.div))
  self.assertEqual(str(soup),before)
 def test_root_note_image_is_placeholder_without_decoder_or_payload_metadata(self):
  uri='DATA:application/octet-stream;base64,QUJD\nPRIVATE_PIXELS_MUST_NOT_SURVIVE';node=BeautifulSoup('<p class="Footnote">Visible caption<img src="'+uri+'" alt="'+uri+'"></p>','html.parser').p
  with patch.object(base64,'b64decode',side_effect=AssertionError('Image payload decoder forbidden')) as decoder:r=semantics(node,'https://example.invalid/code')
  decoder.assert_not_called();self.assertEqual(r['image_placeholder_count'],1);self.assertEqual(len(r['notes']),1);self.assertIn('[IMAGE]',r['notes'][0]);self.assertNotIn('PRIVATE_PIXELS',json.dumps(r));self.assertNotIn('QUJD',json.dumps(r));self.assertEqual(r['assets'][0]['status'],'policy_omitted_image');self.assertFalse(r['assets'][0]['required'])

class NestedSourceGroups(unittest.TestCase):
 def check(self,first):
  before='<p>Before sibling.</p>' if first else ''
  raw=('<div id="mainContent"><h1 id="h">Title</h1><div class="Bulleted_outer" id="outer">'+before+'<div class="P2_outer" id="inner"><p>A <a href="#target">legal</a>.</p><table><tr><td id="target">Cell mandatory.</td></tr></table><p>Caption<img src="data:application/octet-stream;base64,PRIVATE_PIXEL_SENTINEL"></p></div><p>B mandatory.</p></div></div>').encode()
  with patch.object(base64,'b64decode',side_effect=AssertionError('Image decode prohibited')) as decoder:records,audit=parse(raw,'https://example.invalid/code',[])
  decoder.assert_not_called();self.assertEqual(len(records),1);r=records[0];s=BeautifulSoup(r['semantic_html'],'html.parser');self.assertEqual(len(s.select('#outer')),1);self.assertEqual(len(s.select('#inner')),1);self.assertIn('B mandatory.',s.get_text());self.assertIn('A legal.',r['full_text']);self.assertEqual(len(s.select('table')),1);self.assertEqual(len(r['tables']),1);self.assertEqual(len(r['links']),1);self.assertEqual(r['image_placeholder_count'],1);self.assertEqual(r['semantic_html'].count('[IMAGE]'),1);self.assertNotIn('PRIVATE_PIXEL',str(r));self.assertEqual(len(r['source_list_groups']),2);self.assertEqual(r['source_list_groups'][1]['parent_source_group_id'],r['source_list_groups'][0]['source_group_id']);self.assertEqual(audit['source_blocks'],audit['owned_blocks']);self.assertEqual(len(r['block_indices']),len(set(r['block_indices'])))
  if first:self.assertIn('Before sibling.',s.get_text())
 def test_nested_same_first_index_full_conservation(self):self.check(False)
 def test_nested_different_first_index_full_conservation(self):self.check(True)
 def test_multiple_record_nested_group_refuses_ambiguous_owner(self):
  raw=b'<div id="mainContent"><h1>Title</h1><div class="Bulleted_outer"><p>Legal.</p><div class="P2_outer"><h3>New section</h3><p>Mandatory.</p></div></div></div>'
  with self.assertRaisesRegex(ValueError,'Unqualified source list group ownership shape'):parse(raw,'https://example.invalid/code',[])

try:
 suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(CandidateNotes),unittest.defaultTestLoader.loadTestsFromTestCase(NestedSourceGroups)])
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 after={p.name:sha(p) for p in source.iterdir() if p.is_file() and p.suffix in ['.py','.json']}
 if after!=before:raise AssertionError('Selected originals runtime changed during QA')
 receipt={'schema':'originals-portable-nine-legal-structure-regressions-1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),'runtime_files_sha256':before,'runner_sha256':sha(Path(__file__)),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful() and result.testsRun==9,'source_unchanged':True,'network_and_browser_tripwires':True,'image_decode_tripwire_in_image_cases':True,'scope':'Nine bounded real-parser regression cases; no live transport or full-publication credit'}
 if args.receipt:
  if args.receipt.exists():raise FileExistsError('Fresh receipt path required')
  args.receipt.parent.mkdir(parents=True,exist_ok=True);args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
 sys.exit(0 if receipt['passed'] else 1)
finally:
 for guard in reversed(patches):guard.stop()
