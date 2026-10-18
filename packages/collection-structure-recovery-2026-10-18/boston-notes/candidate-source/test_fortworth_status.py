"""Exact raw-fragment status qualification and fail-closed controls; offline tripwires."""
import copy,hashlib,importlib.util,json,pathlib,platform,socket,sys,unittest
from unittest.mock import patch
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[3]
spec=importlib.util.spec_from_file_location('fortworth_candidate_model',OUT/'model.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
study=json.loads((OUT/'fixtures/fortworth-status-v1.json').read_text());witness={x['document_id']:x for x in study['unqualified_units']};identity=study['identity'];cases=[]
def record(item,html):return m.html_record({'doc_id':item['document_id'],'id':item['internal_id'],'title':item['heading'],'html':html},item,identity,study['source_receipt']['requested_url'],study['source_native_sha256'])
def mutate_fragment(did,transform):
 original=witness[did]['source_fragment_html'];changed=transform(original);assert changed!=original,'Mutation did not alter original raw source';return changed
class Qualification(unittest.TestCase):
 def test_01_actual_repealed_body(self):
  w=witness['0-0-0-267'];r=record(w['toc'],w['source_fragment_html']);self.assertEqual(r['content_classification'],'source-explicit-status');e=r['source_status_evidence'];self.assertEqual((e['status'],e['source_field'],e['literal']),('repealed','own-body','[Repealed]'));self.assertEqual(r['body_block_ids'],w['owned_block_ids']);self.assertEqual(e['source_fragment_sha256'],w['source_fragment_sha256']);self.assertEqual(r['text'],w['old_text'])
 def test_02_actual_reserved_native_heading_not_abbreviated_TOC(self):
  w=witness['0-0-0-3695'];r=record(w['toc'],w['source_fragment_html']);self.assertEqual(r['content_classification'],'source-explicit-status');self.assertEqual(r['source_status_evidence']['literal'],'§§ 3-99—3-100 RESERVED.');self.assertEqual(r['heading'],'§§ 3-99');self.assertEqual(r['text'],w['old_text']);self.assertEqual(r['source_status_evidence']['status'],'reserved')
 def test_03_other_seven_actual_gaps_remain(self):
  for did,w in witness.items():
   if did in ['0-0-0-267','0-0-0-3695']:continue
   with self.subTest(did=did):
    r=record(w['toc'],w['source_fragment_html']);self.assertEqual(r['content_classification'],'unqualified-heading-only');self.assertNotIn('source_status_evidence',r);self.assertEqual(r['text'],w['old_text']);self.assertEqual(r['body_block_ids'],w['owned_block_ids'])
 def test_04_status_must_be_exact_standalone_body(self):
  w=witness['0-0-0-267']
  for status in ['Repealed','[Amended]','[Repealed?]','[Repealed] applies']:
   with self.subTest(status=status):
    r=record(w['toc'],mutate_fragment(w['document_id'],lambda s:s.replace('[Repealed]',status)));self.assertNotIn('source_status_evidence',r)
 def test_05_no_disposition_from_other_element_type(self):
  w=witness['0-0-0-3695'];r=record(w['toc'],mutate_fragment(w['document_id'],lambda s:s.replace('class="Section ', 'class="Subchapter ')));self.assertEqual(r['content_classification'],'unqualified-heading-only')
 def test_06_no_Reserved_parking_or_uncited_heading(self):
  w=witness['0-0-0-3695']
  for title in ['RESERVED.','§§ 3-99—3-100 RESERVED PARKING.','§§ 3-99—3-100 RESERVED. applies']:
   with self.subTest(title=title):
    r=record(w['toc'],mutate_fragment(w['document_id'],lambda s:s.replace('&#167;&#167; 3-99&#8212;3-100  RESERVED.',title)));self.assertEqual(r['content_classification'],'unqualified-heading-only')
 def test_07_native_reserved_heading_with_operative_body_is_not_status_only(self):
  w=witness['0-0-0-3695'];r=record(w['toc'],w['source_fragment_html']+'<div id="rid-added"><p>Rule applies to all properties.</p></div>');self.assertEqual(r['content_classification'],'operative-or-front-matter-body');self.assertNotIn('source_status_evidence',r)
 def test_08_wrong_requested_source_id_fails(self):
  w=witness['0-0-0-267']
  with self.assertRaises(AssertionError):record(w['toc'],mutate_fragment(w['document_id'],lambda s:s.replace('rid-0-0-0-267','rid-wrong-id')))
 def test_09_images_stay_placeholder_not_short_status(self):
  w=witness['0-0-0-267'];r=record(w['toc'],mutate_fragment(w['document_id'],lambda s:s.replace('[Repealed]','<img src="https://example.invalid/opaque.png" alt="Available label">')));self.assertEqual(r['content_classification'],'intentional-image-placeholder');self.assertNotIn('source_status_evidence',r);self.assertIn('[IMAGE]',r['text']);self.assertNotIn('<img',r['html']);self.assertEqual(r['body_block_ids'],w['owned_block_ids']);self.assertTrue(all(a.get('kind')=='image' and a.get('disposition')=='image-placeholder' for a in r['assets']))
if __name__=='__main__':
 class Result(unittest.TextTestResult):
  def addSuccess(self,test):super().addSuccess(test);cases.append({'name':test.id(),'passed':True})
 with patch.object(socket,'socket',side_effect=AssertionError('Network forbidden')) as network,patch.object(Image,'open',side_effect=AssertionError('Image decode forbidden')) as decoder:
  result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromTestCase(Qualification))
 report={'passed':result.wasSuccessful(),'tests_run':result.testsRun,'count':result.testsRun,'test_cases':cases,'failures':[(str(t),msg) for t,msg in result.failures+result.errors],'socket_calls':network.call_count,'Image_open_calls':decoder.call_count,'runtime':{'python':sys.version,'platform':platform.platform()},'candidate_model_sha256':hashlib.sha256((OUT/'model.py').read_bytes()).hexdigest(),'source_inspection_sha256':hashlib.sha256((OUT/'fixtures/fortworth-status-v1.json').read_bytes()).hexdigest(),'test_script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'scope':'Nine actual own raw source fragments plus scoped mutation controls; not a full current-source Fort Worth replay.'};print(json.dumps(report,indent=2,ensure_ascii=False));sys.exit(0 if result.wasSuccessful() else 1)
