import contextlib,copy,io,json,tempfile,unittest,subprocess,sys
from pathlib import Path
from unittest.mock import patch,MagicMock
import standalone as s
import ecode360 as e
class Response:
 status=200;headers={'content-type':'text/html'};request=None
 def body(self):return b'<html>Synthetic response, not a live source</html>'
class Page:
 url='https://ecode360.com/100'
 def goto(self,*a,**kw):return Response()
 def locator(self,*a):return self
 @property
 def first(self):return self
 def wait_for(self,*a,**kw):return None
 def content(self):return '<html>synthetic blocked page</html>'
 def title(self):return 'Synthetic'
 def screenshot(self,path,**kw):Path(path).write_bytes(b'synthetic screenshot')
class Browser:
 version='synthetic test runtime'
 def new_context(self):
  page=Page();ctx=MagicMock();ctx.new_page.return_value=page;ctx.pages=[page];return ctx
class StandaloneTests(unittest.TestCase):
 def job(self):return {'slug':'test-ca','jurisdiction':'Test','discovery_url':'https://ecode360.com/100'}
 def legal(self):
  html='<div id="codeContent"><div id="toc"><div class="contentTitle" data-guid="101" data-code-content-type="section"><a class="titleLink" href="/101"><span class="titleNumber">§ 1</span><span class="titleTitle">Example</span></a></div></div><article><header><div class="contentTitle" data-guid="101" data-code-content-type="section"><span class="titleNumber">§ 1</span><span class="titleTitle">Example</span></div></header><div id="101_content" class="section_content"><p>Sample legal text.</p></div></article></div>'
  return {'url':'https://ecode360.com/100','title':'Chapter 1: Synthetic','html':html,'identity':{'customer_id':'TE0000','code_id':'1','currency_raw':'2026-01-01'},'heading_node_id':'100','section_bodies':['101_content'],'toc':[{'node_id':'101'}],'challenge':False}
 def test_synthetic_legacy_receipt_cannot_bypass_registry(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(s,'state',side_effect=lambda *a:copy.deepcopy(self.legal())),patch.object(s.time,'sleep'):
   out=Path(tmp)/'out'
   with self.assertRaisesRegex(e.ValidationError,'route registry'):s.acquire(Browser(),self.job(),out)
   receipt=e.load(out/'receipt.json');self.assertTrue(receipt['accepted'])
   self.assertFalse((out/'pipeline/exports/aggregate-fulltext.json').exists())
 def test_historical_direct_entries_are_disabled(self):
  for filename in ['standalone.py','acquire_browser.py']:
   result=subprocess.run([sys.executable,str(Path(__file__).with_name(filename))],capture_output=True,text=True,timeout=10)
   self.assertEqual(result.returncode,2);self.assertIn('Historical acquisition entry disabled',result.stderr)
 def test_serial_reuse_and_unknown_slug_refused_before_launch(self):
  with tempfile.TemporaryDirectory() as tmp:
   (Path(tmp)/'receipt.json').write_text('immutable')
   cmd=[sys.executable,str(Path(__file__).with_name('run_serial.py')),'--out',tmp,'--authorization',str(Path(__file__).parent/'headed-live/RESUMPTION.json')]
   result=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
   self.assertEqual(result.returncode,2);self.assertIn('new empty output',result.stderr)
   result=subprocess.run(cmd+['--slugs','unknown-city'],capture_output=True,text=True,timeout=10)
   self.assertEqual(result.returncode,2);self.assertIn('unreviewed jurisdiction',result.stderr)
   result=subprocess.run(cmd+['--slugs'],capture_output=True,text=True,timeout=10)
   self.assertEqual(result.returncode,2);self.assertIn('empty explicit',result.stderr)
 def test_serial_failure_returns_nonzero_and_default_includes_foster(self):
  import run_serial as runner
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);e.dump(root/'route-registry.json',[dict(self.job(),customer_id='TE0000',code_id='1'),dict(self.job(),slug='foster-city-ca',customer_id='FO4449',code_id='2')]);e.dump(root/'auth.json',{'explicit_user_authorized_resumption':True})
   fake={'accepted':False,'initial_http_status':403,'final_document_http_status':403,'rate_limit':None}
   with patch.object(runner,'ROOT',root),patch.object(runner,'probe',return_value=fake) as capture,patch.object(runner.time,'sleep'),contextlib.redirect_stdout(io.StringIO()):
    code=runner.main(['--out',str(root/'fresh'),'--authorization',str(root/'auth.json')])
   self.assertEqual(code,2);self.assertEqual(capture.call_count,2);self.assertEqual(capture.call_args_list[-1].args[1],'foster-city-ca')
 def test_challenge_never_parsed_or_retried(self):
  state=self.legal();state['challenge']=True;state['html']=None;state['identity']={k:None for k in state['identity']}
  with tempfile.TemporaryDirectory() as tmp,patch.object(s,'state',return_value=state) as view:
   r=s.acquire(Browser(),self.job(),Path(tmp)/'out');self.assertFalse(r['accepted']);self.assertEqual(view.call_count,1);self.assertFalse((Path(tmp)/'out/pipeline').exists())
 def test_existing_output_refused(self):
  with tempfile.TemporaryDirectory() as tmp:
   (Path(tmp)/'receipt.json').write_text('retained')
   with self.assertRaises(e.ValidationError):s.acquire(Browser(),self.job(),tmp)
 def test_host_429_stops_remaining_queue(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);routes=root/'routes.json';e.dump(routes,[self.job(),dict(self.job(),slug='other-ca')]);pw=MagicMock();runtime=MagicMock();pw.__enter__.return_value=runtime
   with patch.object(s,'ROOT',root),patch.object(s,'sync_playwright',return_value=pw),patch.object(s,'acquire',return_value={'http_status':429,'accepted':False,'standalone_e2e_verified':False,'response_headers':{'retry-after':'120'},'blocker':'rate limit'}) as call,contextlib.redirect_stdout(io.StringIO()):
    code=s.main(['--routes',str(routes),'--out',str(root/'result')]);self.assertEqual(code,2);self.assertEqual(call.call_count,1)
   self.assertEqual(e.load(root/'standalone-live/ecode360-host-throttle.json')['retry_after'],'120')
 def test_retained_throttle_prevents_launch(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);e.dump(root/'standalone-live/ecode360-host-throttle.json',{'status':'stop'});e.dump(root/'routes.json',[self.job()])
   with patch.object(s,'ROOT',root),patch.object(s,'sync_playwright') as runtime,contextlib.redirect_stderr(io.StringIO()):
    with self.assertRaises(SystemExit):s.main(['--routes',str(root/'routes.json'),'--out',str(root/'result')])
    runtime.assert_not_called()
if __name__=='__main__':unittest.main()
