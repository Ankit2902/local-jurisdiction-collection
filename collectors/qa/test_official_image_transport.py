"""Synthetic production collection: no separate image requests, readable placeholders."""
import contextlib,io,json,sys,tempfile,unittest
from email.message import Message
from urllib.error import HTTPError
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'collectors/official'));import collect,verify,post_transport
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
class RefusalBodies(unittest.TestCase):
 def invoke(self,post,status,mime,payload,forbid_read=False):
  headers=Message();headers['Content-Type']=mime
  class Body(io.BytesIO):
   reads=0
   def read(self,*a,**k):
    self.reads+=1
    if forbid_read:raise AssertionError('Image error body must never be read')
    return super().read(*a,**k)
  body=Body(payload);error=HTTPError(BASE,status,'Synthetic refusal',headers,body)
  opener=SimpleNamespace(open=lambda *a,**k:(_ for _ in ()).throw(error))
  with patch.object(collect.transport,'reserve') as reserve,patch.object(collect.transport,'stop') as stop,patch('urllib.request.build_opener',return_value=opener):
   result=post_transport.fetch(BASE,[('book','one')]) if post else collect.transport.fetch(BASE)
  self.assertEqual(reserve.call_count,1)
  return result,body.reads,stop.call_count
 def test_get_error_images_omitted_without_read_and_stop_preserved(self):
  for status in [403,404,429]:
   for mime in ['image/png',' IMAGE/SVG+XML ']:
    with self.subTest(status=status,mime=mime):
     (data,r),reads,stops=self.invoke(False,status,mime,b'image body must not be accessed',True)
     self.assertEqual((data,reads),(b'',0));self.assertTrue(r['policy_omitted_image']);self.assertEqual(r['bytes'],0);self.assertEqual(stops,1 if status in [403,429] else 0)
 def test_post_error_images_omitted_without_read_and_stop_preserved(self):
  for status in [403,404,429]:
   (data,r),reads,stops=self.invoke(True,status,'image/png',b'image body must not be accessed',True)
   self.assertEqual((data,reads),(b'',0));self.assertTrue(r['policy_omitted_image']);self.assertEqual(stops,1 if status in [403,429] else 0)
 def test_nonimage_error_evidence_retained(self):
  for post in [False,True]:
   (data,r),reads,stops=self.invoke(post,403,'text/html',b'<html>Permission denied</html>')
   self.assertEqual(data,b'<html>Permission denied</html>');self.assertEqual(reads,1);self.assertEqual(stops,1);self.assertTrue(r['access_stop']);self.assertNotIn('policy_omitted_image',r)
if __name__=='__main__':unittest.main(verbosity=2)
