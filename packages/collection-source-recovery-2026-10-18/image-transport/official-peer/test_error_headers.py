"""Independent error-header and body-denial controls; all transport/state mocked."""
import sys
sys.dont_write_bytecode=True
import hashlib,io,socket,unittest
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
ROOT=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
sys.path.insert(0,str(ROOT/'collectors/official'))
import transport,post_transport
URL='https://example.invalid/source'
class IndependentErrorControls(unittest.TestCase):
 def invoke(self,post,status,mime,payload,deny_read,extra=None):
  headers=Message();headers['cOnTeNt-TyPe']=mime
  for k,v in (extra or {}).items():headers[k]=v
  class Body(io.BytesIO):
   reads=0
   def read(self,*args,**kwargs):
    self.reads+=1
    if deny_read:raise AssertionError('Forbidden image response body read')
    return super().read(*args,**kwargs)
  body=Body(payload);error=HTTPError(URL,status,'Controlled status',headers,body)
  with patch.object(transport,'reserve') as reserve,patch.object(transport,'stop') as stop,patch('urllib.request.build_opener',return_value=SimpleNamespace(open=lambda *a,**kw:(_ for _ in ()).throw(error))),patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')):
   data,receipt=(post_transport.fetch(URL,[('publication','literal value')]) if post else transport.fetch(URL))
  self.assertEqual(reserve.call_args.args,(URL,));self.assertEqual(reserve.call_count,1)
  self.assertEqual(receipt['status'],status);self.assertEqual(receipt['final_url'],URL);self.assertEqual(receipt['headers'],dict(headers));self.assertEqual(receipt['bytes'],len(data));self.assertEqual(receipt['sha256'],hashlib.sha256(data).hexdigest());self.assertIn('Controlled status',receipt['error'])
  if stop.called:
   self.assertEqual(stop.call_count,1);self.assertEqual(stop.call_args.args[:3],(URL,status,dict(headers)))
  return data,receipt,body.reads,stop.called
 def test_mixed_case_padded_SVG_and_retry_headers_preserved_without_body(self):
  for post in [False,True]:
   for status in [403,429]:
    with self.subTest(post=post,status=status):
     data,r,reads,stopped=self.invoke(post,status,' IMAGE/SVG+XML ; charset=UTF-8 ',b'NEVER_READ_SYNTHETIC_PAYLOAD',True,{'Retry-After':'120'})
     self.assertEqual(data,b'');self.assertEqual(reads,0);self.assertIs(r['policy_omitted_image'],True);self.assertIs(r['access_stop'],True);self.assertTrue(stopped)
 def test_image_404_header_challenge_stops_without_read_and_plain404_does_not(self):
  for post in [False,True]:
   for challenge in [False,True]:
    with self.subTest(post=post,challenge=challenge):
     data,r,reads,stopped=self.invoke(post,404,'image/png',b'NEVER_READ_SYNTHETIC_PAYLOAD',True,{'Cf-Mitigated':'challenge'} if challenge else {})
     self.assertEqual((data,reads),(b'',0));self.assertEqual(stopped,challenge);self.assertEqual(r.get('access_stop',False),challenge)
 def test_nonimage_text_and_body_challenge_evidence_remain_available(self):
  for post in [False,True]:
   for status,payload,stopped in [(403,b'Permission denied',True),(404,b'<title>Just a moment</title>',True),(404,b'Not found',False)]:
    with self.subTest(post=post,status=status,payload=payload):
     data,r,reads,actual=self.invoke(post,status,'text/html; charset=UTF-8',payload,False)
     self.assertEqual(data,payload);self.assertEqual(reads,1);self.assertEqual(actual,stopped);self.assertNotIn('policy_omitted_image',r)
if __name__=='__main__':unittest.main(verbosity=2)
