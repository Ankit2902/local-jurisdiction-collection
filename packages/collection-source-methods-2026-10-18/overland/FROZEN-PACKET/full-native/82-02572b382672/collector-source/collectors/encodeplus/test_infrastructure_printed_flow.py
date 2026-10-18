"""Portable entire62-page cached-source flow/structure qualification and faults."""
import ast,copy,gzip,json,socket,unittest
from pathlib import Path
from unittest.mock import patch
from . import infrastructure_logical as logical
from . import infrastructure_printed_flow as flow
HERE=Path(__file__).resolve().parent
class PrintedFlow(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  d=json.loads(gzip.decompress((HERE/'fixtures/infrastructure-printed-native/source-ir-and-native-inventory.json.gz').read_bytes()));cls.pages=d['source_pages'];cls.inventory=d['native_inventory'];cls.cfg=json.loads((HERE/'configs/native-82-0c6b3dc40877.json').read_text());cls.witness=json.loads((HERE/'fixtures/infrastructure-printed-native/native-page26-list-witness.json').read_text())
  with patch.object(socket,'socket',side_effect=AssertionError('Offline')):cls.records,cls.dim=logical.project_records(cls.pages,cls.inventory,cls.cfg,'raw/start.pdf',logical.SOURCE_METADATA,cls.witness)
 def test_entire_source_and_positive_scoped_topology(self):
  s=self.dim['source_printed_flow_dimensions'];self.assertEqual((len(self.records),s['pages'],s['source_fragments'],s['source_words']),(172,62,1776,18662));self.assertEqual((s['source_list_groups'],s['literal_marker_items'],s['source_explicit_nonlist_dispositions']),(19,85,8));self.assertTrue(s['source_literal_block_list_topology_qualified']);self.assertEqual(s['independent_native_line_geometry_queries'],68);self.assertEqual(s['unresolved_counts'],{'cross_page_paragraph_boundary':38});self.assertFalse(s['publication_complete'])
 def test_whole_source_render_reconstructs(self):logical.validate_records(self.records,self.cfg);self.assertEqual(logical.outputs(self.records),logical.outputs(copy.deepcopy(self.records)))
 def test_all_source_leaf_and_image_ownership(self):
  ls=[x for r in self.records for x in flow.walk({'kind':'root','children':r['ordered_blocks']})];self.assertEqual(len(ls),1776);self.assertEqual(len({x['id']for x in ls}),1776);ids=[w for x in ls for w in x['word_ids']];self.assertEqual(len(ids),len(set(ids)));self.assertEqual(len(ids),18662);self.assertEqual(sum(r['html'].count('[IMAGE]')for r in self.records),5)
 def test_invented_HTML_fails_canonical_verifier(self):
  x=copy.deepcopy(self.records);x[5]['html']+='<p>Invented legal text</p>'
  with self.assertRaisesRegex(AssertionError,'canonical/diagnostic'):logical.validate_records(x,self.cfg)
 def test_active_image_HTML_never_passes_source_reconstruction(self):
  x=copy.deepcopy(self.records);x[54]['html']+='<img src="data:image/png;base64,DO_NOT_DECODE">'
  with self.assertRaises(AssertionError):logical.validate_records(x,self.cfg)
 def test_false_qualification_lift_refused(self):
  x=copy.deepcopy(self.records);x[54]['source_printed_flow_evidence']['whole_publication_qualified']=True
  with self.assertRaises(AssertionError):logical.validate_records(x,self.cfg)
 def test_diagnostic_corruption_not_hidden(self):
  x=copy.deepcopy(self.records);x[2]['superseded_printed_flow_diagnostics']['original_fields']['text']+='wrong'
  with self.assertRaises(AssertionError):logical.validate_records(x,self.cfg)
 def test_wrong_native_source_pages_refuse(self):
  pages=copy.deepcopy(self.pages);pages[10]['raw_sha256']='0'*64
  with self.assertRaises(AssertionError):logical.project_records(pages,self.inventory,self.cfg,'raw/start.pdf',logical.SOURCE_METADATA,self.witness)
 def test_missing_corrupt_geometry_failclosed(self):
  with patch.object(flow.Path,'read_bytes',side_effect=FileNotFoundError('Absent witness')):
   with self.assertRaises(FileNotFoundError):flow.load_geometry()
  with patch.object(flow.Path,'read_bytes',return_value=b'{}'):
   with self.assertRaisesRegex(AssertionError,'geometry corrupt'):flow.load_geometry()
 def test_geometry_word_or_text_changes_refuse(self):
  g=flow.load_geometry();fid=next(iter(g));f=next(x for r in self.records for x in flow.walk({'kind':'root','children':r['ordered_blocks']})if x['id']==fid);f=copy.deepcopy(f)
  for changed in ['text','word']:
   wrong=copy.deepcopy(g[fid])
   if changed=='text':wrong['lines'][0]['text']+='invented'
   else:wrong['lines'][0]['words'][0]['id']='foreign-word'
   with self.subTest(changed=changed),self.assertRaises(AssertionError):flow.qualify_source_lines(f,wrong)
 def test_profile_helpers_no_network_native_image_imports(self):
  for name in ['infrastructure_printed_flow.py','infrastructure_flow_inventory.py']:
   tree=ast.parse((HERE/name).read_text());imports=[n.module for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names];self.assertFalse(any((n or'').split('.')[0]in ['socket','requests','urllib','PIL','pdfplumber','pypdfium2','pypdf','fitz','playwright']for n in imports))
if __name__=='__main__':unittest.main()
