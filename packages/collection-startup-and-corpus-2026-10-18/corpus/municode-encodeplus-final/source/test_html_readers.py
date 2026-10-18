"""Actual retained-book reader tests; no parser/browser/PDF work or network."""
import copy,json,socket,tempfile,unittest,os,shutil
from pathlib import Path
from unittest.mock import patch
import common,reader_utils,municode_html,encodeplus_html,package
HERE=Path(__file__).resolve().parent;OUTER=Path(os.environ.get('CORPUS_READERS_FIXTURES',str(HERE.parent)))
INPUTS={n:OUTER/'packages'/n/'evidence/input' for n in ['henderson','charter']}
MODS={'henderson':municode_html,'charter':encodeplus_html}

def data(name):
 return common.load(OUTER/(name+'-proof/read-only-proof.json')),common.load(OUTER/(name+'-proof/family-verification.json'))
def projection(name):return MODS[name].read_projection(INPUTS[name],*data(name))
class Readers(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.network=patch.object(socket.socket,'connect',side_effect=AssertionError('No network'))
  cls.network.start();cls.projections={n:projection(n) for n in INPUTS}
 @classmethod
 def tearDownClass(cls):cls.network.stop()
 def test_actual_complete_inventory_body_disposition(self):
  for name,counts in [('henderson',(2122,2123)),('charter',(188,188))]:
   with self.subTest(name=name):
    p=self.projections[name];common.validate_projection(p)
    self.assertEqual((len(p.rows),len(p.nodes)),counts)
    self.assertEqual(len(p.dispositions),len(p.nodes));self.assertEqual(len({x['record_id'] for x in p.provenance}),len(p.rows))
 def test_available_source_hierarchy_not_blank(self):
  p=self.projections['henderson'];self.assertEqual(sum(bool(x['section_number']) for x in p.rows),1913);self.assertEqual(sum(bool(x['chapter']) for x in p.rows),1997)
  p=self.projections['charter'];self.assertEqual(sum(bool(x['section_number']) for x in p.rows),171);self.assertEqual(sum(bool(x['article']) for x in p.rows),181)
 def test_charter_observed_order_not_numeric_export_sort(self):
  p=self.projections['charter'];ids=[x['record_id'].split(':')[-1] for x in p.provenance]
  cp=common.load(INPUTS['charter']/'checkpoint.json');self.assertEqual(ids,[str(i) for b in cp['blocks'] for i in b['record_ids']]);self.assertLess(ids.index('950'),ids.index('944'))
 def test_exact_canonical_html_and_parent_owned_bodies(self):
  for name,p in self.projections.items():
   rs=reader_utils.lines(INPUTS[name]/('publications/14896/sections.jsonl' if name=='henderson' else 'records.jsonl'))
   rm={str(r['node_id'] if name=='henderson' else r['id']):r for r in rs}
   for row,pr in zip(p.rows,p.provenance):
    r=rm[pr['record_id'].split(':')[-1]];self.assertEqual(row['full_text'],r['html' if name=='henderson' else 'body_html'])
   self.assertTrue(any(x.get('parent_source_id') for x in p.provenance))
  self.assertTrue(any(x['source_kind']=='source_parent_with_owned_body' for x in self.projections['henderson'].provenance))
 def test_false_gates_and_source_version_unchanged(self):
  for n,p in self.projections.items():
   self.assertEqual(p.inherited_coverage,common.load(INPUTS[n]/'coverage.json'))
   self.assertFalse(p.inherited_coverage['jurisdiction_complete'])
   self.assertFalse(json.loads(common.artifacts(p)['validation-report.json'])['downstream_ready'])
 def changed_records(self,n,change):
  mod=MODS[n];real=mod.lines
  def altered(path):
   values=copy.deepcopy(real(path));change(values);return values
  return patch.object(mod,'lines',side_effect=altered)
 def test_duplicate_body_refused(self):
  for n in INPUTS:
   with self.subTest(n=n),self.changed_records(n,lambda rs:rs.append(copy.deepcopy(rs[0]))),self.assertRaises(ValueError):projection(n)
 def test_missing_body_refused(self):
  for n in INPUTS:
   with self.subTest(n=n),self.changed_records(n,lambda rs:rs.pop()),self.assertRaises(ValueError):projection(n)
 def test_wrong_parent_or_hierarchy_refused(self):
  for n in INPUTS:
   def wrong(rs):next(r for r in rs if r.get('parent_id'))['parent_id']='FOREIGN'
   with self.subTest(n=n),self.changed_records(n,wrong),self.assertRaises(ValueError):projection(n)
 def test_wrong_source_version_refused(self):
  def wrong(rs):rs[0]['job_id']+=1
  with self.changed_records('henderson',wrong),self.assertRaises(ValueError):projection('henderson')
  proof,family=data('charter');family['inventory_sha256']='0'*64
  with self.assertRaises(ValueError):encodeplus_html.read_projection(INPUTS['charter'],proof,family)
 def test_unknown_native_or_body_format_refused(self):
  for n in INPUTS:
   def wrong(rs):rs[0]['doc_type']=99;rs[0]['kind']='native_pdf_page'
   with self.subTest(n=n),self.changed_records(n,wrong),self.assertRaises(ValueError):projection(n)
 def test_municode_separate_notes_fail_closed_instead_of_omitted(self):
  for field,value in [('notes',{'NoteContent':'available legal note'}),('footnotes_html','<p>available legal footnote</p>')]:
   def wrong(rs):rs[0][field]=value
   with self.subTest(field=field),self.changed_records('henderson',wrong),self.assertRaisesRegex(ValueError,'separate Notes/Footnotes'):projection('henderson')
 def test_raw_separate_notes_present_but_old_ir_empty_refused(self):
  # Adversarial source-backed mutation: keep stored normalized notes empty and
  # rebind raw byte hashes. This is NOT a new successful verification proof.
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'input';shutil.copytree(INPUTS['henderson'],root)
   proof,family=data('henderson');cp=common.load(root/'checkpoint.json');pub=next(iter(cp['publications'].values()));name=pub['content_units'][0];u=cp['units'][name];receipt_path=root/u['receipt'];receipt=common.load(receipt_path);body=root/receipt['body_file'];original=body.read_bytes()
   for key in ['Notes','Footnotes']:
    docs=json.loads(original);docs[0][key]='RAW LEGAL NOTE WHICH OLD NORMALIZED IR DID NOT EMIT';body.write_bytes(common.encoded(docs));h=common.file_hash(body);u['sha256']=h;receipt['sha256']=h;receipt_path.write_bytes(common.encoded(receipt));(root/'checkpoint.json').write_bytes(common.encoded(cp))
    attacked=copy.deepcopy(proof);attacked['evidence_sha256_before']=common.files(root);attacked['evidence_sha256_after']=copy.deepcopy(attacked['evidence_sha256_before'])
    with self.subTest(raw_field=key),self.assertRaisesRegex(ValueError,'separate Notes/Footnotes'):
     municode_html.read_projection(root,attacked,family)
 def test_raw_structural_landing_notes_cannot_be_excluded(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=(Path(tmp)/'input').resolve();shutil.copytree(INPUTS['henderson'],root)
   proof,family=data('henderson');cp=common.load(root/'checkpoint.json');pub=next(iter(cp['publications'].values()));report=common.load(root/'publications/14896/coverage.json');ex=report['justified_exclusions'][0];u=cp['units'][ex['evidence_unit']];receipt_path=root/u['receipt'];receipt=common.load(receipt_path);body=root/receipt['body_file'];original=body.read_bytes()
   for key in ['Notes','Footnotes']:
    landing=json.loads(original);d=next(x for x in landing['Docs'] if str(x['Id'])==str(ex['id']));self.assertEqual(d['DocType'],4);self.assertFalse(d.get('Content'));d[key]='RAW STRUCTURAL LEGAL NOTE NOT REPRESENTED BY ANY IR ROW';body.write_bytes(common.encoded(landing));h=common.file_hash(body);u['sha256']=h;receipt['sha256']=h;receipt_path.write_bytes(common.encoded(receipt));(root/'checkpoint.json').write_bytes(common.encoded(cp))
    attacked=copy.deepcopy(proof);attacked['evidence_sha256_before']=common.files(root);attacked['evidence_sha256_after']=copy.deepcopy(attacked['evidence_sha256_before'])
    with self.subTest(raw_field=key),self.assertRaisesRegex(ValueError,'separate Notes/Footnotes in structural'):
     municode_html.read_projection(root,attacked,family)
 def test_raw_body_hash_corruption_refused(self):
  for n in INPUTS:
   field='body_sha256' if n=='henderson' else 'raw_sha256'
   def wrong(rs):rs[0][field]='0'*64
   with self.subTest(n=n),self.changed_records(n,wrong),self.assertRaises(ValueError):projection(n)
 def test_proof_identity_and_code_drift_refused(self):
  for n in INPUTS:
   for key in ['selected_config','collector_sources_after']:
    proof,family=data(n);proof[key]={}
    with self.subTest(n=n,key=key),self.assertRaises(ValueError):MODS[n].read_projection(INPUTS[n],proof,family)
 def test_actual_input_map_mutation_refused(self):
  # Same complete real proof, no recomputed false verification claim.
  proof,family=data('charter');bad=copy.deepcopy(proof);bad['evidence_sha256_before']['records.jsonl']='0'*64;bad['evidence_sha256_after']=copy.deepcopy(bad['evidence_sha256_before'])
  with self.assertRaisesRegex(ValueError,'Input differs'):package.validate_input(INPUTS['charter'],bad,family)
 def test_lf_jsonl_preserves_unicode_legal_separators(self):
  value={'text':'first\u2028second\u0085third\u2029fourth'}
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'r.jsonl';p.write_text(json.dumps(value,ensure_ascii=False)+'\n',encoding='utf-8');self.assertEqual(reader_utils.lines(p),[value])
 def test_literal_image_and_html_structure_preserved(self):
  html='<h3 id="owner">Caption</h3><ol start="4"><li>Available [IMAGE] caption<table><tr><th colspan="2">Header</th></tr><tr><td>A</td><td>B</td></tr></table></li></ol><p id="note">Note</p>'
  row,*_=reader_utils.corpus_row('J','Book',[{'id':'n','heading':'ARTICLE I'}],'Sec. 2. Title',html,'https://example.test/x','2026-01-01')
  self.assertEqual(row['full_text'],html);self.assertEqual(row['section_number'],'2.')
  with self.assertRaises(ValueError):reader_utils.corpus_row('J','B',[],'Title','<img src="data:image/png,PIXELS">','https://example.test','2026-01-01')
 def test_repeated_hierarchy_retains_conflict_instead_of_guess(self):
  fields,number,name,evidence,conflicts=reader_utils.literal_components([{'id':'a','heading':'PART I GENERAL'},{'id':'b','heading':'PART II SPECIAL'}],'Sec. 2. Text')
  self.assertEqual(fields['part'],'');self.assertEqual(len(conflicts),1);self.assertEqual(number,'2.')
if __name__=='__main__':unittest.main()
