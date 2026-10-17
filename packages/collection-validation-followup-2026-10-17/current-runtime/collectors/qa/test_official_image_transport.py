"""Synthetic production collection: no separate image requests, readable placeholders."""
import contextlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'collectors/official'));import collect,verify
BASE='https://example.invalid/code/'
BODY=b'<html><main><h2>Section 1 Legal provision</h2><p>Every application shall contain the required information.</p><img src="https://example.invalid/image.png"><svg><image href="https://example.invalid/map.png"/></svg><table><tr><td>Cell<img src="cell.png"></td></tr></table></main></html>'
class Tests(unittest.TestCase):
 def test_no_image_fetch_and_complete_selected_synthetic_document(self):
  calls=[]
  def fake(url,*args,**kwargs):
   calls.append(url);self.assertEqual(url,BASE,'Collector attempted a separate image request');return BODY,{'url':url,'status':200,'success':True,'headers':{'content-type':'text/html'},'sha256':collect.model.sha(BODY)}
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);cfg={'schema':1,'id':'qa-synthetic-image','jurisdiction':'Fixture','state':'NV','publication':'Synthetic single document','source_url':BASE,'mode':'html_single','transport':'http','content_selector':'main','legal_marker_regex':'shall contain'};path=root/'config.json';path.write_text(json.dumps(cfg));out=root/'run'
   with patch.object(collect.transport,'fetch',fake),contextlib.redirect_stdout(io.StringIO()):status=collect.collect(path,out)
   self.assertEqual(status,0);self.assertTrue(verify.verify(out)['requested_coverage_complete']);self.assertEqual(calls,[BASE,BASE,BASE]);rows=[json.loads(x) for x in (out/'records.jsonl').read_text().splitlines()];self.assertIn('[IMAGE]',rows[0]['text']);self.assertFalse(collect.BeautifulSoup(rows[0]['html'],'html.parser').select('img,svg'))
if __name__=='__main__':unittest.main(verbosity=2)
