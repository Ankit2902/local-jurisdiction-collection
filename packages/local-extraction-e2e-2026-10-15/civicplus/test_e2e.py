import copy,json,tempfile,unittest
from pathlib import Path
from review_pdf import apply_review
import civicplus as cp
HERE=Path(__file__).resolve().parent
class ReviewedPdfTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=HERE/'live-e2e/qa/portland-ch13-fresh.pdf'
  cls.pages,cls.blocks,cls.issues=cp.extract_document(cls.raw,'portland')
 def apply(self):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);dest=Path(tmp.name);(dest/'raw').mkdir()
  return apply_review(HERE/'reviewed-recoveries.json','b4305bca-b7ef-4d12-b84f-5554626b4b81',cp.sha(self.raw.read_bytes()),self.pages,self.blocks,self.issues,dest)
 def test_reviewed_subcolumns_have_real_header_hierarchy(self):
  _,blocks,_,_=self.apply();b=next(x for x in blocks if x.get('review_id')=='portland-p37-rent-columns')
  self.assertIn('<th colspan="2">Unheated</th>',b['html']);self.assertIn('<td>264</td><td>1134</td>',b['html']);self.assertNotIn('<pre>',b['html'])
 def test_continued_food_table_bound_to_both_source_pages(self):
  _,blocks,_,_=self.apply();b=next(x for x in blocks if x.get('review_id')=='portland-p37-p38-food-continuation')
  self.assertEqual([x['page'] for x in b['source_fragments']],[37,38]);self.assertEqual(len(b['rows']),9)
  self.assertIn('<td>2</td><td>7.00</td><td>49.00</td><td>203.00</td>',b['html'])
  self.assertEqual(b['html'].count('Number in Household'),1);self.assertFalse(any(x['kind']=='table' and x['page']==38 and abs(x['bbox'][1]-116.96)<.02 for x in blocks))
 def test_visible_missing_line_recovers_readable_words_and_preserves_unknown_symbol(self):
  _,blocks,issues,events=self.apply();line=next(b for b in blocks if b.get('review_id')=='portland-p48-visible-line')
  self.assertEqual(line['text'],'abatement process under 36 M.R.S.A. [UNREADABLE SYMBOL] 841(2) and through');self.assertTrue(any(b['kind']=='image' and b['page']==48 for b in blocks));self.assertTrue(any(i['condition']=='unreadable_source_symbol_after_reviewed_transcription' for i in issues));self.assertEqual(len(events),3)
 def test_stale_review_never_applies_to_changed_pdf(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaisesRegex(ValueError,'source hash mismatch'):apply_review(HERE/'reviewed-recoveries.json','b4305bca-b7ef-4d12-b84f-5554626b4b81','0'*64,self.pages,self.blocks,self.issues,Path(td))
 def test_changed_source_cells_reject_reviewed_table_override(self):
  bad=copy.deepcopy(self.blocks);next(b for b in bad if b['kind']=='table' and b['page']==37)['rows'][1][0]='changed'
  with tempfile.TemporaryDirectory() as td:
   (Path(td)/'raw').mkdir()
   with self.assertRaisesRegex(ValueError,'cells changed'):apply_review(HERE/'reviewed-recoveries.json','b4305bca-b7ef-4d12-b84f-5554626b4b81',cp.sha(self.raw.read_bytes()),self.pages,bad,self.issues,Path(td))
if __name__=='__main__':unittest.main(verbosity=2)
