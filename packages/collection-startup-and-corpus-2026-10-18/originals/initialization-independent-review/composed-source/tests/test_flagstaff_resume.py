import base64,copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flagstaff_html as fh
from source_common import *
class Page:
 def __init__(self,mapping):self.mapping=mapping;self.calls=[]
 def goto(self,*a,**kw):
  from types import SimpleNamespace
  return SimpleNamespace(body=lambda:b'<title>Native cover</title>',status=200,headers={})
 def evaluate(self,fn,url):
  self.calls.append(url);raw=self.mapping[url];return {'status':200,'url':url,'headers':{'content-type':'text/html'},'data':base64.b64encode(raw).decode()}
class Context:
 def __init__(self,page):self.page=page
 def route(self,*a):pass
 def on(self,*a):pass
 def new_page(self):return self.page
 def close(self):pass
class Browser:
 version='synthetic browser, no network'
 def __init__(self,page):self.page=page
 def new_context(self):return Context(self.page)
 def close(self):pass
class PW:
 def __init__(self,page):self.page=page;self.chromium=self
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def launch(self,*a,**kw):return Browser(self.page)
class Resume(unittest.TestCase):
 def prepare(self,folder,partial_closing=False):
  folder.mkdir();url=fh.URL+'cgi/reader.pl?cite=Flagstaff01&archive=html';root={'source_url':fh.URL+'html/Flagstaff01/Flagstaff01.html','value':'../html/Flagstaff01/Flagstaff01.html','label':'Title 1','source_id':'Flagstaff01'};reader={'root':root,'url':url,'retained_sha256':'synthetic'};fragment=b'<p><input name="code" value="../html/Flagstaff01/section.html#s"><a href="../html/Flagstaff01/section.html#s" id="s">1 Legal heading</a></p>';curr=b'<p>The Flagstaff City Charter and City Code are current through Ordinance 2026-19, passed August 25, 2026.</p>';edges=fh.inventory([dict(reader,raw=fragment)]);state={'schema':'flagstaff-full-html-1','source_url':fh.URL,'started_at':stamp(),'code_fingerprint':{n:sha((Path(fh.__file__).parent/n).read_bytes()) for n in fh.FILES},'observed_readers':[reader],'artifacts':[],'errors':[],'blocked':[],'image_requests_blocked':[],'complete':False,'inventory':edges,'opening_currency':fh.currency(curr)}
  def artifact(role,url,body):
   rel=f'raw/{len(state["artifacts"]):04d}.bin';transport.atomic(folder/rel,body);state['artifacts'].append({'role':role,'source_url':url,'final_url':url,'status':200,'path':rel,'sha256':sha(body),'bytes':len(body),'headers':{}})
  artifact('toc-start',url,fragment);artifact('currency-start',fh.CURRENCY_URL,curr);artifact('content',root['source_url'],b'<div id="mainContent"><h1>Title 1</h1></div>')
  if partial_closing:artifact('toc-end',url,fragment)
  save(folder/'checkpoint.json',state);mapping={url:fragment,fh.ROOT_TOC_URL:fragment,fh.CURRENCY_URL:curr,fh.URL+'html/Flagstaff01/section.html':b'<div id="mainContent"><h3>1 Legal heading</h3><p>Body</p></div>'};return state,Page(mapping)
 def test_exact_resume_acquires_missing_only_and_recloses(self):
  with tempfile.TemporaryDirectory() as tmp:
   src=Path(tmp)/'source';s,page=self.prepare(src);before={a['path']:sha((src/a['path']).read_bytes()) for a in s['artifacts']}
   with patch.object(fh,'sync_playwright',return_value=PW(page)),patch.object(fh.transport,'ROOT',Path(tmp)/'gate'),patch.object(fh,'root_inventory',return_value=[s['observed_readers'][0]['root']]):r=fh.collect(src,resume=True)
   self.assertFalse(r['errors']);self.assertEqual(r['content_acquired'],2);self.assertTrue(r['closing_inventory_equal']);self.assertTrue(r['closing_currency_equal']);self.assertNotIn(s['artifacts'][2]['source_url'],page.calls);self.assertEqual(sum(a['role']=='toc-start' for a in r['artifacts']),1);self.assertEqual(sum(a['role']=='toc-end' for a in r['artifacts']),1)
   self.assertEqual(before,{name:sha((src/name).read_bytes()) for name in before})
 def test_interrupted_closing_preserved_and_recomputed(self):
  with tempfile.TemporaryDirectory() as tmp:
   src=Path(tmp)/'source';s,page=self.prepare(src,True);oldpath=s['artifacts'][-1]['path'];oldsha=s['artifacts'][-1]['sha256']
   with patch.object(fh,'sync_playwright',return_value=PW(page)),patch.object(fh.transport,'ROOT',Path(tmp)/'gate'),patch.object(fh,'root_inventory',return_value=[s['observed_readers'][0]['root']]):r=fh.collect(src,resume=True)
   self.assertFalse(r['errors']);self.assertEqual(sha((src/oldpath).read_bytes()),oldsha);self.assertEqual(sum(a['role']=='toc-end' for a in r['artifacts']),1);self.assertEqual(sum(a['role']=='abandoned-partial-toc-end' for a in r['artifacts']),1)
 def test_version_drift_refuses_before_browser(self):
  with tempfile.TemporaryDirectory() as tmp:
   src=Path(tmp)/'source';s,page=self.prepare(src);s['code_fingerprint']['flagstaff_html.py']='bad';save(src/'checkpoint.json',s)
   with patch.object(fh,'sync_playwright') as browser:
    with self.assertRaisesRegex(ValueError,'version mismatch'):fh.collect(src,resume=True)
    browser.assert_not_called()
 def test_retained_refusal_never_resumes(self):
  with tempfile.TemporaryDirectory() as tmp:
   src=Path(tmp)/'source';s,page=self.prepare(src);s['blocked']=[{'status':429}];save(src/'checkpoint.json',s)
   with patch.object(fh,'sync_playwright') as browser:
    with self.assertRaises(ValueError):fh.collect(src,resume=True)
    browser.assert_not_called()
if __name__=='__main__':unittest.main()
