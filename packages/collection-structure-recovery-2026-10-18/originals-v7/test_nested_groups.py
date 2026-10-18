import sys,unittest,base64
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'source'))
from flagstaff_html_normalize import parse
from bs4 import BeautifulSoup
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
if __name__=='__main__':unittest.main()
