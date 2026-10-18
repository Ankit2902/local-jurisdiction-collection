"""Retained actual whole6 source integration/native-workflow faults; no repeated nativeparse."""
import copy,csv,gzip,hashlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from . import native_document as n,solid_waste_logical as s
H=Path(__file__).resolve().parent;F=H/'fixtures/solid-waste-logical'
class Logical(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.cfg=json.loads((H/'configs/native-82-4b983dc51ab6.json').read_text());c.data=(F/'source.pdf').read_bytes();c.rows=[json.loads(l) for l in gzip.decompress((F/'captured-records.jsonl.gz').read_bytes()).decode().splitlines()];c.details=json.loads((F/'captured-details.json').read_text())
 def test_actual88_units_6pages_complete_evidence(self):
  n.validate_record_identity(self.rows,self.details,self.cfg);e=self.rows[0]['source_document_evidence'];self.assertEqual((len(self.rows),self.details['pages'],len(e['source_controls']),len(e['source_glyphs']),len(e['source_tags']['references'])),(88,6,26,15574,109));self.assertEqual(len(self.rows[0]['superseded_detector_diagnostics']['original_page_records']),6)
 def test_canonical_JSON_CSV_sourcepages_and_control_sidecars(self):
  out=n.outputs(self.rows);self.assertEqual([json.loads(l) for l in out['records.jsonl'].decode().splitlines()],self.rows);csvrows=list(csv.DictReader(io.StringIO(out['records.csv'].decode())));self.assertEqual(len(csvrows),88)
  for a,b in zip(csvrows,self.rows):self.assertEqual(a['text'],b['text']);self.assertEqual(json.loads(a['source_pages']),b['source_pages']);self.assertEqual(a['physical_page'],'')
  self.assertEqual(len(out['source-page-diagnostics.jsonl'].decode().splitlines()),6);self.assertEqual(len(out['source-controls.jsonl'].decode().splitlines()),26)
 def test_other_source_noop_and_generic_export_unchanged(self):
  self.assertFalse(s.matches(b'Other source',dict(self.cfg,expected_sha256='0'*64)));old=self.rows[0]['superseded_detector_diagnostics']['original_page_records'];out=n.outputs(old);self.assertEqual(set(out),{'records.jsonl','records.csv'});self.assertEqual(list(csv.DictReader(io.StringIO(out['records.csv'].decode())))[0]['physical_page'],'1')
 def test_wrong_source_edition_config_or_owner_refuses(self):
  for data in [self.data+b'\n',self.data[:100]+b'X'+self.data[101:]]:
   with self.assertRaises(AssertionError):s.matches(data,self.cfg)
  for k,v in [('id','wrong'),('url','https://wrong.invalid'),('title','Wrong book'),('state','MO'),('jurisdiction','Wrong city'),('expected_pages',88),('expected_sha256','0'*64)]:
   cfg=dict(self.cfg);cfg[k]=v
   with self.assertRaises(AssertionError):s.matches(self.data,cfg)
 def test_count_identity_fake_physical_page_refuses(self):
  for change in ['missing','duplicate','owner','page','pagecount']:
   rows=copy.deepcopy(self.rows);d=copy.deepcopy(self.details)
   if change=='missing':rows.pop(20)
   elif change=='duplicate':rows[20]=rows[19]
   elif change=='owner':rows[20]['document_id']='wrong'
   elif change=='page':rows[20]['physical_page']=3
   else:d['pages']=88
   with self.assertRaises(AssertionError):n.validate_record_identity(rows,d,self.cfg)
 def test_text_parent_crosspage_or_missing_evidence_refuses(self):
  for change in ['text','parent','crosspage','control','glyph','dependency']:
   rows=copy.deepcopy(self.rows);x=next(r for r in rows if r['logical_key']=='7.36-5.D');e=rows[0]['source_document_evidence']
   if change=='text':x['text']='invented'
   elif change=='parent':x['parent_id']='wrong'
   elif change=='crosspage':x['source_pages']=[5]
   elif change=='control':e['source_controls'].pop()
   elif change=='glyph':e['source_glyphs'].pop()
   else:e['qualification']['required_external_legal_dependencies_complete']=True
   with self.assertRaises(AssertionError):s.validate_records(rows,self.cfg)
 def test_mixed_generic_and_logical_CSV_unambiguous(self):
  old=copy.deepcopy(self.rows[0]['superseded_detector_diagnostics']['original_page_records'][0]);old['id']='unrelated::page:1';old['document_id']='unrelated';mixed=[old]+copy.deepcopy(self.rows);out=n.outputs(mixed);cs=list(csv.DictReader(io.StringIO(out['records.csv'].decode())));self.assertEqual(len(cs),89);self.assertEqual(cs[0]['physical_page'],'1');self.assertEqual(cs[1]['physical_page'],'');self.assertEqual([r['text'] for r in cs],[r['text'] for r in mixed]);self.assertEqual(json.loads(out['records.jsonl'].decode().splitlines()[0]),old)
 def checkpoint(self,root):
  from .util import hash_json
  cfg=copy.deepcopy(self.cfg);versions=n.code_hashes();(root/'raw').mkdir();(root/'script-versions').mkdir()
  for name,h in versions.items():(root/'script-versions'/(h+Path(name).suffix)).write_bytes((H/name).read_bytes())
  h=hashlib.sha256(self.data).hexdigest();entries={}
  for key in ['start','end']:
   p=root/'raw'/(key+'.pdf');p.write_bytes(self.data);meta={'url':cfg['url'],'http_status':200,'sha256':h,'challenge':False,'scope':'offline retained-source fixture, not live acquisition'};p.with_name(p.name+'.receipt.json').write_text(json.dumps(meta));entries[key]={'path':'raw/'+key+'.pdf','url':cfg['url'],'sha256':h}
  (root/'checkpoint.json').write_text(json.dumps({'config':cfg,'config_sha256':hash_json(cfg),'code_hashes':versions,'phase':'finished',**entries}))
  for name,body in n.outputs(self.rows).items():(root/name).write_bytes(body)
 def test_current_native_verify_scope_counts_and_owntext(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);self.checkpoint(root)
   with patch.object(n,'page_records',return_value=(copy.deepcopy(self.rows),copy.deepcopy(self.details))):r=n.verify(root)
   self.assertTrue(r['native_document_complete']);self.assertEqual(r['physical_pages'],6);self.assertEqual(r['normalized_record_count'],88);self.assertTrue(r['publication_text_complete']);self.assertTrue(r['source_logical_structure_qualified']);self.assertFalse(r['attachments_complete']);self.assertFalse(r['publication_complete']);self.assertFalse(r['edition_complete']);self.assertFalse(r['required_external_legal_dependencies_complete'])
 def test_current_native_verify_source_CSV_controls_identity_faults(self):
  for change in ['source','CSV','controls','checkpoint']:
   with tempfile.TemporaryDirectory() as td:
    root=Path(td);self.checkpoint(root)
    if change=='source':(root/'raw/start.pdf').write_bytes(self.data+b'\n')
    elif change=='CSV':p=root/'records.csv';p.write_text(p.read_text().replace('2011','2099',1))
    elif change=='controls':(root/'source-controls.jsonl').write_text('')
    else:p=root/'checkpoint.json';v=json.loads(p.read_text());v['config']['expected_pages']=88;p.write_text(json.dumps(v))
    with patch.object(n,'page_records',return_value=(copy.deepcopy(self.rows),copy.deepcopy(self.details))):r=n.verify(root)
    self.assertFalse(r['native_document_complete']);self.assertTrue(r['errors'])
if __name__=='__main__':unittest.main(verbosity=2)
