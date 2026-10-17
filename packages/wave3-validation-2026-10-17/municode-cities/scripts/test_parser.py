"""Network-free regressions for observed parser review issues; source table QA is separate."""
import sys
sys.dont_write_bytecode=True
import unittest
from normalize import LegalHTML
class ParserRegression(unittest.TestCase):
 def test_cells_remain_separate_in_search_text(self):
  p=LegalHTML();p.feed('<table><tr><th>Unit</th><th>Rate</th></tr><tr><td>Family</td><td>100</td></tr></table>');text=p.parsed();self.assertNotIn('UnitRate',text);self.assertNotIn('Family100',text);self.assertIn('Family',text);self.assertIn('100',text)
 def test_nested_table_restores_outer_tail_cell_and_row(self):
  p=LegalHTML();p.feed('<table><tr><td>A<table><tr><td>N</td></tr></table>Z</td><td>B</td></tr><tr><td>C</td></tr></table>');p.parsed();self.assertEqual(p.tables[0][0][0]['text'],'A N Z');self.assertEqual(p.tables[0][0][1]['text'],'B');self.assertEqual(p.tables[0][1][0]['text'],'C');self.assertEqual(p.tables[1][0][0]['text'],'N')
 def test_internal_link_attributes_and_linebreaks(self):
  p=LegalHTML();p.feed('<table><tr><td rowspan="2" colspan="3">Include/<br>Omit<a data-nodeid="X" data-linktype="internal">§1</a></td></tr></table>');p.parsed();self.assertEqual(p.tables[0][0][0]['text'],'Include/ Omit§1');self.assertEqual(p.tables[0][0][0]['rowspan'],'2');self.assertEqual(p.links[0]['target_node_id'],'X')
if __name__=='__main__':unittest.main(verbosity=2)
