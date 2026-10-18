"""Historical native method guards; uses retained bytes/IR, never parses PDF pages."""
import copy,hashlib,json,pathlib,sys,tempfile,unittest,shutil,os
from unittest.mock import patch
H=pathlib.Path(sys.argv.pop(1)).resolve()if len(sys.argv)>1 and not sys.argv[1].startswith('-')else pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H/'candidate'))
from collectors.encodeplus import retained_native as m
class Method(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.cfg=json.loads((H/'candidate/collectors/encodeplus/configs/native-82-8fbdce15716d.json').read_text());c.data=(H/'actual-retained-full172/raw/source.pdf').read_bytes();c.receipt=json.loads((H/'actual-retained-full172/raw/source.pdf.receipt.json').read_text());c.out=H/'actual-retained-full172'
 def test_exact_observed_source_and_historical_config(self):
  x=m.validate_source(self.data,self.receipt,self.cfg);self.assertFalse(x['catalog_alias_acquisition_verified']);self.assertEqual(x['url'],self.cfg['url']);self.assertIn('codes.opkansas.org',x['url']);self.assertEqual(self.cfg['expected_pages'],172)
 def test_alias_is_not_silently_a_proven_download(self):
  r=copy.deepcopy(self.receipt);r['url']=r['final_url']=self.cfg['qualification']['catalog_source_url']
  with self.assertRaisesRegex(AssertionError,'receipt URL'):m.validate_source(self.data,r,self.cfg)
 def test_wrong_bytes_edition_fail_before_native(self):
  with patch.object(m.native,'page_records',side_effect=AssertionError('Must not parse'))as parser:
   for data in [b'',self.data[:200],self.data+b'changed edition']:
    with self.assertRaisesRegex(AssertionError,'source edition/hash'):m.validate_source(data,self.receipt,self.cfg)
   parser.assert_not_called()
 def test_refusal_mime_hash_filename_not_waived(self):
  changes=[('http_status',403),('challenge',True),('error','refused'),('sha256','0'*64),('bytes',len(self.data)-1)]
  for key,value in changes:
   r=copy.deepcopy(self.receipt);r[key]=value
   with self.subTest(key=key),self.assertRaises(AssertionError):m.validate_source(self.data,r,self.cfg)
  for header,value in [('Content-Type','text/html'),('content-disposition','inline; filename=current2026.pdf')]:
   r=copy.deepcopy(self.receipt);r['headers'][header]=value
   with self.subTest(header=header),self.assertRaises(AssertionError):m.validate_source(self.data,r,self.cfg)
 def test_fresh_out_never_overwrites_existing_evidence(self):
  with tempfile.TemporaryDirectory()as td,patch.object(m.native,'page_records',side_effect=AssertionError('Must not parse'))as parser:
   out=pathlib.Path(td)/'exists';out.mkdir();(out/'evidence').write_text('unchanged')
   with self.assertRaisesRegex(AssertionError,'Fresh output'):m.extract(self.cfg,H/'actual-retained-full172/raw/source.pdf',H/'actual-retained-full172/raw/source.pdf.receipt.json',out)
   self.assertEqual((out/'evidence').read_text(),'unchanged');parser.assert_not_called()
 def test_pixel_and_network_calls_refused_without_exposure(self):
  from PIL import Image
  import urllib.request
  from pdfminer.pdftypes import PDFStream
  from pdfminer.psparser import LIT
  for action in [lambda:Image.open('no-image'),lambda:urllib.request.urlopen('https://example.invalid'),lambda:PDFStream({'Subtype':LIT('Image')},b'NO_PIXEL_DECODE').get_data()]:
   with self.assertRaises(AssertionError),m.guards():action()
 def test_all172_captured_IR_required_and_false_limits_preserved(self):
  s=json.loads((self.out/'checkpoint.json').read_text());rows=[json.loads(l)for l in(self.out/'records.jsonl').read_text().split('\n')if l];headers=m.validate_source(self.data,self.receipt,self.cfg);r=m.summarize(rows,s['details'],self.cfg,headers)
  self.assertEqual(len(rows),172);self.assertEqual(r['physical_page_sequence'],list(range(1,173)));self.assertEqual(len(r['undecoded_CID_literal_pages']),102);self.assertFalse(r['publication_text_complete']);self.assertFalse(r['current_adopted_edition_qualified']);self.assertFalse(r['closing_acquisition_performed']);self.assertIsNone(r['start_end_consistent']);self.assertEqual(r['image_placeholders'],46)
  for bad in [rows[:-1],[rows[1],rows[0]]+rows[2:]]:
   with self.assertRaises(AssertionError):m.summarize(bad,s['details'],self.cfg,headers)
 def test_historical_cover_witness_cannot_be_guessed(self):
  s=json.loads((self.out/'checkpoint.json').read_text());rows=[json.loads(l)for l in(self.out/'records.jsonl').read_text().split('\n')if l];rows[6]['text']=rows[6]['text'].replace('POC-3460','POC-3529')
  with self.assertRaisesRegex(AssertionError,'identity witness'):m.summarize(rows,s['details'],self.cfg,{})
 def test_readonly_replay_never_calls_native_parser(self):
  with patch.object(m.native,'page_records',side_effect=AssertionError('No second native parse'))as parser:
   report=m.verify(self.out);self.assertTrue(report['artifact_replay_verified']);self.assertFalse(report['native_parser_reexecuted']);parser.assert_not_called()
 def test_corrupt_artifact_and_external_source_symlink_refuse(self):
  for mode in ['record','symlink']:
   with tempfile.TemporaryDirectory()as td,patch.object(m.native,'page_records',side_effect=AssertionError('No parse')):
    out=pathlib.Path(td)/'proof';shutil.copytree(self.out,out)
    if mode=='record':(out/'records.jsonl').write_bytes((out/'records.jsonl').read_bytes()+b'changed')
    else:
     (out/'raw/source.pdf').unlink();(out/'raw/source.pdf').symlink_to(self.out/'raw/source.pdf')
    with self.subTest(mode=mode),self.assertRaises(ValueError):m.verify(out)
 def test_hardlinked_same_source_is_readonly_not_rewritten(self):
  with tempfile.TemporaryDirectory()as td,patch.object(m.native,'page_records',side_effect=AssertionError('No parse')):
   out=pathlib.Path(td)/'proof';shutil.copytree(self.out,out);target=out/'raw/source.pdf';target.unlink();os.link(self.out/'raw/source.pdf',target);before=hashlib.sha256(target.read_bytes()).hexdigest();report=m.verify(out);self.assertTrue(report['artifact_replay_verified']);self.assertEqual(before,hashlib.sha256(target.read_bytes()).hexdigest());self.assertEqual(before,hashlib.sha256((self.out/'raw/source.pdf').read_bytes()).hexdigest())
if __name__=='__main__':unittest.main(verbosity=2)
