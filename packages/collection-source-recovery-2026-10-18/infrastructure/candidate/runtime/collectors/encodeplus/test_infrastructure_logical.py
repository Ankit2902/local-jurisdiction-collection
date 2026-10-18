"""Actual62-IR dispatch/identity/serialization faults; no image/network/native reparse."""
import copy,csv,gzip,io,json,pathlib,socket,unittest,tempfile
from unittest.mock import patch,Mock
from . import infrastructure_logical as m,native_document as native,pdf_structure
HERE=pathlib.Path(__file__).resolve().parent
class InfrastructurePrintedWorkflow(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.fixture=json.loads(gzip.decompress((HERE/'fixtures/infrastructure-printed-native/source-ir-and-native-inventory.json.gz').read_bytes()));cls.cfg=json.loads((HERE/'configs/native-82-0c6b3dc40877.json').read_text());cls.rows,cls.dim=m.project_records(cls.fixture['source_pages'],cls.fixture['native_inventory'],cls.cfg,'raw/start.pdf',list_witness=json.loads((HERE/'fixtures/infrastructure-printed-native/native-page26-list-witness.json').read_text()))
 def setUp(self):
  p=patch.object(socket,'socket',side_effect=AssertionError('No network'));p.start();self.addCleanup(p.stop)
 def test_actual172_units62_pages_5grids79cells_and_diagnostics(self):
  self.assertEqual(len(self.rows),172);self.assertEqual(self.rows[0]['unit_type'],'frontmatter');self.assertEqual(self.rows[1]['unit_type'],'table-of-contents');self.assertEqual(sum(r['unit_type']=='printed-heading-unit' for r in self.rows),170);self.assertEqual(self.dim['source_pages'],62);self.assertEqual(self.dim['source_control_blocks'],142);self.assertEqual(self.dim['all79_grid_cell_boundaries_and_spans_match_native_strokes'],True)
  native.validate_record_identity(self.rows,{'pages':62,'physical_page_count':62,'normalized_record_count':172,'canonical_record_unit':m.UNIT},self.cfg)
  self.assertTrue(all('physical_page' not in r for r in self.rows));self.assertEqual(sum(len(r['tables']) for r in self.rows),5)
 def test_exact_identity_and_route_refusals_with_source_digest_fixture(self):
  # Only the byte digest is simulated in this narrow identity-control test.
  # Actual native bytes/default build are independently exercised by the full proof.
  with patch.object(m.hashlib,'sha256',return_value=Mock(hexdigest=lambda:m.source.SHA)):
   self.assertTrue(m.matches(b'source-digest-fixture',self.cfg))
   for key,value in [('id','other'),('title','Other'),('url','https://example.gov/other'),('state','MO'),('jurisdiction','Other'),('expected_pages',63),('expected_sha256','0'*64)]:
    cfg=dict(self.cfg);cfg[key]=value
    with self.assertRaises(AssertionError):m.matches(b'source-digest-fixture',cfg)
 def test_changed_selected_config_refuses_before_transport_or_output(self):
  with tempfile.TemporaryDirectory() as td,patch.object(native,'cached',side_effect=AssertionError('Transport forbidden')) as transport:
   out=pathlib.Path(td)/'not-created';cfg=dict(self.cfg);cfg['url']='https://example.gov/other'
   with self.assertRaises(AssertionError):native.collect(cfg,out)
   self.assertFalse(out.exists());transport.assert_not_called()
 def test_changed_real_bytes_refuse_before_native_access(self):
  with patch('pypdf.PdfReader',side_effect=AssertionError('Must not parse wrong bytes')):
   with self.assertRaises(AssertionError):m.matches(b'%PDF-wrong edition',self.cfg)
 def test_all_canonical_source_field_mutations_refuse(self):
  for key,value in [('text','missing legal text'),('heading','invented'),('source_pages',[1]),('document_id','other'),('raw_sha256','0'*64),('raw_ref','other.pdf'),('state','MO'),('parent_id',self.rows[0]['id'])]:
   rows=copy.deepcopy(self.rows);rows[2][key]=value
   with self.assertRaises(AssertionError):m.validate_records(rows,self.cfg)
 def test_exact_native_metadata_is_preserved_and_cannot_mutate(self):
  self.assertEqual(self.rows[0]['source_document_evidence']['native_metadata'],m.SOURCE_METADATA);rows=copy.deepcopy(self.rows);rows[0]['source_document_evidence']['native_metadata']['/Title']='data:image/png;base64,bad'
  with self.assertRaises(AssertionError):m.validate_records(rows,self.cfg)
 def test_physical_page_identity_or_count_cannot_replace_units(self):
  for mutate in [lambda r:r.pop(),lambda r:r[1].update(physical_page=2),lambda r:r[1].update(page_count=172),lambda r:r[1].update(id=r[0]['id'])]:
   rows=copy.deepcopy(self.rows);mutate(rows)
   with self.assertRaises(AssertionError):native.validate_record_identity(rows,{'pages':62,'physical_page_count':62,'normalized_record_count':len(rows),'canonical_record_unit':m.UNIT},self.cfg)
 def test_original_inventory_page_diagnostics_and_false_gates_cannot_drift(self):
  for change in [lambda e:e['native_inventory']['outlines'][1].update(printed_title='other'),lambda e:e.update(edition_complete=True),lambda e:e.update(required_external_legal_dependencies_complete=True),lambda e:e.update(nested_list_hierarchy_qualified=True)]:
   rows=copy.deepcopy(self.rows);change(rows[0]['source_document_evidence'])
   with self.assertRaises(AssertionError):m.validate_records(rows,self.cfg)
  rows=copy.deepcopy(self.rows);rows[0]['superseded_detector_diagnostics']['original_page_records'][11]['text']='changed'
  with self.assertRaises(AssertionError):m.validate_records(rows,self.cfg)
 def test_primary_and_sidecars_csv_json_export172not62(self):
  out=native.outputs(self.rows);j=[json.loads(x) for x in out['records.jsonl'].decode().splitlines()];c=list(csv.DictReader(io.StringIO(out['records.csv'].decode())));self.assertEqual(len(j),len(c));self.assertEqual(len(j),172)
  for a,b in zip(j,c):self.assertEqual(a['text'],b['text']);self.assertEqual(a['source_pages'],json.loads(b['source_pages']));self.assertEqual(b['physical_page'],'')
  self.assertEqual(len(out['infrastructure-source-page-diagnostics.jsonl'].splitlines()),62);self.assertIn('infrastructure-source-inventory.json',out);self.assertEqual(sum(r['text'].count('[IMAGE]') for r in j),5)
 def test_serialization_rejects_corrupt_source_unit_before_output(self):
  rows=copy.deepcopy(self.rows);rows[1]['text']='corrupt'
  with self.assertRaises(AssertionError):native.outputs(rows)
 def test_ordinary_generic_profile_and_csv_are_unchanged(self):
  six=[json.loads(x) for x in (HERE/'fixtures/sto-four-column/ordinary-solid-waste-baseline.jsonl').read_text().splitlines()];body=(HERE/'fixtures/overland-solid-waste-native.pdf').read_bytes();cfg=json.loads((HERE/'configs/native-82-4b983dc51ab6.json').read_text())
  with patch('collectors.encodeplus.solid_waste_logical.matches',return_value=False),patch.object(pdf_structure,'pages',return_value=(six,[])):
   rows,details=native.page_records(body,cfg)
  self.assertEqual(rows,six);self.assertEqual(details['pages'],6);self.assertFalse(details['pdf_table_semantics_complete']);self.assertEqual(list(csv.DictReader(io.StringIO(native.outputs(six)['records.csv'].decode())))[0]['physical_page'],'1')
if __name__=='__main__':unittest.main(verbosity=2)
