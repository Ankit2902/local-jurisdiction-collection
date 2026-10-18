import sys
sys.dont_write_bytecode=True
import pathlib,json,copy,unittest
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H/'captured'))
from collectors.encodeplus import retained_native as n
from pdfminer.pdftypes import PDFStream
from unittest.mock import patch
class SourceMethods(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  id='82-cfe47a936088';c.cfg=json.loads((H/'configs'/('native-'+id+'.json')).read_text());c.body=(H/'native-discovery'/(id+'.bin')).read_bytes();c.receipt=json.loads((H/'native-discovery'/(id+'.bin.receipt.json')).read_text())
 def test_valid_literal_source(self):self.assertEqual(n.validate_source(self.body,self.receipt,self.cfg)['url'],self.cfg['url'])
 def test_source_bytes_change(self):
  with self.assertRaises(AssertionError):n.validate_source(self.body+b'changed',self.receipt,self.cfg)
 def test_other_alias_refused(self):
  r=copy.deepcopy(self.receipt);r['url']=r['final_url']=r['url'].replace('online.encodeplus.com/regs/overlandpark-ks','codes.opkansas.org/municipal-code')
  with self.assertRaises(AssertionError):n.validate_source(self.body,r,self.cfg)
 def test_bad_mime_refused(self):
  r=copy.deepcopy(self.receipt);r['headers']['Content-Type']='text/html'
  with self.assertRaises(AssertionError):n.validate_source(self.body,r,self.cfg)
 def test_refusal_receipt(self):
  for key,value in [('challenge',True),('http_status',403),('sha256','0'*64),('bytes',0)]:
   r=copy.deepcopy(self.receipt);r[key]=value
   with self.subTest(key=key),self.assertRaises(AssertionError):n.validate_source(self.body,r,self.cfg)
 def test_missing_config_pin(self):
  cfg=copy.deepcopy(self.cfg);cfg['expected_pages']=0
  with self.assertRaises(AssertionError):n.validate_source(self.body,self.receipt,cfg)
 def test_image_source_before_decoder(self):
  original=PDFStream.get_data;calls=[]
  def decoder(*a,**k):calls.append(True);return b'ordinary font'
  for attrs in [{'W':1,'H':1},{'Width':1,'Height':1},{'/W':1,'/H':1},{'Subtype':'Image'}]:
   with self.subTest(attrs=attrs),patch.object(PDFStream,'get_data',decoder):
    with self.assertRaises(AssertionError):
     with n.guards():PDFStream(attrs,b'untouched').get_data()
  self.assertEqual(calls,[])
 def test_nonimage_font_stream_allowed(self):
  with patch.object(PDFStream,'get_data',return_value=b'font')as decoder:
   with n.guards():self.assertEqual(PDFStream({'Length1':4},b'font').get_data(),b'font')
   self.assertEqual(decoder.call_count,1)
if __name__=='__main__':unittest.main()
