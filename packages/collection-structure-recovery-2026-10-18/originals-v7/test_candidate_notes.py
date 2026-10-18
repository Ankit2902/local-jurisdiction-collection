import sys,json,unittest,base64
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'source'))
from bs4 import BeautifulSoup
from model import semantics
from king_normalize import blocks
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
if __name__=='__main__':unittest.main()
