"""Independent final-policy regressions over real parser entry points; synthetic bodies."""
import sys,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from test_cross_family_edges import al,off,ec,ep,ecode_page,BASE
from bs4 import BeautifulSoup
PIXEL_SENTINEL='UElYRUxTX0FSRV9OT1RfRk9SX1JFT1VU'
IMAGES=('''<p>Before image text.</p><img id="i1" src="ordinary.png"><picture><source srcset="small.png 1x, large.png 2x"><img src="fallback.png"></picture><svg id="vector"><image href="map.png"/><use xlink:href="symbol.svg#shape"/></svg><p style="background-image:url(css.png)">CSS label</p><img src="data:image/png;base64,PIXELS"><video poster="poster.png"></video><style>.legal-map{background-image:url(sheet.png)}</style><object data="data:image/png;base64,PIXELS" type="image/png"></object><picture><source srcset="data:image/png;base64,PIXELS 1x"><img src="fallback.png"></picture><p style="background-image:url(data:image/png;base64,PIXELS)">Inline CSS label</p><table><tr><td>Outer cell<img src="cell.png"><table><tr><td>Nested cell<img src="nested.png"></td></tr></table></td></tr></table><p>After image text.</p>''').replace('PIXELS',PIXEL_SENTINEL)
IMAGE_ONLY='<img src="ordinary.png"><svg><image href="map.png"/></svg>'
DOC='<p>The adopted standard is incorporated by reference <a href="https://example.invalid/document/123">Required Standard</a></p>'
class Tests(unittest.TestCase):
 def rows(self,body):
  item={'document_id':'A','internal_id':1,'heading':'§ 1 Map provision','path':['§ 1 Map provision'],'parent_id':None,'has_children':False};ar=al.html_record({'doc_id':'A','id':1,'html':'<h2 id="rid-A">§ 1 Map provision</h2>'+body},item,{},BASE,'fixture')
  raw=ecode_page(body);er=ec.parse_ecode(raw,'https://ecode360.com/101',ec.identity(raw,'https://ecode360.com/101','ecode360'))['records'][0]
  cfg={'base':BASE,'identity':'Fixture Code','jurisdiction':'Fixture NV','scope':'Synthetic parser test'};pr=ep.parse_document('<div id="thePage" secid="1"><section data-secid="1"><h2>§ 1 Map provision</h2>'+body+'</section></div>','1',cfg,{'1':{'heading':'§ 1 Map provision','has_children':False}})[0]
  cfg={'mode':'html_single','id':'fixture','jurisdiction':'Fixture','state':'NV','publication':'Fixture code','content_selector':'main','legal_marker_regex':'§'};oi={'id':'fixture','heading':'§ 1 Map provision','url':BASE,'raw_ref':'raw/fixture.html'};orr=off.html_records(('<html><main><h2>§ 1 Map provision</h2>'+body+'</main></html>').encode(),oi,cfg)[0][0]
  return {'american-legal':(ar,'html','document_id'),'ecode':(er,'content_html','id'),'encodeplus':(pr,'body_html','id'),'official':(orr,'html','id')}
 def assert_safe(self,html):
  s=BeautifulSoup(html,'html.parser');self.assertFalse(s.select('img,picture,svg,image,use,source[srcset],video[poster]'),html);self.assertNotRegex(html,r'data:image/|url\s*\(',html)
  for el in s.select('object,embed'):self.assertFalse(el.get('type','').startswith('image/') or el.get('data','').startswith('data:image/'))
 def test_mixed_images_tables_normalized_html_and_text(self):
  for family,(r,key,idkey) in self.rows(IMAGES).items():
   with self.subTest(family=family):
    self.assertTrue(r[idkey]);self.assertTrue(r['heading']);self.assert_safe(r[key]);self.assertIn('[IMAGE]',r['text']);self.assertIn('Before image text.',r['text']);self.assertIn('After image text.',r['text']);self.assertGreaterEqual(r['text'].count('[IMAGE]'),8)
    tables=BeautifulSoup(r[key],'html.parser').select('table');self.assertEqual(len(tables),2);self.assertIn('[IMAGE]',tables[0].get_text());self.assertIn('[IMAGE]',tables[1].get_text())
 def test_image_only_source_identity_retained(self):
  for family,(r,key,idkey) in self.rows(IMAGE_ONLY).items():
   with self.subTest(family=family):self.assertTrue(r[idkey]);self.assertTrue(r['heading']);self.assertIn('[IMAGE]',r['text']);self.assert_safe(r[key]);self.assertFalse(any(a.get('required',False) for a in r['assets']))
 def test_image_bytes_absent_from_normalized_metadata(self):
  import json
  for family,(r,key,idkey) in self.rows(IMAGES).items():
   with self.subTest(family=family):self.assertNotIn(PIXEL_SENTINEL,json.dumps(r),'Normalized metadata must retain MIME/hash/locator rather than pixel payload')
 def test_explicit_nonimage_incorporation_remains_required(self):
  for family,(r,key,idkey) in self.rows(DOC).items():
   with self.subTest(family=family):self.assertTrue(any(a['url']=='https://example.invalid/document/123' and a.get('required',a.get('disposition')=='required-asset') for a in r['assets']))
if __name__=='__main__':unittest.main(verbosity=2)
