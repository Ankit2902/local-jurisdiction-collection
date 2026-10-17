"""Current-policy six-family payload/cell probes, always synthetic source bodies."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent));sys.path.insert(0,str(ROOT/'collectors/municode'))
import test_image_policy as four_families
from bs4 import BeautifulSoup
from image_policy import sanitize
from normalize import LegalHTML
from collectors.gridics.model import normalize as gridics_normalize
PIXELS='SU1BR0VfUElYRUxfQllURVNfTVVTVF9OT1RfQkVfTk9STUFMSVpFRA=='
class AllFamilyImageMetadata(unittest.TestCase):
 def rows(self,body):
  result={family:(r,key) for family,(r,key,idkey) in four_families.Tests().rows(body).items()}
  html,omissions=sanitize(body,'https://example.invalid/code/');p=LegalHTML();p.feed(html);result['municode']=({'html':html,'text':p.parsed(),'tables':p.tables,'image_omissions':omissions},'html')
  result['gridics']=(gridics_normalize(body,'https://codehub.gridics.com/us/zz/test'),'html');return result
 def test_inline_pixels_absent_from_all_normalized_metadata(self):
  body=('<p>Rule applies.</p><img src="data:image/png;base64,PIXELS"><p style="background-image:url(data:image/png;base64,PIXELS)">Background rule</p><object type="image/png" data="data:image/png;base64,PIXELS"></object><picture><source srcset="data:image/png;base64,PIXELS 1x"><img src="fallback.png"></picture><img src="ordinary.png" alt="data:image/png;base64,PIXELS">').replace('PIXELS',PIXELS)
  for family,(r,k) in self.rows(body).items():
   with self.subTest(family=family):self.assertNotIn(PIXELS,json.dumps(r));self.assertNotIn('data:image/',r[k].lower());self.assertGreaterEqual(r['text'].count('[IMAGE]'),4)
 def test_background_image_survives_nested_cell_serialization(self):
  body='<p>Rule applies.</p><table><tr><td background="outer.png">Outer<table><tr><td style="background-image:url(inner.png)">Inner</td></tr></table></td></tr></table>'
  for family,(r,k) in self.rows(body).items():
   with self.subTest(family=family):
    cells=BeautifulSoup(r[k],'html.parser').select('td');self.assertEqual(len(cells),2);self.assertIn('[IMAGE]',cells[0].get_text());self.assertIn('[IMAGE]',cells[1].get_text());self.assertNotIn('background=',r[k]);self.assertNotIn('url(',r[k])
    if family=='municode':self.assertIn('[IMAGE]',r['tables'][0][0][0]['text']);self.assertIn('[IMAGE]',r['tables'][1][0][0]['text'])
 def test_stylesheet_image_placeholder_not_silently_dropped(self):
  body='<p>Rule applies.</p><style>.map {background-image:url(map.png)}</style>'
  for family,(r,k) in self.rows(body).items():
   with self.subTest(family=family):self.assertIn('[IMAGE]',r['text']);self.assertNotIn('url(',r[k])
 def test_source_and_untyped_image_object_placeholder(self):
  body='<p>Rule applies.</p><source src="data:image/png;base64,'+PIXELS+'"><object data="map.png"></object>'
  for family,(r,k) in self.rows(body).items():
   with self.subTest(family=family):self.assertGreaterEqual(r['text'].count('[IMAGE]'),2);self.assertNotIn(PIXELS,json.dumps(r))
 def test_comment_never_becomes_operative_text(self):
  body='<p>This operative legal requirement applies to every property and applicant.</p><!-- INTERNAL_COMMENT_NOT_LEGAL_TEXT -->'
  for family,(r,k) in self.rows(body).items():
   with self.subTest(family=family):self.assertNotIn('INTERNAL_COMMENT_NOT_LEGAL_TEXT',r['text'])
if __name__=='__main__':unittest.main(verbosity=2)
