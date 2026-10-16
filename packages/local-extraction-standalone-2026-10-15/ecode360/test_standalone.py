import contextlib,copy,io,json,tempfile,unittest
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
 def test_synthetic_acceptance_receipt_stays_immutable(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(s,'state',side_effect=lambda *a:copy.deepcopy(self.legal())),patch.object(s.time,'sleep'):
   out=Path(tmp)/'out';r=s.acquire(Browser(),self.job(),out)
   self.assertTrue(r['standalone_e2e_verified']);receipt=(out/'receipt.json').read_bytes();result=e.load(out/'pipeline/e2e-result.json')
   self.assertEqual(result['receipt_sha256'],e.digest(receipt));self.assertEqual((out/'pipeline/capture-receipt.json').read_bytes(),receipt)
   self.assertNotIn('supported_browser_e2e_verified',result);self.assertNotIn('CUA',result['transport'])
   manifest=e.load(out/'pipeline/imported/artifacts.json');self.assertEqual(manifest['artifacts'][0]['transport'],'standalone Python Playwright public source')
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
