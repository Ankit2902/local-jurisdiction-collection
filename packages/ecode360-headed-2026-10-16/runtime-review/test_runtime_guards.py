#!/usr/bin/env python3
"""Offline fake-runtime regression of the frozen worker source. Never launches a browser."""
import copy,hashlib,importlib.metadata,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'evidence/reviewed-headed-probe.py.txt'
EXPECTED='4cb2651f0e43a6053287542ab2f0147238f7ae8df5836ee66f0c5b2f95239891'
URL='https://ecode360.com/12345'
class ValidationError(Exception):pass

def dump(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2))

class Response:
 def __init__(self,status=200,url=URL,headers=None):
  self.url=url;self.status=status;self.headers=headers or {};self.request=types.SimpleNamespace(resource_type='document',method='GET')
 def body(self):raise AssertionError('The response callback must not read or wait for the response body')

class Runtime:
 def __init__(self,mode='legal',mutation=None):
  self.mode=mode;self.mutation=mutation;self.launches=[];self.context_args=[];self.waits=[];self.ui_actions=[];self.closed=[];self.state_calls=0
  self.browser=types.SimpleNamespace(version='fake-offline',new_context=self.new_context,close=lambda:self.closed.append('browser'))
  self.chromium=types.SimpleNamespace(launch=self.launch)
 def __enter__(self):return self
 def __exit__(self,*args):return False
 def launch(self,**kw):self.launches.append(kw);return self.browser
 def new_context(self,**kw):
  self.context_args.append(kw)
  self.ctx=types.SimpleNamespace(new_page=lambda:self.page,route=self.route,on=self.on,close=lambda:self.closed.append('context'))
  self.page=types.SimpleNamespace(goto=self.goto,screenshot=self.screenshot,wait_for_timeout=lambda ms:self.waits.append(ms),content=lambda:'<html>fake</html>')
  return self.ctx
 def route(self,pattern,fn):self.route_guard=fn
 def on(self,event,fn):self.callback=fn
 def emit429(self):self.callback(Response(429,'https://api.ecode360.com/sample?secret=redacted',{'retry-after':'120','set-cookie':'secret-value','content-type':'text/html'}))
 def goto(self,*args,**kwargs):
  r=Response(429 if self.mode=='initial429' else 200,headers={'retry-after':'120','set-cookie':'secret-value'});self.callback(r);return r
 def screenshot(self,**kw):
  if Path(kw['path']).name=='final.png':
   if self.mode=='late429':self.emit429()
   if self.mode=='late_exception':raise RuntimeError('synthetic final screenshot failure')
 def state(self,page):
  self.state_calls+=1
  s={'url':URL,'challenge':False,'identity':{'customer_id':'TEST','code_id':'CODE','currency':'2026-01-26'},'heading_node_id':'12345','html':'<article>legal content</article>','section_bodies':['body'],'toc':['node']}
  if self.mutation and self.state_calls%2==0:self.mutation(s)
  return s

def load_module(runtime):
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED,'frozen source changed'
 fake_e=types.ModuleType('ecode360');fake_e.ValidationError=ValidationError;fake_e.fetch_url=lambda x:x;fake_e.load=lambda p:json.loads(Path(p).read_text());fake_e.dump=dump;fake_e.digest=lambda b:hashlib.sha256(b).hexdigest();fake_e.now=lambda:'2026-10-16T00:00:00+00:00'
 fake_pw=types.ModuleType('playwright.sync_api');fake_pw.sync_playwright=lambda:runtime
 fake_st=types.ModuleType('standalone');fake_st.state=runtime.state
 module=types.ModuleType('reviewed_probe');module.__file__=str(SOURCE)
 with patch.dict(sys.modules,{'ecode360':fake_e,'standalone':fake_st,'playwright.sync_api':fake_pw}):exec(compile(SOURCE.read_text(),str(SOURCE),'exec'),module.__dict__)
 return module

class GuardTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='offline-guard-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  dump(self.root/'route-registry.json',[{'slug':'test','discovery_url':URL,'customer_id':'TEST','code_id':'CODE'}]);(self.root/'standalone.py').write_text('# synthetic helper, never executed\n');(self.root/'ecode360.py').write_text('# synthetic core helper, never executed\n');dump(self.root/'authorization.json',{'explicit_user_authorized_resumption':True})
 def call(self,runtime,**kwargs):
  m=load_module(runtime);m.ROOT=self.root
  tick=iter(n/4 for n in range(1000))
  with patch.object(importlib.metadata,'version',return_value='offline'),patch.object(m.time,'monotonic',side_effect=lambda:next(tick)):
   result=m.probe(URL,'test','TEST',self.root/'capture',self.root/'authorization.json',seconds=1,**kwargs)
  return m,result
 def test_ordinary_headed_fresh_context_accepts_stable_legal_source(self):
  rt=Runtime();_,r=self.call(rt)
  self.assertTrue(r['accepted']);self.assertEqual(rt.launches,[{'channel':'chrome','headless':False}]);self.assertEqual(rt.context_args,[{}]);self.assertEqual(rt.ui_actions,[]);self.assertEqual(rt.closed,['context','browser'])
 def test_initial429_stops_before_passive_wait_and_retains_only_safe_headers(self):
  rt=Runtime('initial429');_,r=self.call(rt)
  self.assertFalse(r['accepted']);self.assertEqual(rt.waits,[]);self.assertEqual(rt.state_calls,0)
  stop=json.loads((self.root/'headed-live/CURRENT-HOST-STOP.json').read_text());self.assertEqual(stop['event']['headers'],{'retry-after':'120'});self.assertFalse(stop['automatic_retry'])
  self.assertNotIn('secret-value',json.dumps(r));self.assertIn('not_read_in_callback',r['rate_limit']['body_capture_status'])
 def test_guard_aborts_publisher_and_subdomains_after429_only(self):
  rt=Runtime('initial429');self.call(rt)
  for url,expected in [('https://ecode360.com/a','abort'),('https://files.ecode360.com/a','abort'),('https://example.org/a','continue')]:
   actions=[];route=types.SimpleNamespace(request=types.SimpleNamespace(url=url),abort=lambda:actions.append('abort'),continue_=lambda:actions.append('continue'));rt.route_guard(route);self.assertEqual(actions,[expected])
 def test_existing_stop_refuses_next_browser_launch(self):
  rt=Runtime('initial429');self.call(rt);other=Runtime();m=load_module(other);m.ROOT=self.root
  with self.assertRaisesRegex(ValidationError,'host stop'):m.probe(URL,'test','TEST',self.root/'next',self.root/'authorization.json')
  self.assertEqual(other.launches,[])
 def test_late429_revokes_previously_accepted_capture(self):
  _,r=self.call(Runtime('late429'));self.assertFalse(r['accepted']);self.assertIsNotNone(r['rate_limit']);self.assertTrue((self.root/'headed-live/CURRENT-HOST-STOP.json').exists())
 def test_late_exception_revokes_previously_accepted_capture(self):
  _,r=self.call(Runtime('late_exception'));self.assertFalse(r['accepted']);self.assertIn('synthetic',r['error'])
 def test_after_snapshot_rejects_url_challenge_customer_code_currency_heading_and_html_changes(self):
  mutations=[lambda s:s.update(url='https://ecode360.com/99999'),lambda s:s.update(challenge=True),lambda s:s['identity'].update(customer_id='WRONG'),lambda s:s['identity'].update(code_id='WRONG'),lambda s:s['identity'].update(currency='changed'),lambda s:s.update(heading_node_id='99999'),lambda s:s.update(html='changed')]
  for mutation in mutations:
   with self.subTest(mutation=mutation):
    capture=self.root/'capture'
    if capture.exists():
     import shutil;shutil.rmtree(capture)
    _,r=self.call(Runtime(mutation=mutation));self.assertFalse(r['accepted'])
 def test_wrong_registry_identity_and_unapproved_code_refuse_before_launch(self):
  for kwargs in [{'customer':'WRONG'},{'code_id':'WRONG'},{'url':'https://ecode360.com/99999'}]:
   rt=Runtime();m=load_module(rt);m.ROOT=self.root;args=dict(url=URL,slug='test',customer='TEST',out=self.root/'capture',authorization=self.root/'authorization.json');args.update(kwargs)
   with self.assertRaises(ValidationError):m.probe(**args)
   self.assertEqual(rt.launches,[])
 def test_unauthorized_resumption_refuses_before_browser_launch(self):
  dump(self.root/'authorization.json',{'explicit_user_authorized_resumption':False});rt=Runtime();m=load_module(rt);m.ROOT=self.root
  with self.assertRaisesRegex(ValidationError,'authorization'):m.probe(URL,'test','TEST',self.root/'capture',self.root/'authorization.json')
  self.assertEqual(rt.launches,[])
 def test_export_inspection_does_not_touch_controls_when_host_already_stopped(self):
  rt=Runtime();m=load_module(rt);page=types.SimpleNamespace(evaluate=lambda _: {'sections':[{'id':'12345','text':10}]},locator=lambda *_:self.fail('selection must not occur'))
  result=m.inspect_export_ui(page,None,self.root,{'status':429});self.assertFalse(result['file_acquired']);self.assertIn('host stopped',result['error'])
 def test_export_429_after_local_selection_prevents_toolbar_action(self):
  rt=Runtime();m=load_module(rt);rate={}
  class LocalSelection:
   def check(self,**kw):rate.update(status=429)
   def inner_text(self,**kw):return 'local citation'
  page=types.SimpleNamespace(on=lambda *args:None,evaluate=lambda _: {'sections':[{'id':'12345','text':10}]},locator=lambda selector:types.SimpleNamespace(is_visible=lambda:False) if selector.startswith('#silktide') else LocalSelection(),get_by_role=lambda *_a,**_k:self.fail('toolbar action must not occur'))
  result=m.inspect_export_ui(page,types.SimpleNamespace(on=lambda *args:None),self.root,rate);self.assertFalse(result['file_acquired']);self.assertIn('host stopped after local selection',result['error'])
 def test_direct_probe_rejects_unbounded_passive_wait_before_launch(self):
  for seconds in [0,61,-1]:
   rt=Runtime();m=load_module(rt);m.ROOT=self.root
   with self.assertRaisesRegex(ValidationError,'bounded passive wait'):m.probe(URL,'test','TEST',self.root/'capture',self.root/'authorization.json',seconds=seconds)
   self.assertEqual(rt.launches,[])
 def test_export429_during_ordinary_consent_prevents_content_selection(self):
  rt=Runtime();m=load_module(rt);rate={}
  class Consent:
   def is_visible(self):return True
   def inner_text(self):return 'Reject non-essential'
   def click(self,**kwargs):rate.update(status=429)
  class Backdrop:
   def wait_for(self,**kwargs):pass
  def locator(selector):
   if selector=='#silktide-backdrop':return Backdrop()
   if selector.startswith('#silktide'):return Consent()
   self.fail('No content selection after consent response429')
  page=types.SimpleNamespace(evaluate=lambda _: {'sections':[{'id':'12345','text':10}]},locator=locator)
  result=m.inspect_export_ui(page,None,self.root,rate);self.assertFalse(result['file_acquired']);self.assertIn('host stopped before selection',result['error'])
 def test_export429_after_pdf_action_prevents_download_retention(self):
  rt=Runtime();m=load_module(rt);rate={};saved=[];callbacks={}
  class Element:
   def is_visible(self):return False
   def inner_text(self,**kwargs):return 'Section 1'
   def check(self,**kwargs):pass
   def all(self):return []
  class Button:
   def __init__(self,name):self.name=name
   def is_visible(self):return True
   def is_enabled(self):return True
   def all_text_contents(self):return ['PDF']
   def click(self,**kwargs):
    if self.name=='PDF':
     callbacks['download'](types.SimpleNamespace(suggested_filename='sample.pdf',save_as=lambda p:saved.append(p),url='https://ecode360.com/export'))
     rate.update(status=429)
  page=types.SimpleNamespace(evaluate=lambda _: {'sections':[{'id':'12345','text':10}]},locator=lambda selector:Element(),on=lambda event,fn:callbacks.update({event:fn}),get_by_role=lambda role,**kwargs:Button(kwargs.get('name')),wait_for_timeout=lambda _:None,content=lambda:'<html/>',screenshot=lambda **kwargs:None)
  m.state=lambda page:{'identity':{'customer_id':'TEST','code_id':'CODE'}}
  result=m.inspect_export_ui(page,types.SimpleNamespace(on=lambda *args:None),self.root,rate);self.assertFalse(result['file_acquired']);self.assertEqual(saved,[]);self.assertIn('host stopped during PDF generation',result['error'])
 def test_public_event_url_excludes_query_and_fragment(self):
  m=load_module(Runtime());self.assertEqual(m.public_url('https://ecode360.com/a?token=SECRET#fragment'),'https://ecode360.com/a')

if __name__=='__main__':unittest.main(verbosity=2)
