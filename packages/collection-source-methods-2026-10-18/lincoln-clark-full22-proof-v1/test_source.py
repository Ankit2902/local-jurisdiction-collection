import unittest,json,socket
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
from source_inventory import validate
from no_image import guard
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def setUp(self):self.raw=(P/'clark-county-code.html').read_bytes();self.expected=json.loads((P/'clark-uncodified-inventory.json').read_text())
 def test_actual_independent_full22_titles_dates(self):self.assertEqual(len(validate(self.raw,self.expected['source_url'],self.expected)),22)
 def test_omitted_source_row_refuses(self):
  s=BeautifulSoup(self.raw,'html.parser');s.select('main .table.bordered.bid > div')[1].decompose()
  with self.assertRaises(AssertionError):validate(str(s).encode(),self.expected['source_url'],self.expected)
 def test_wrong_source_and_foreign_base_code_refuse(self):
  with self.assertRaises(AssertionError):validate(self.raw,'https://www.clarkcountynv.gov/other',self.expected)
  with self.assertRaises(AssertionError):validate(self.raw.replace(b'/nv/clark_county/',b'/nv/other_county/'),self.expected['source_url'],self.expected)
 def test_adopted_date_change_refuses(self):
  changed=self.raw.replace(b'6/16/2026',b'6/16/2025',1)
  with self.assertRaises(AssertionError):validate(changed,self.expected['source_url'],self.expected)
 def test_image_controls_stop_before_decode(self):
  from PIL import Image
  from pypdf._page import PageObject
  calls=[]
  with guard(calls),patch.object(socket,'socket',side_effect=AssertionError('No network')):
   with self.assertRaises(AssertionError):Image.open('not-an-image-resource')
   with self.assertRaises(AssertionError):PageObject.create_blank_page(width=10,height=10).images
  self.assertEqual(len(calls),2)
if __name__=='__main__':unittest.main(verbosity=2)
