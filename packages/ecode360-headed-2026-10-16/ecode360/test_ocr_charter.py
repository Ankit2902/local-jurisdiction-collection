import tempfile,unittest
from pathlib import Path
import ecode360 as e
from ocr_charter_review import process
ROOT=Path(__file__).parent
BASE=ROOT/'standalone-live/official-alternatives/santa-clara'
URL='https://santaclara.legistar.com/View.ashx?GUID=9FDBDA24-1C91-4A58-859B-2516966A0809&ID=15562338&M=F'
class CharterOCRTests(unittest.TestCase):
 def run_sample(self,out,ocr=None,receipt=None):return process(BASE/'santa-clara-current-charter.pdf',ocr or BASE/'vision-page1/ocr.json',URL,out,receipt or BASE/'santa-clara-current-charter.pdf.receipt.json')
 def test_actual_first_page_five_complete_bodies_not_boundary_heading(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'exports';r=self.run_sample(out);rows=e.load(out/'fulltext.json')['provisions'];self.assertEqual([x['section_number'] for x in rows],['100','200','300','301','302']);self.assertEqual(r['unresolved_boundary_nodes'],1);self.assertFalse(r['municipal_code_gap_closed']);self.assertFalse(r['whole_charter_parsed'])
   self.assertEqual(rows[0]['full_text'],'The municipal corporation now existing and known as the "City of Santa Clara" shall remain and continue to be a municipal body politic and corporate, as at present, in name, in fact, and in law.')
 def test_bad_acquisition_hash_refused(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);r=e.load(BASE/'santa-clara-current-charter.pdf.receipt.json');r['sha256']='bad';e.dump(p/'receipt.json',r)
   with self.assertRaises(e.ValidationError):self.run_sample(p/'out',receipt=p/'receipt.json')
 def test_low_confidence_body_not_emitted(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);o=e.load(BASE/'vision-page1/ocr.json');o['rows'][5]['confidence']=0.5;e.dump(p/'ocr.json',o);self.run_sample(p/'out',ocr=p/'ocr.json');rows=e.load(p/'out/fulltext.json')['provisions'];self.assertNotIn('100',[x['section_number'] for x in rows])
if __name__=='__main__':unittest.main()
