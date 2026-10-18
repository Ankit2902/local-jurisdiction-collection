import copy,hashlib,json,pathlib,tempfile,unittest
from unittest.mock import patch
import retained_native as r
class RetainedNativeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=pathlib.Path(self.tmp.name);self.source=self.base/'source';(self.source/'raw').mkdir(parents=True);self.body=b'%PDF-test-envelope-only-not-a-real-PDF';self.sha=hashlib.sha256(self.body).hexdigest();self.patch=patch.object(r,'SHA',self.sha);self.patch.start();self.addCleanup(self.patch.stop)
  self.cfg={'url':r.URL,'expected_sha256':self.sha,'expected_pages':62};state={'phase':'finished','config':self.cfg}
  for key in ['start','end']:
   rel='raw/'+key+'.pdf';(self.source/rel).write_bytes(self.body);state[key]={'path':rel,'url':r.URL,'sha256':self.sha};(self.source/(rel+'.receipt.json')).write_text(json.dumps({'url':r.URL,'sha256':self.sha,'http_status':200,'challenge':False,'started_at':'original-time'}))
  (self.source/'checkpoint.json').write_text(json.dumps(state))
 def test_original_receipt_preserved_and_no_parser(self):
  a=r.RetainedTransport(self.source,self.cfg);data,meta=a(self.base/'output',r.URL,'raw/start.pdf');self.assertEqual(data,self.body);self.assertEqual(meta['started_at'],'original-time');self.assertEqual((self.base/'output/raw/start.pdf.receipt.json').read_bytes(),(self.source/'raw/start.pdf.receipt.json').read_bytes());self.assertEqual(len(a.calls),1)
 def test_unknown_url_or_raw_reference_refuses(self):
  a=r.RetainedTransport(self.source,self.cfg)
  for url,rel in [(r.URL+'x','raw/start.pdf'),(r.URL,'raw/image.png')]:
   with self.assertRaises(ValueError):a(self.base/'output',url,rel)
  self.assertFalse((self.base/'output').exists())
 def test_mutated_native_bytes_refuse(self):
  (self.source/'raw/start.pdf').write_bytes(self.body+b'x')
  with self.assertRaises(ValueError):r.inspect_source(self.source,self.cfg)
 def test_changed_receipt_after_preflight_refuses(self):
  a=r.RetainedTransport(self.source,self.cfg);p=self.source/'raw/start.pdf.receipt.json';p.write_text(p.read_text()+' ')
  with self.assertRaises(ValueError):a(self.base/'output',r.URL,'raw/start.pdf')
 def test_wrong_config_refuses(self):
  cfg=copy.deepcopy(self.cfg);cfg['url']+='x'
  with self.assertRaises(ValueError):r.inspect_source(self.source,cfg)
 def test_refusal_receipt_refuses(self):
  p=self.source/'raw/end.pdf.receipt.json';d=json.loads(p.read_text());d['http_status']=429;p.write_text(json.dumps(d))
  with self.assertRaises(ValueError):r.inspect_source(self.source,self.cfg)
 def test_existing_output_not_overwritten(self):
  a=r.RetainedTransport(self.source,self.cfg);out=self.base/'output';a(out,r.URL,'raw/start.pdf')
  with self.assertRaises(ValueError):a(out,r.URL,'raw/start.pdf')
if __name__=='__main__':unittest.main()
