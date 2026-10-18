import copy,csv,gzip,io,json,pathlib,sys,unittest
BASE=pathlib.Path(__file__).resolve().parent
from collectors.encodeplus import infrastructure_contents as m
from collectors.encodeplus.native_document import outputs
FIX=BASE/'fixtures/infrastructure-four-region'
class CanonicalSource(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ir=json.loads(gzip.decompress((FIX/'selected-ir.json.gz').read_bytes()))
 def source(self,n=2):
  ir=copy.deepcopy(next(d for d in self.ir if d['physical_page']==n));r=ir['original_record'];item={'id':r['document_id'],'url':r['source_url'].split('#page=')[0],'raw_ref':r['raw_ref'],'expected_sha256':m.SOURCE_SHA256};return ir,r,item
 def project(self,n=2):
  ir,r,item=self.source(n);old=copy.deepcopy(r);self.assertTrue(m.attach_retained_ir(r,ir,item,m.SOURCE_SHA256));return r,old
 def failure(self,mutate):
  ir,r,item=self.source();mutate(ir,r,item);before=copy.deepcopy(r)
  with self.assertRaises(ValueError):m.attach_retained_ir(r,ir,item,m.SOURCE_SHA256)
  self.assertEqual(r,before,'Selected source refusal must be atomic')
 def test_actual_four_canonical_non_grid_regions(self):
  out=[self.project(n)[0]for n in [2,3,6,46]];s=m.summary(out)
  self.assertTrue(s['finite_source_structure_complete']);self.assertEqual(s['contents_entries'],96);self.assertEqual(s['source_words'],603)
  self.assertEqual(s['source_printed_units'],110);self.assertEqual(s['original_failed_detector_cells_retained'],44);self.assertEqual(s['literal_leader_folio_spacing_discrepancies'],3)
  self.assertFalse(s['whole_book_semantic_or_table_completeness_qualified']);self.assertFalse(s['full_line_spacing_complete'])
  self.assertTrue(all(r['tables']==[]and r['canonical_structure_selection']['canonical_table_ids']==[]for r in out))
 def test_original_five_fields_restore_exact(self):
  for n in [2,3,6,46]:
   row,old=self.project(n);restored=copy.deepcopy(row)
   self.assertEqual(row['superseded_detector_diagnostics']['original_record_fields'],{k:old[k]for k in m.FIELDS})
   for k,v in row['superseded_detector_diagnostics']['original_record_fields'].items():restored[k]=v
   for k in ['canonical_structure_selection','superseded_detector_diagnostics','source_infrastructure_structures']:restored.pop(k)
   self.assertEqual(restored,old)
 def test_all_old_467_cells_and44_false_unchanged_diagnostics(self):
  rows=[self.project(n)[0]for n in [2,3,6,46]];tables=[t for r in rows for t in r['superseded_detector_diagnostics']['original_record_fields']['tables']]
  self.assertEqual(sum(len(t['cells'])for t in tables),467);self.assertEqual(sum(not c['independent_character_agreement']for t in tables for c in t['cells']),44)
 def test_three_spacing_false_flags_remain_authoritative_review(self):
  row,_=self.project(6);q=row['pdf_qualification'];self.assertFalse(q['source_infrastructure_full_line_spacing_complete']);self.assertTrue(q['source_infrastructure_component_spacing_complete'])
  self.assertIn('source_contents_literal_leader_folio_spacing_discrepancy',q['review_conditions']);self.assertTrue(row['semantic_review_required'])
 def test_csv_and_json_use_canonical_not_old_detector_text(self):
  row,old=self.project(3);self.assertNotEqual(row['text'],old['text']);payload=outputs([row]);j=json.loads(payload['records.jsonl']);c=list(csv.DictReader(io.StringIO(payload['records.csv'].decode())))[0]
  self.assertEqual(j['text'],row['text']);self.assertEqual(c['text'],row['text']);self.assertIn('5. HORIZONTAL DIRECTIONAL DRILLING',c['text'])
 def test_cover_dates_are_metadata_not_legal_schedule(self):
  row,_=self.project(46);e=row['source_infrastructure_structures'][0]
  self.assertEqual([x['date']for x in e['publication_dates']],['2019-03-26','2020-01-21','2024-03-01']);self.assertEqual(row['tables'],[])
  self.assertIn('Originally Published March 26, 2019',row['text']);self.assertFalse(e['whole_book_semantic_or_table_completeness_qualified'])
 def test_known_printed_targets_are_not_legal_section_identity(self):
  row,_=self.project(6)
  refs=[b['source_printed_reference']for b in row['ordered_blocks']if 'source_printed_reference'in b]
  self.assertEqual(refs[0]['printed_folio'],'A-6');self.assertEqual(refs[0]['target']['physical_page'],52)
  self.assertTrue(all(x['reference_kind']=='printed_folio'and not x['destination_legal_section_identity_verified']for x in refs))
 def test_configured_namespace_rebased_without_foreign_ownership(self):
  ir,row,item=self.source();oldid=item['id'];newid='native-infrastructure-custom';row=json.loads(json.dumps(row).replace(oldid,newid));item=dict(item,id=newid,raw_ref='raw/custom.pdf');row['raw_ref']=item['raw_ref']
  self.assertTrue(m.attach_retained_ir(row,ir,item,m.SOURCE_SHA256));self.assertEqual(row['document_id'],newid)
  self.assertTrue(all(w.startswith(newid+'::page:2::word:')for b in row['ordered_blocks']for w in b['word_ids']))
  self.assertNotIn(oldid,json.dumps(row))
 def test_wrong_source_is_noop_before_native_access(self):
  ir,row,item=self.source();old=copy.deepcopy(row);self.assertFalse(m.attach_record(row,object(),object(),item,'0'*64));self.assertEqual(row,old)
 def test_unobserved_url_is_noop_before_native_access(self):
  ir,row,item=self.source();old=copy.deepcopy(row);item['url']='https://example.gov/guessed.pdf';self.assertFalse(m.attach_record(row,object(),object(),item,m.SOURCE_SHA256));self.assertEqual(row,old)
 def test_unselected_page_is_noop(self):
  ir,row,item=self.source();row['physical_page']=5;old=copy.deepcopy(row);self.assertFalse(m.attach_record(row,object(),object(),item,m.SOURCE_SHA256));self.assertEqual(row,old)
 def test_source_record_hash_mismatch_atomic(self):self.failure(lambda ir,r,item:r.update(raw_sha256='0'*64))
 def test_configured_edition_hash_mismatch_atomic(self):self.failure(lambda ir,r,item:item.update(expected_sha256='0'*64))
 def test_raw_reference_mismatch_atomic(self):self.failure(lambda ir,r,item:item.update(raw_ref='raw/other.pdf'))
 def test_record_owner_mismatch_atomic(self):self.failure(lambda ir,r,item:r.update(document_id='wrong-document'))
 def test_source_url_mismatch_atomic(self):self.failure(lambda ir,r,item:r.update(source_url=item['url']+'#page=3'))
 def test_prior_canonical_selection_not_overwritten(self):self.failure(lambda ir,r,item:r.update(canonical_structure_selection={'profile':'other'}))
 def test_prior_diagnostics_not_overwritten(self):self.failure(lambda ir,r,item:r.update(superseded_detector_diagnostics={}))
 def test_changed_false_cell_not_silently_qualified(self):
  def mutate(ir,r,item):next(c for t in r['tables']for c in t['cells']if not c['independent_character_agreement'])['independent_character_agreement']=True
  self.failure(mutate)
 def test_changed_word_geometry_atomic(self):self.failure(lambda ir,r,item:ir['words'][5].update(x0=ir['words'][5]['x0']+.001))
 def test_changed_actual_query_rectangle_atomic(self):self.failure(lambda ir,r,item:ir['lines'][1]['native_query_bbox_pdf'].__setitem__(0,ir['lines'][1]['native_query_bbox_pdf'][0]+.001))
 def test_changed_native_spacing_atomic(self):self.failure(lambda ir,r,item:ir['lines'][1].update(native_query_result=ir['lines'][1]['native_query_result'].replace('GENERAL REQUIREMENTS','GENERALREQUIREMENTS')))
 def test_decoder_uncertainty_cannot_be_waived(self):self.failure(lambda ir,r,item:r['pdf_qualification']['unmapped_or_private_use_codepoints'].append(0xf0b7))
 def test_images_not_added_or_removed_by_selected_projection(self):
  for n in [2,3,6,46]:
   row,old=self.project(n);self.assertEqual(row['image_placeholder_count'],old['image_placeholder_count']);self.assertEqual(row['assets'],old['assets']);self.assertEqual(row['links'],old['links'])
if __name__=='__main__':unittest.main(verbosity=2)
