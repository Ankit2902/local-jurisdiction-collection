"""Source-bound semantic authority and output corruption negatives, no guessing."""
from pathlib import Path
from unittest.mock import patch,PropertyMock
import copy,io,json,unittest
import pypdfium2 as p
from pypdf import PdfReader
from pypdf.generic import EncodedStreamObject
from pypdf._page import PageObject
from pdfminer.pdftypes import PDFStream
import study as m
from verify import verify_result
class Metadata(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.actual=m.read(m.HERE/'STUDY.json');cls.fresh=m.study();cls.source=(m.HERE/'source/legacy-upoc.pdf').read_bytes();cls.prior=m.derive(cls.source);cls.reader=PdfReader(io.BytesIO(cls.source),strict=True);cls.resources,_,cls.programs,cls.census,_=m.metadata(cls.reader)
 @classmethod
 def tearDownClass(cls):
  for f in cls.programs.values():f.close()
 def test_actual_source_metadata_and_finite_probes_replay(self):
  verify_result(self.actual,self.fresh);self.assertEqual(len(self.actual['metadata_census_scope']['xref_font_objects']),16);self.assertFalse(self.actual['metadata_census_scope']['metadata_errors'])
  for n in self.actual['finite_native_probes']:
   for g in n['probes']:self.assertTrue(g['native_output_is_not_Unicode_witness'])
 def test_different_face_missing_or_nonunique_cmap_cannot_override_prior(self):
  for case in ['wrongface','missingcmap','aliasambiguity']:
   c=copy.deepcopy(self.census);w=next(v for v in c if v['font_object']==623)
   if case=='wrongface':w['face']='ArialDifferentFace'
   elif case=='missingcmap':w['explicit_semantic_cmap_entries']=[e for e in w['explicit_semantic_cmap_entries'] if e['gid']!=56]
   else:
    e=copy.deepcopy(next(e for e in w['explicit_semantic_cmap_entries'] if e['gid']==56));e['unicode']=86;w['explicit_semantic_cmap_entries'].append(e)
   with self.subTest(case=case):
    with self.assertRaises(AssertionError):m.search(self.resources,self.programs,c,self.prior)
 def test_raw_glyph_identity_required_not_font_name_or_metrics_only(self):
  target=self.programs[620];original=m.glyph_bytes
  def changed(font,gid):
   b=original(font,gid)
   return b+b'CORRUPT' if font is target and gid==56 else b
  with patch.object(m,'glyph_bytes',changed):
   with self.assertRaises(AssertionError):m.search(self.resources,self.programs,self.census,self.prior)
 def test_guessed_Unicode_deleted_unknown_or_changed_finite_native_data_refused(self):
  cases=[]
  x=copy.deepcopy(self.actual);x['unresolved_CID_inventory'][0]['Unicode']='V';x['unresolved_CID_inventory'][0]['qualified']=True;cases.append(x)
  x=copy.deepcopy(self.actual);x['unresolved_CID_inventory'].pop();cases.append(x)
  x=copy.deepcopy(self.actual);x['unresolved_CID_inventory'][0]['occurrences']-=1;cases.append(x)
  x=copy.deepcopy(self.actual);x['finite_native_probes'][0]['probes'][0]['native_output_is_not_Unicode_witness']=False;cases.append(x)
  x=copy.deepcopy(self.actual);x['no_current_edition_or_installed_font_substitution']=False;cases.append(x)
  for i,x in enumerate(cases):
   with self.subTest(fault=i):
    with self.assertRaises(AssertionError):verify_result(x,self.fresh)
 def test_wrong_original_edition_and_prior_mapping_tamper_refused(self):
  with self.assertRaises(ValueError):m.derive(self.source+b'\n')
  wrong=copy.deepcopy(self.prior);wrong['pairs'][0]['accepted'][0]['unicode']='X'
  with self.assertRaises(ValueError):m.decoder_from_original(self.source,wrong)
if __name__=='__main__':unittest.main()
