"""Bounded actual-index/fault/decoder-tripwire tests; no network/native parse."""
import copy,json,pathlib,sys,unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
import run as g
H=pathlib.Path(__file__).resolve().parent
class Method(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.config=json.loads((H/'config.json').read_text());cls.data=(H/'regulations/body.bin').read_bytes()
 def discover(self,data):
  with patch.object(g.collect,'fetch_raw',return_value=(data,{},'raw/fixture.bin')):items,identity=g.collect.discover(pathlib.Path('/not-written'),self.config)
  g.selected(items)
  return items,identity
 def test_actual_index_exact_pair_and_archive_exclusion(self):
  items,identity=self.discover(self.data);g.selected(items);self.assertEqual(len(identity['excluded_components']),1);self.assertIn('SupersededZoningOrdinance_2001',identity['excluded_components'][0]['url']);self.assertFalse(identity['excluded_components'][0]['required'])
 def test_missing_native_source_link_refused(self):
  from bs4 import BeautifulSoup
  s=BeautifulSoup(self.data,'html.parser');next(a for a in s.select(self.config['inventory_selector'])if'Subdivision'in a.get_text()).decompose()
  with self.assertRaises(ValueError):self.discover(str(s).encode())
 def test_duplicate_same_document_not_two_publications(self):
  from bs4 import BeautifulSoup
  s=BeautifulSoup(self.data,'html.parser');a=[a for a in s.select(self.config['inventory_selector'])if a.get_text(' ',strip=True).startswith(('Subdivision','Zoning Ordinance'))];a[1]['href']=a[0]['href']
  with self.assertRaises(ValueError):self.discover(str(s).encode())
 def test_wrong_host_source_excluded_and_pair_refuses(self):
  from bs4 import BeautifulSoup
  s=BeautifulSoup(self.data,'html.parser');a=next(a for a in s.select(self.config['inventory_selector'])if'Subdivision'in a.get_text());a['href']='https://example.invalid/other.pdf'
  with self.assertRaises(ValueError):self.discover(str(s).encode())
 def test_retained_official_refusals_block_before_network(self):
  import urllib.request
  with patch.object(urllib.request,'urlopen',side_effect=AssertionError('No request'))as net:
   for url in ['https://www.slc.gov/slc-infobase/','https://www.stamfordct.gov/government/boards-commissions/board-of-representatives']:
    with self.assertRaisesRegex(RuntimeError,'Retained official host refusal'):g.preflight(url)
   net.assert_not_called()
 def test_stopped_publisher_family_not_alternate_transport(self):
  for u in ['https://library.municode.com/ct/stamford/codes/code_of_ordinances','https://codelibrary.amlegal.com/codes/manchester/latest/overview']:
   with self.assertRaisesRegex(RuntimeError,'publisher-family stop'):g.preflight(u)
 def test_image_contexts_refuse_before_any_decoder(self):
  from pdfminer.pdftypes import PDFStream
  from pdfminer.psparser import LIT
  from pypdf.generic import EncodedStreamObject,DecodedStreamObject,NameObject,NumberObject
  attrs=[{'Subtype':LIT('Image')},{'W':1,'H':1},{'Width':1,'Height':1},{'/W':1,'/H':1},{'/Width':1,'/Height':1}]
  for cls in [PDFStream,EncodedStreamObject,DecodedStreamObject]:
   for d in attrs:
    x=PDFStream(d,b'NO_IMAGE_DATA')if cls is PDFStream else cls()
    if cls is not PDFStream:x.update({NameObject('/'+k.lstrip('/')):NameObject('/Image')if k.endswith('Subtype')else NumberObject(v)for k,v in d.items()})
    with patch.object(cls,'get_data',side_effect=AssertionError('Original decoder must not run'))as decoder:
     with self.assertRaisesRegex(AssertionError,'forbidden_image_or_offline_network_operation'),g.guards([]):x.get_data()
     decoder.assert_not_called()
 def test_nonimage_font_text_context_remains_allowed(self):
  from pdfminer.pdftypes import PDFStream
  with patch.object(PDFStream,'get_data',return_value=b'TEXT_FONT_SENTINEL')as decoder,g.guards([]):
   self.assertEqual(PDFStream({'Type':'Font'},b'NO_IMAGE').get_data(),b'TEXT_FONT_SENTINEL');decoder.assert_called_once()
 def test_actual_native_edition_pins(self):
  rows=json.loads((H/'full-two-pdf-v1/opening-native-metadata.json').read_text())
  for r in rows:
   b=(H/'full-two-pdf-v1/capture'/r['raw_ref']).read_bytes();item={'url':r['url'],'heading':r['heading']};pin=g.native_source(b,item);self.assertEqual(pin['physical_pages'],r['physical_pages'])
   with self.assertRaisesRegex(ValueError,'edition/hash/identity'):g.native_source(b+b'changed',item)
 def test_crosswired_wrong_edition_refuses_before_parser(self):
  rows=json.loads((H/'full-two-pdf-v1/opening-native-metadata.json').read_text());a,b=rows;data=(H/'full-two-pdf-v1/capture'/a['raw_ref']).read_bytes()
  with patch.object(g.collect,'parse_item',side_effect=AssertionError('No parse'))as parser:
   with self.assertRaisesRegex(ValueError,'edition/hash/identity'):g.native_source(data,{'url':b['url'],'heading':b['heading']})
   parser.assert_not_called()
if __name__=='__main__':unittest.main(verbosity=2)
