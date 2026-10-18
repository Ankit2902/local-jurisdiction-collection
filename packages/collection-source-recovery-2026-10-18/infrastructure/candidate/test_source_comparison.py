"""Whole-source deterministic projection and source-sensitive refusal tests."""
import copy,gzip,hashlib,json,tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'runtime'))
from collectors.encodeplus.infrastructure_flow_inventory import inventory
from collectors.encodeplus.infrastructure_printed_flow import project,project_record,walk,outputs
def project_source(data):
 assert hashlib.sha256(data).hexdigest()=='8bf0cf6e1d319d900fbdafff16dd8f051e945f39a6102aaad035fe3a4001afe9','Source identity/version/hash differs'
 return project([json.loads(l)for l in data.decode().split('\n')if l])
class WholeSource(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.data=gzip.decompress((H/'evidence/baseline-records.jsonl.gz').read_bytes());c.old=[json.loads(x)for x in c.data.decode().split('\n')if x];c.rows,c.summary=project_source(c.data)
 def test_all_units_primary_text_word_ownership_and_diagnostics(self):
  self.assertEqual((len(self.rows),self.summary['source_fragments'],self.summary['source_words']),(172,1776,18662));self.assertEqual(self.summary['literal_marker_items'],85);self.assertEqual(self.summary['source_list_groups'],19);self.assertEqual(self.summary['IMAGE_count'],5)
  for a,b in zip(self.old,self.rows):self.assertEqual(a['text'],b['text']);self.assertEqual(a['tables'],b['tables']);self.assertEqual(a['source_fragments'],b['source_fragments']);self.assertEqual(b['superseded_printed_flow_diagnostics']['original_fields']['ordered_blocks'],a['ordered_blocks'])
 def test_source_cache_wrong_byte_version_edition_refused_before_projection(self):
  for data in [self.data+b' ',self.data.replace(b'Overland',b'Another',1),self.data[:200]]:
   with self.subTest(length=len(data)),patch(__name__+'.project',side_effect=AssertionError('Should not project')):
    with self.assertRaisesRegex(AssertionError,'identity/version/hash'):project_source(data)
 def test_missing_fragment_and_duplicate_word_fail(self):
  a=copy.deepcopy(self.old);a[2]['source_fragments'].pop()
  with self.assertRaises(AssertionError):project(a)
  a=copy.deepcopy(self.old);fs=[f for r in a for f in r['source_fragments']if f['block'].get('word_ids')];fs[1]['block']['word_ids'][0]=fs[0]['block']['word_ids'][0]
  with self.assertRaises(AssertionError):project(a)
 def test_reordered_whole_source_not_silently_normalized(self):
  a=copy.deepcopy(self.old);a[2]['source_fragments'][1:3]=list(reversed(a[2]['source_fragments'][1:3]))
  with self.assertRaisesRegex(AssertionError,'Canonical text differs'):project(a)
 def test_grid_char_loss_refused_not_hidden_as_spacing(self):
  a=copy.deepcopy(self.old);t=next(t for r in a for t in r['tables']);t['cells'][0]['text']+=' LOST_OR_INVENTED'
  with self.assertRaisesRegex(AssertionError,'nonwhitespace character'):project(a)
 def test_same_indent_sequence_gap_explicitly_unresolved(self):
  a=copy.deepcopy(self.old);r=a[56];f=next(f for f in r['source_fragments']if f['block']['text'].startswith('b) '));f['block']['text']='z) '+f['block']['text'][3:];r['text']='\n'.join(f['block']['text']for f in r['source_fragments']);inv=inventory(a);by=[f for f in inv['fragments']if f['unit_id']==r['id']];out=project_record(r,by);self.assertTrue(any(x['kind']=='ordered_marker_sequence_gap'for x in out['source_printed_flow_evidence']['unresolved']));self.assertFalse(out['source_printed_flow_evidence']['whole_publication_qualified'])
 def test_no_phone_measurement_or_acronym_promoted_and_crosspage_not_waived(self):
  self.assertEqual(self.summary['unresolved_counts'],{'cross_page_paragraph_boundary':38});self.assertEqual(self.summary['source_explicit_nonlist_dispositions'],8);self.assertTrue(self.summary['source_literal_block_list_topology_qualified']);self.assertEqual(self.rows[32]['source_printed_flow_evidence']['literal_marker_items'],0);self.assertIn('(913)',self.rows[32]['html']);self.assertFalse(self.summary['paragraph_continuation_semantics_complete']);self.assertFalse(self.summary['publication_complete'])
 def test_every_multiline_heading_one_header_and_SOURCE_IMAGE_exact(self):
  for a,b in zip(self.old,self.rows):self.assertEqual(b['html'].count('<h2 '),bool(a['source_outline']));self.assertNotIn('<img',b['html']);self.assertNotIn('<svg',b['html']);self.assertEqual(b['html'].count('[IMAGE]'),a['text'].count('[IMAGE]'))
 def test_deterministic_export_replay(self):
  x,s=project_source(self.data);self.assertEqual(outputs(x),outputs(self.rows));self.assertEqual(s,self.summary)
if __name__=='__main__':unittest.main()
