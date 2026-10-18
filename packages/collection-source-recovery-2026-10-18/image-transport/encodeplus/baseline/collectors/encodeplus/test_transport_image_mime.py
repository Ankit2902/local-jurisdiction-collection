"""Two MIME branches, actual fetch() and isolated temporary state; no network/images."""
import sys
sys.dont_write_bytecode=True
import io,json,socket,tempfile,unittest,urllib.error
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from . import transport
URL='https://online.encodeplus.com/regs/fixture/document'
class ImageMIME(unittest.TestCase):
 def invoke(self,status,mime,payload,deny_image_read):
  with tempfile.TemporaryDirectory(prefix='ep-mime-control-') as td:
   root=Path(td);out=root/'response.bin';gate=root/'isolated-gate';headers=Message();headers['Content-Type']=mime
   class Body(io.BytesIO):
    reads=0
    def read(self,*a,**kw):
     self.reads+=1
     if deny_image_read:raise AssertionError('IMAGE_BODY_READ_FORBIDDEN')
     return super().read(*a,**kw)
   body=Body(payload)
   if status==200:
    response=SimpleNamespace(status=status,headers=headers,read=body.read,close=body.close)
    opener=SimpleNamespace(open=lambda *a,**kw:response)
   else:
    error=urllib.error.HTTPError(URL,status,'Synthetic access refusal',headers,body)
    opener=SimpleNamespace(open=lambda *a,**kw:(_ for _ in ()).throw(error))
   stopped=False
   with patch.dict(transport.os.environ,{'ENCODEPLUS_GATE_DIR':str(gate)}),patch('urllib.request.build_opener',return_value=opener),patch.object(transport.time,'sleep'),patch.object(socket.socket,'connect',side_effect=AssertionError('NETWORK_FORBIDDEN')):
    try:transport.fetch(URL,out)
    except transport.Stopped:stopped=True
   receipt=json.loads(out.with_name(out.name+'.receipt.json').read_text());data=out.read_bytes();state=json.loads((gate/'state.json').read_text());requests=[json.loads(x) for x in (gate/'requests.jsonl').read_text().split('\n') if x]
   self.assertEqual(len(requests),1);self.assertEqual(receipt['transport_sha256'],transport.TRANSPORT_SHA256)
   return data,receipt,state,body.reads,stopped
 def test_padded_image_GET200_body_never_read(self):
  for mime in [' IMAGE/PNG ','\timage/svg+xml ; charset=UTF-8 ']:
   with self.subTest(mime=mime):
    body,r,state,reads,stopped=self.invoke(200,mime,b'SYNTHETIC_IMAGE_SENTINEL_NEVER_READ',True)
    self.assertEqual(reads,0);self.assertEqual(body,b'');self.assertEqual(r['http_status'],200);self.assertIs(r['image_body_intentionally_skipped'],True);self.assertIs(r['request_attempted'],True);self.assertFalse(stopped);self.assertFalse(state.get('stopped',False));self.assertEqual(r['sha256'],transport.digest(b''))
 def test_padded_image_HTTPError403_body_never_read_stop_preserved(self):
  for mime in [' IMAGE/PNG ','\tIMAGE/SVG+XML ; charset=UTF-8 ']:
   with self.subTest(mime=mime):
    body,r,state,reads,stopped=self.invoke(403,mime,b'SYNTHETIC_IMAGE_SENTINEL_NEVER_READ',True)
    self.assertEqual(reads,0);self.assertEqual(body,b'');self.assertEqual(r['http_status'],403);self.assertTrue(r['image_body_intentionally_skipped']);self.assertTrue(stopped);self.assertTrue(state['stopped']);self.assertEqual(state['stop_reason']['status'],403);self.assertEqual(r['headers']['Content-Type'],mime);self.assertTrue(r['challenge'])
 def test_ordinary_text_and_PDF_success_bodies_preserved(self):
  for mime,payload in [('text/html; charset=UTF-8',b'<main>Legal source text</main>'),(' application/pdf ',b'%PDF-synthetic-nonimage-control')]:
   with self.subTest(mime=mime):
    body,r,state,reads,stopped=self.invoke(200,mime,payload,False)
    self.assertEqual(body,payload);self.assertEqual(reads,1);self.assertEqual(r['http_status'],200);self.assertFalse(r['image_body_intentionally_skipped']);self.assertFalse(stopped)
 def test_ordinary_text_and_PDF_error_bodies_and_stop_preserved(self):
  for mime,payload in [('text/html',b'Permission denied'),('application/pdf',b'%PDF-synthetic-refusal-control')]:
   with self.subTest(mime=mime):
    body,r,state,reads,stopped=self.invoke(403,mime,payload,False)
    self.assertEqual(body,payload);self.assertEqual(reads,1);self.assertFalse(r['image_body_intentionally_skipped']);self.assertEqual(r['http_status'],403);self.assertTrue(state['stopped']);self.assertTrue(stopped)
if __name__=='__main__':unittest.main(verbosity=2)
