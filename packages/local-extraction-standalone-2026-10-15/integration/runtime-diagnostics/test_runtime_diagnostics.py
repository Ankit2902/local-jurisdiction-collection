import argparse,contextlib,io,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import runtime_diagnostics as d

class RuntimePolicyTests(unittest.TestCase):
 def test_proxy_credentials_and_ca_paths_are_not_disclosed(self):
  with patch.dict(os.environ,{'https_proxy':'http://private-user:private-password@internal-proxy.example:8080','NODE_EXTRA_CA_CERTS':'/private/account/secret-ca.pem'}):
   data=d.inspect_runtime();text=json.dumps(data)
  for secret in ['private-user','private-password','internal-proxy.example','/private/account/secret-ca.pem']:self.assertNotIn(secret,text)
  self.assertTrue(any(x['has_embedded_credentials'] for x in data['proxy_configuration_presence_only']))
  self.assertTrue(data['custom_ca_configuration_presence_only']['NODE_EXTRA_CA_CERTS']['present'])
 def test_errors_and_final_urls_redact_authentication_and_query_values(self):
  message=d.safe_error('Failed https://alice:super-secret@example.org/path?auth=private-token')
  for secret in ['alice','super-secret','private-token']:self.assertNotIn(secret,message)
  self.assertEqual(d.public_url('https://example.org/code?__cf_chl_rt_tk=private-challenge#1.01'),'https://example.org/code?[redacted]#1.01')
 def test_http429_records_retry_after_and_stops_different_route_on_same_host(self):
  calls=[]
  class Page:
   url='https://publisher.example/one'
   def goto(self,url,**kwargs):calls.append(url);return types.SimpleNamespace(status=429,headers={'server':'test','retry-after':'120','set-cookie':'secret-cookie-value'})
   def title(self):return 'Rate limited'
   def content(self):return '<html><body>Rate limited</body></html>'
   def locator(self,selector):return types.SimpleNamespace(inner_text=lambda **kw:'Rate limited')
  class Context:
   count=0
   def cookies(self):self.count+=1;return [] if self.count==1 else [{'name':'fresh-session','value':'secret-cookie-value'}]
   def new_page(self):return Page()
   def close(self):pass
  class Browser:
   version='normal-test-browser'
   def new_context(self):return Context()
   def close(self):pass
  class Runtime:
   chromium=types.SimpleNamespace(launch=lambda **kwargs:Browser())
   def __enter__(self):return self
   def __exit__(self,*args):pass
  module=types.ModuleType('playwright.sync_api');module.sync_playwright=lambda:Runtime()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);args=argparse.Namespace(url='https://publisher.example/one',out=str(root/'one'),host_ledger=None,engine='chrome',headed=False,timeout=5,expect_selector=None,readiness_seconds=1,screenshot=False)
   with patch.dict(sys.modules,{'playwright.sync_api':module}),contextlib.redirect_stdout(io.StringIO()):d.probe(args)
   receipt=json.loads((root/'one/receipt.json').read_text());ledger=json.loads((root/'HOST-STOP.json').read_text())
   self.assertEqual(receipt['http_status'],429);self.assertEqual(ledger['stopped_hosts']['publisher.example']['retry_after'],'120')
   self.assertNotIn('secret-cookie-value',json.dumps(receipt));self.assertNotIn('set-cookie',receipt['response_headers_allowlist'])
   args.url='https://publisher.example/a-different-route';args.out=str(root/'two')
   with self.assertRaisesRegex(ValueError,'Host-wide stop'):d.probe(args)
   self.assertEqual(calls,['https://publisher.example/one']);self.assertFalse((root/'two').exists())
 def test_documented_ecode_host_stop_blocks_before_browser_import(self):
  ledger=json.loads((Path(__file__).parent/'probes/HOST-STOP.json').read_text())
  self.assertEqual(ledger['stopped_hosts']['ecode360.com']['status'],429)
  with tempfile.TemporaryDirectory() as tmp:
   args=argparse.Namespace(url='https://ecode360.com/never-requested',out=str(Path(tmp)/'new'),host_ledger=str(Path(__file__).parent/'probes/HOST-STOP.json'),engine='chromium',headed=True)
   with self.assertRaisesRegex(ValueError,'Host-wide stop'):d.probe(args)

if __name__=='__main__':unittest.main(verbosity=2)
