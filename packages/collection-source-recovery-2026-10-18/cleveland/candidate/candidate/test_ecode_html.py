"""Actual acquired-source projection faults; no fixtures are promoted municipal law."""
import copy,json,sys,unittest,base64,socket,subprocess
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import ecode_html as ec
from common import artifacts,canonical,check_html,sha,validate_projection

ROOT=Path(sys.argv[1]);PROOF=Path(sys.argv[2]);sys.argv=sys.argv[:1]
class ActualReader(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.proof=json.loads(PROOF.read_text());cls.family=json.loads((PROOF.parent/'family-verification.json').read_text());cls.records=ec.lines(ROOT/'records.jsonl');cls.nodes=ec.load(ROOT/'inventory.json');cls.disps=ec.load(ROOT/'dispositions.json')
  cls.guards=[]
  def no(*a,**k):raise AssertionError('Network/process/image decode prohibited')
  for obj,name in [(socket,'create_connection'),(socket.socket,'connect'),(subprocess,'Popen'),(base64,'b64decode'),(Image,'open')]:
   g=patch.object(obj,name,no);g.start();cls.guards.append(g)
  cls.projection=ec.read_projection(ROOT,cls.proof,cls.family)
 @classmethod
 def tearDownClass(cls):
  for g in reversed(cls.guards):g.stop()
 def test_actual_all_acquired_rows_and_dispositions(self):
  p=self.projection;validate_projection(p);self.assertEqual((len(p.rows),len(p.nodes),len(p.dispositions)),(3006,3253,3253));self.assertEqual(sum(len(d['record_ids']) for d in p.dispositions),3006)
 def test_exact_canonical_notes_tables_and_original_ordinal(self):
  for row,pr in zip(self.projection.rows,self.projection.provenance):
   r=self.records[pr['rich_ir']['line_ordinal']];self.assertEqual(row['full_text'],r['semantic_html']);self.assertEqual(pr['notes_html'],r['notes_html']);self.assertEqual(pr['tables_html'],r['tables_html']);self.assertEqual(pr['rich_ir']['record_sha256'],sha(canonical(r)))
 def test_literal_source_order_not_GUID_sort(self):
  positions=[int(p['source_order_witness']['literal_data_position']) for p in self.projection.provenance];self.assertEqual(positions,sorted(positions));self.assertEqual(len(positions),len(set(positions)));self.assertNotEqual([p['rich_ir']['line_ordinal'] for p in self.projection.provenance],list(range(3006)))
 def test_false_publication_gates_and_6missingdocuments(self):
  p=self.projection;d=json.loads(artifacts(p)['validation-report.json']);self.assertFalse(d['complete']);self.assertFalse(d['downstream_ready']);self.assertFalse(p.inherited_coverage['complete']);self.assertEqual(len(p.inherited_coverage['missing_assets']),6);self.assertFalse(p.inherited_coverage['start_end_inventory_consistent'])
 def test_exact_28IMAGE_and_inert_HTML(self):
  self.assertEqual(sum(row['full_text'].count('[IMAGE]') for row in self.projection.rows),28)
  for row in self.projection.rows:check_html(row['full_text'])
 def test_missing_owned_body_fails(self):
  with patch.object(ec,'lines',return_value=self.records[:-1]):
   with self.assertRaisesRegex(ValueError,'Missing/duplicate acquired body'):ec.read_projection(ROOT,self.proof,self.family)
 def test_missing_source_disposition_fails(self):
  original=ec.load
  def altered(path):return self.disps[:-1] if Path(path).name=='dispositions.json' else original(path)
  with patch.object(ec,'load',side_effect=altered):
   with self.assertRaisesRegex(ValueError,'Missing/duplicate source descriptor'):ec.read_projection(ROOT,self.proof,self.family)
 def test_corrupt_family_proof_fails(self):
  proof=copy.deepcopy(self.proof);proof['verification']['family_report_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'Wrong family verification payload'):ec.read_projection(ROOT,proof,self.family)
 def test_corrupt_raw_fails(self):
  def refused(*a,**k):raise ValueError('Corrupt raw source')
  with patch.object(ec,'raw',side_effect=refused):
   with self.assertRaisesRegex(ValueError,'Corrupt raw'):ec.read_projection(ROOT,self.proof,self.family)
 def test_wrong_source_revision_fails(self):
  proof=copy.deepcopy(self.proof);proof['collector_sources_before']['adapters.py']='0'*64;proof['collector_sources_after']=dict(proof['collector_sources_before'])
  with self.assertRaisesRegex(ValueError,'Wrong explicitly selected'):ec.read_projection(ROOT,proof,self.family)
 def test_image_in_canonical_body_fails(self):
  p=copy.deepcopy(self.projection);p.rows[0]['full_text']='<img src="data:application/octet-stream;base64,NEVER_DECODE">';p.provenance[0]['corpus_row_sha256']=sha(canonical(p.rows[0]))
  with self.assertRaisesRegex(ValueError,'Active image'):artifacts(p)
 def test_foreign_municipal_family_fails(self):
  proof=copy.deepcopy(self.proof);proof['family']='municipal.codes'
  with self.assertRaisesRegex(ValueError,'Unsupported verification'):ec.read_projection(ROOT,proof,self.family)
 def test_recursive_note_image_metadata_fails(self):
  p=copy.deepcopy(self.projection);p.provenance[0]['notes_html']=['<p data-pixel="DATA:IMAGE/PNG;base64,QUJD\nPIXEL_CONTINUATION">Legal caption</p>']
  with self.assertRaisesRegex(ValueError,'Image payload'):artifacts(p)
 def test_recursive_opaque_image_metadata_fails(self):
  p=copy.deepcopy(self.projection);p.provenance[0]['image_references']=[{'tag':'image','source':{'url':'data:application/octet-stream;base64,NEVER_DECODE'}}]
  with self.assertRaisesRegex(ValueError,'Opaque data payload'):artifacts(p)
if __name__=='__main__':unittest.main()
