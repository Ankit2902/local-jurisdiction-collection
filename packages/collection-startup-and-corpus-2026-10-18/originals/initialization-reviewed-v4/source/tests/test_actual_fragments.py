"""Compact real-source regressions, separately scoped from full primary proof."""
import json,sys,unittest,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from source_common import sha
from bs4 import BeautifulSoup
from model import semantics
from word_model import ordered_text
FIXTURES=Path(__file__).resolve().parents[1]/'fixtures'
class ActualFragments(unittest.TestCase):
 def test_retained_flagstaff_fee_table_cells_spans_and_amounts(self):
  m=next(x for x in json.loads((FIXTURES/'actual-fragments.json').read_text()) if x['fixture'].endswith('.html'));raw=(FIXTURES/m['fixture']).read_bytes();self.assertEqual(sha(raw),m['fixture_sha256']);table=semantics(BeautifulSoup(raw,'html.parser').table,m['source_url'])['tables'][0];self.assertEqual(table['rows'],m['expected_rows']);self.assertEqual(table['rows'][0][1]['text'],'Fees per Unit');self.assertEqual(table['rows'][0][1]['colspan'],'3');self.assertEqual(table['rows'][-1][-1]['text'],'$2,022')
 def test_retained_word_symbol_positions_are_not_globally_guessed(self):
  m=next(x for x in json.loads((FIXTURES/'actual-fragments.json').read_text()) if x['fixture'].endswith('.xml'));raw=(FIXTURES/m['fixture']).read_bytes();self.assertEqual(sha(raw),m['fixture_sha256']);text,images,notes=ordered_text(E.fromstring(raw));self.assertEqual(text,m['expected_text']);self.assertIn('70[SYMBOL F0B0] F. (21.1[SYMBOL F0B0] C)',text);self.assertEqual(len(images),0);self.assertEqual(m['images_members_opened'],0)
if __name__=='__main__':unittest.main()
