"""Network-free, synthetic graph fault tests. Fixtures are intentionally not real law."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from collectors.ecode.engine import *
from collectors.ecode.common import *
BASE='https://ecode360.com/ZZ9000'
def valid_pdf():
 from pypdf import PdfWriter
 writer=PdfWriter();writer.add_blank_page(width=72,height=72);stream=io.BytesIO();writer.write(stream);return stream.getvalue()
def page(guid,heading,toc='',bodies=''):
 return ('''<!doctype html><html><head><title>Synthetic Test Municipality</title></head><body data-cust-id="ZZ9000" data-code-id="fixture-1" data-current-code-id="fixture-1" data-code-date="2099-01-01" data-customer-name="Synthetic Test Municipality, NV" data-customer='{"state":"NV"}' '''+(('data-guid="'+guid+'"') if guid else '')+'''><h1 id="pageTitle">'''+heading+'''</h1><div id="codeContent"><nav id="toc">'''+toc+'''</nav>'''+bodies+'''</div></body></html>''').encode()
def title(n,h,kind='chapter'):
 return f'<div class="contentTitle" id="{n}_title" data-guid="{n}" data-full-title="{h}" data-code-content-type="{kind}"><a class="titleLink" href="https://ecode360.com/{n}">{h}</a></div>'
ROOT=page(None,'Synthetic Code',title('101','Chapter 1')+title('102','Chapter 2'))
ONE=page('101','Chapter 1',title('201','§ 1-1. Operative section','section'),'<div class="chapter_content content" id="101_content"><p class="history">Adopted fixture history.</p></div><div id="childContent">'+title('201','§ 1-1. Operative section','section')+'<div class="content" id="201_content"><p>Alpha legal text.</p><table><tr><th rowspan="2">A</th><td>One<table><tr><td>Nested</td></tr></table></td></tr><tr><td>Two</td></tr></table><p class="footnote">Fixture note.</p></div></div>')
TWO=page('102','Chapter 2',title('202','§ 2-1. Operative section','section'),'<div id="childContent">'+title('202','§ 2-1. Operative section','section')+'<div class="content" id="202_content"><p>Beta legal text.</p></div></div>')
SOURCES={BASE:ROOT,'https://ecode360.com/101':ONE,'https://ecode360.com/102':TWO}
class FakeBrowser:
 fail=None
 def __init__(self,*a,**k):pass
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def fetch(self,url,method='GET'):
  if self.fail==url:raise RuntimeError('Synthetic interruption before second chapter')
  return SOURCES[url],{'url':url,'requested_url':url,'status':200,'headers':{'content-type':'text/html'},'transport':'SYNTHETIC TEST ONLY','retrieved_at':'2099-01-01'}
 bootstrap=fetch
 def check(self,*a):pass
CFG={'family':'ecode360','url':BASE,'jurisdiction':'Synthetic Test Municipality','state':'NV','publication':None,'subtree':False,'max_items':None,'gate_dir':None}
class FaultTests(unittest.TestCase):
 def setUp(self):
  self.advisory_patch=patch('collectors.ecode.engine.enforce_published_advisory');self.advisory_patch.start();self.addCleanup(self.advisory_patch.stop)
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def make(self,name='full'):
  out=self.root/name
  with patch('collectors.ecode.browser.Browser',FakeBrowser):r=collect(CFG,out)
  self.assertTrue(r['complete'],r);self.assertTrue(verify(out)['complete']);return out
 def test_full_and_tables(self):
  out=self.make();rows=[json.loads(x) for x in (out/'records.jsonl').read_text().splitlines()];self.assertEqual(len(rows),3);self.assertIn('rowspan="2"',next(r for r in rows if r['id']=='201')['semantic_html']);self.assertEqual(read(out/'coverage.json')['inventory_nodes'],5)
 def test_missing_artifact(self):
  out=self.make();s=read(out/'checkpoint.json');(out/next(a['path'] for a in s['artifacts'] if a['role']=='content')).unlink()
  with self.assertRaises((QualificationError,FileNotFoundError)):verify(out)
 def test_duplicate_record(self):
  out=self.make();p=out/'records.jsonl';atomic(p,p.read_bytes()+p.read_bytes().splitlines()[0]+b'\n')
  with self.assertRaisesRegex(QualificationError,'Duplicate'):verify(out)
 def test_corrupt_raw(self):
  out=self.make();s=read(out/'checkpoint.json');p=out/s['artifacts'][0]['path'];atomic(p,p.read_bytes()+b'X')
  with self.assertRaisesRegex(QualificationError,'corruption'):verify(out)
 def test_wrong_edition_even_with_rehashed_raw(self):
  out=self.make();s=read(out/'checkpoint.json');a=next(a for a in s['artifacts'] if a['role']=='content');raw=(out/a['path']).read_bytes().replace(b'fixture-1',b'fixture-2');atomic(out/a['path'],raw);a['sha256']=digest(raw);a['bytes']=len(raw);save(out/'checkpoint.json',s)
  with self.assertRaisesRegex(QualificationError,'drift'):verify(out)
 def test_missing_checkpoint_artifact(self):
  out=self.make();s=read(out/'checkpoint.json');s['artifacts']=[a for a in s['artifacts'] if a['requested_url']!='https://ecode360.com/102'];save(out/'checkpoint.json',s)
  try:r=verify(out);self.assertFalse(r['complete'])
  except QualificationError:pass
 def test_interruption_and_resume(self):
  full=self.make();out=self.root/'resumed';FakeBrowser.fail='https://ecode360.com/102'
  try:
   with patch('collectors.ecode.browser.Browser',FakeBrowser):r=collect(CFG,out)
   self.assertFalse(r['complete']);self.assertFalse(verify(out)['complete'])
  finally:FakeBrowser.fail=None
  with patch('collectors.ecode.browser.Browser',FakeBrowser):r=collect(CFG,out,True)
  self.assertTrue(r['complete'],r);self.assertTrue(verify(out)['complete'])
  # Artifact timestamps/transport chronology may differ. Stable legal rows must agree exactly.
  def stable(p):
   rs=[json.loads(x) for x in (p/'records.jsonl').read_text().splitlines()]
   for r in rs:r.pop('raw_witnesses',None)
   return rs
  self.assertEqual(stable(full),stable(out))
 def test_graphics_and_unknown_empty_types(self):
  from collectors.ecode.adapters import parse_ecode,identity,asset_refs
  graphic=ONE.replace(b'<p>Alpha legal text.</p>',b'<svg viewBox="0 0 10 10"><image href="https://example.invalid/map.png"/><use xlink:href="https://example.invalid/symbol.svg#x"/></svg><picture><source srcset="a.png 1x, b.png 2x"/><img src="map.png"/></picture><p style="background-image:url(bg.svg)"></p>')
  parsed=parse_ecode(graphic,'https://ecode360.com/101',identity(graphic,'https://ecode360.com/101','ecode360'));r=next(r for r in parsed['records'] if r['id']=='201');self.assertNotIn('<svg',r['content_html']);self.assertNotIn('<svg',r['semantic_html']);self.assertIn('[IMAGE]',r['text']);self.assertEqual(r['image_placeholder_count'],3);urls={a['url'] for a in r['assets']};self.assertIn('https://example.invalid/map.png',urls);self.assertIn('https://ecode360.com/b.png',urls);self.assertIn('https://ecode360.com/bg.svg',urls)
  empty=page('101','Chapter 1',title('201','Unknown node','mystery'),'<div id="childContent">'+title('201','Unknown node','mystery')+'<div class="content" id="201_content"></div></div>');parsed=parse_ecode(empty,'https://ecode360.com/101',identity(empty,'https://ecode360.com/101','ecode360'));self.assertEqual(next(d['classification'] for d in parsed['dispositions'] if d['id']=='201'),'unresolved_empty')
 def test_heading_only_and_unowned_visuals(self):
  from collectors.ecode.adapters import parse_ecode,identity
  h=page('101','Chapter 1',title('201','Section 1','section'),'<div id="childContent">'+title('201','Section 1','section')+'<div class="content" id="201_content"><h2>Heading only</h2></div></div>')
  parsed=parse_ecode(h,'https://ecode360.com/101',identity(h,'https://ecode360.com/101','ecode360'));self.assertEqual(next(d['classification'] for d in parsed['dispositions'] if d['id']=='201'),'unresolved_empty')
  for extra in ['<svg><path d="x"/></svg>','<img src="map.png"/>','<div class="notes">Unowned history.</div>']:
   bad=ROOT.replace(b'</div></body>',extra.encode()+b'</div></body>')
   with self.assertRaisesRegex(QualificationError,'Unowned'):parse_ecode(bad,BASE,identity(bad,BASE,'ecode360'))
 def test_background_and_standalone_source_images(self):
  from collectors.ecode.adapters import normalized_images,image_occurrences,asset_refs
  from bs4 import BeautifulSoup
  cases=[('<table><tr><td background="outer.png">Outer<table><tr><td style="background-image:url(inner.png)">Inner</td></tr></table></td></tr></table>',2),('<source src="data:image/png;base64,PIXEL_PAYLOAD"><object data="map.png"></object>',2),('<source src="DATA:IMAGE/PNG;base64,PIXEL_PAYLOAD"><object data="DATA:IMAGE/PNG;base64,PIXEL_PAYLOAD"></object>',2)]
  for html,count in cases:
   normalized=str(normalized_images(html));self.assertEqual(normalized.count('[IMAGE]'),count);self.assertEqual(len(image_occurrences(html,'x')),count);self.assertNotIn('background=',normalized);self.assertNotIn('url(',normalized);self.assertNotIn('PIXEL_PAYLOAD',normalized);self.assertNotIn('PIXEL_PAYLOAD',json.dumps(image_occurrences(html,'x')));self.assertTrue(all(not a['required'] for a in asset_refs(html,BASE,'x')))
 def test_typed_opaque_images_are_nonrequired_through_real_parser(self):
  from collectors.ecode.adapters import parse_ecode,identity
  for mime in ['image/png','IMAGE/PNG']:
   raw=ONE.replace(b'<p>Alpha legal text.</p>',('<object type="'+mime+'" data="https://example.invalid/opaque-image"></object><source src="DATA:IMAGE/PNG;base64,SENTINEL">').encode())
   parsed=parse_ecode(raw,'https://ecode360.com/101',identity(raw,'https://ecode360.com/101','ecode360'));r=next(r for r in parsed['records'] if r['id']=='201');self.assertEqual(r['image_placeholder_count'],2);self.assertTrue(all(a['image'] and not a['required'] for a in r['assets']));self.assertNotIn('SENTINEL',json.dumps(r))
 def test_image_only_no_fetch_and_nonimage_failure(self):
  original=dict(SOURCES)
  try:
   imagepage=page('101','Chapter 1',title('201','Section 1','section'),'<div id="childContent">'+title('201','Section 1','section')+'<div class="content" id="201_content"><img aria-hidden="true" src="https://never-request.invalid/map"/><svg aria-hidden="true"><path d="x"/></svg><picture><source srcset="data:image/png;base64,AA=="/><img src="data:image/png;base64,AA=="/></picture><p style="background-image:url(map.png)"></p></div></div>')
   SOURCES['https://ecode360.com/101']=imagepage
   out=self.root/'images'
   with patch('collectors.ecode.browser.Browser',FakeBrowser):r=collect(CFG,out)
   self.assertTrue(r['complete'],r);self.assertTrue(verify(out)['complete']);self.assertEqual(r['intentional_image_omissions'],4)
   rec=next(json.loads(x) for x in (out/'records.jsonl').read_text().splitlines() if json.loads(x)['id']=='201');self.assertEqual(rec['text'].count('[IMAGE]'),4);self.assertNotIn('data:image/',rec['content_html']);self.assertNotIn('<img',rec['content_html']);self.assertNotIn('<svg',rec['content_html'])
   SOURCES['https://ecode360.com/101']=ONE.replace(b'Alpha legal text.',b'Alpha legal text. <a href="https://never-request.invalid/required.pdf">Required PDF</a>')
   out=self.root/'missing-pdf'
   with patch('collectors.ecode.browser.Browser',FakeBrowser):r=collect(CFG,out)
   self.assertFalse(r['attachments_complete']);self.assertFalse(r['complete'])
  finally:SOURCES.clear();SOURCES.update(original)
 def test_wrong_requested_node(self):
  from collectors.ecode.adapters import parse_ecode,identity
  with self.assertRaisesRegex(QualificationError,'GUID mismatch'):parse_ecode(ONE,'https://ecode360.com/102',identity(ONE,'https://ecode360.com/101','ecode360'))
 def test_explicit_migration_only(self):
  full=self.make();state=read(full/'checkpoint.json');snap=full/'executed-source'/'adapters.py';atomic(snap,snap.read_bytes()+b'\n# Synthetic previous revision marker\n');state['code_fingerprint']['adapters.py']=digest(snap.read_bytes());save(full/'checkpoint.json',state)
  with self.assertRaisesRegex(QualificationError,'exact source version'):collect(CFG,full,True)
  with patch('collectors.ecode.browser.Browser',FakeBrowser):r=adopt(full,self.root/'migrated',CFG)
  self.assertTrue(r['complete'],r);self.assertTrue(verify(self.root/'migrated')['complete']);self.assertTrue((self.root/'migrated'/'migration-source-checkpoint.json').exists())
 def test_nonimage_head_and_image_head_no_get(self):
  original=dict(SOURCES);calls=[]
  class QualifiedBrowser(FakeBrowser):
   def fetch(self,url,method='GET'):
    calls.append((url,method))
    if url=='https://documents.invalid/download':
     return (b'' if method=='HEAD' else valid_pdf()),{'url':url,'requested_url':url,'status':200,'headers':{'content-type':'application/pdf'},'transport':'SYNTHETIC','method':method}
    if url=='https://documents.invalid/map':
     if method!='HEAD':raise AssertionError('Image GET forbidden')
     return b'',{'url':url,'requested_url':url,'status':200,'headers':{'content-type':'image/png'},'transport':'SYNTHETIC','method':method}
    return super().fetch(url)
   bootstrap=fetch
  try:
   SOURCES['https://ecode360.com/101']=ONE.replace(b'Alpha legal text.',b'Alpha legal text. <a href="https://documents.invalid/download">Download required document</a> <a href="https://documents.invalid/map">Map</a>')
   out=self.root/'head-qualified'
   with patch('collectors.ecode.browser.Browser',QualifiedBrowser):r=collect(CFG,out)
   self.assertTrue(r['complete'],r);self.assertTrue(verify(out)['complete']);self.assertIn(('https://documents.invalid/download','GET'),calls);self.assertIn(('https://documents.invalid/map','HEAD'),calls);self.assertNotIn(('https://documents.invalid/map','GET'),calls)
  finally:SOURCES.clear();SOURCES.update(original)
 def test_access_stop_readonly_replay(self):
  source=self.make();state=read(source/'checkpoint.json');state['errors']=[{'type':'AccessStop','message':'Synthetic429','access_stop':True}];save(source/'checkpoint.json',state)
  out=self.root/'readonly'
  with patch('collectors.ecode.browser.Browser',side_effect=AssertionError('Replay must not open browser')):r=adopt(source,out,CFG,True)
  self.assertFalse(r['complete']);self.assertEqual(r['acquisition_mode'],'retained_source_replay_only');self.assertFalse(verify(out)['complete'])
  with self.assertRaisesRegex(AccessStop,'read-only'):collect(CFG,out,True)
  with self.assertRaisesRegex(AccessStop,'access-stopped'):adopt(source,self.root/'forbidden',CFG)
 def test_hard_interruption_after_raw_before_inventory_commit(self):
  out=self.make();s=read(out/'checkpoint.json');s['artifacts']=[a for a in s['artifacts'] if a['role']!='root-end'];s['inventory_bound_artifacts']=3;prefix={**s,'artifacts':s['artifacts'][:3]};d=rebuild(out,prefix);s['inventory_sha256']=digest(canon(sorted(d['nodes'].values(),key=lambda n:n['id'])));save(out/'checkpoint.json',s)
  # The second chapter's durable raw exists after the committed processed prefix.
  # Resume must validate the prefix, replay the pending raw, and finish without losing it.
  with patch('collectors.ecode.browser.Browser',FakeBrowser):r=collect(CFG,out,True)
  self.assertTrue(r['complete'],r);self.assertTrue(verify(out)['complete']);self.assertEqual(r['owned_content_nodes'],3)
 def test_retry_after_and_visible_refusal_shared_stop(self):
  from collectors.ecode.browser import Browser
  for n,status,headers,raw in [('rate',429,{'retry-after':'120','content-type':'text/html'},b'<html><body>Refused</body></html>'),('busy',503,{'retry-after':'600','content-type':'text/html'},b'<html><body>Busy</body></html>'),('challenge',200,{'content-type':'text/html'},b'<html><head><title>Publisher</title></head><body><div class="cf-error-details">Refused</div></body></html>')]:
   b=Browser('ecode360',self.root,gate_dir=self.root/n)
   with self.assertRaises(AccessStop):b.check(raw,{'url':BASE,'status':status,'headers':headers})
   self.assertTrue((b.gate.root/'STOP.json').exists());self.assertFalse(read(b.gate.root/'STOP.json')['automatic_retry'])
   with self.assertRaises(AccessStop):b.gate.reserve(BASE)
 def test_nonimage_document_only_not_normalized_text_complete(self):
  from collectors.ecode.adapters import parse_ecode,identity
  raw=page('101','Chapter 1',title('201','Section 1','section'),'<div id="childContent">'+title('201','Section 1','section')+'<div class="section_content content" id="201_content"><object data="required.pdf" type="application/pdf">Download PDF</object></div></div>')
  parsed=parse_ecode(raw,'https://ecode360.com/101',identity(raw,'https://ecode360.com/101','ecode360'));self.assertEqual(next(d['classification'] for d in parsed['dispositions'] if d['id']=='201'),'unresolved_nontext_document');self.assertTrue(next(r for r in parsed['records'] if r['id']=='201')['assets'][0]['required'])
 def test_required_document_format_qualification(self):
  from collectors.ecode.media import qualify_asset
  import zipfile
  meta={'requested_url':'https://documents.invalid/a.pdf','headers':{'content-type':'application/pdf'}}
  self.assertEqual(qualify_asset(valid_pdf(),meta)['pages'],1)
  from pypdf import PdfWriter
  zero=io.BytesIO();PdfWriter().write(zero)
  for raw in [b'',zero.getvalue(),b'%PDF-1.7\n%%EOF',valid_pdf()[:-80],b'HTTP200 arbitrary bytes']:
   with self.assertRaises(QualificationError):qualify_asset(raw,meta)
  z=io.BytesIO()
  with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_STORED) as archive:archive.writestr('law.txt','unique-payload')
  zm={'requested_url':'https://documents.invalid/legal.zip','headers':{'content-type':'application/zip'}};self.assertTrue(qualify_asset(z.getvalue(),zm)['crc_checked'])
  corrupt=z.getvalue().replace(b'unique-payload',b'unique-payloae')
  with self.assertRaises(QualificationError):qualify_asset(corrupt,zm)
  with self.assertRaises(QualificationError):qualify_asset(b'unknown binary',{'requested_url':'https://documents.invalid/blob','headers':{'content-type':'application/octet-stream'}})
 def test_http200_empty_pdf_never_completes_or_retries(self):
  original=dict(SOURCES);calls=[]
  class EmptyPDFBrowser(FakeBrowser):
   def fetch(self,url,method='GET'):
    if url=='https://documents.invalid/empty.pdf':calls.append(method);return b'',{'url':url,'requested_url':url,'status':200,'headers':{'content-type':'application/pdf'},'method':method,'transport':'SYNTHETIC'}
    return super().fetch(url,method)
   bootstrap=fetch
  try:
   SOURCES['https://ecode360.com/101']=ONE.replace(b'Alpha legal text.',b'Alpha legal text. <a href="https://documents.invalid/empty.pdf">Required document</a>')
   out=self.root/'empty-pdf'
   with patch('collectors.ecode.browser.Browser',EmptyPDFBrowser):r=collect(CFG,out)
   self.assertFalse(r['complete']);self.assertFalse(r['attachments_complete']);self.assertEqual(r['acquired_assets'],0);self.assertTrue(r['asset_qualification_failures']);self.assertEqual(calls,['HEAD','GET']);self.assertFalse(verify(out)['complete'])
  finally:SOURCES.clear();SOURCES.update(original)
 def test_limit_never_complete(self):
  out=self.root/'limited'
  with patch('collectors.ecode.browser.Browser',FakeBrowser):r=collect({**CFG,'max_items':1},out)
  self.assertFalse(r['complete']);self.assertTrue(r['limits_applied']);self.assertFalse(verify(out)['complete'])
if __name__=='__main__':unittest.main()

MCBASE='https://synthetic.municipal.codes/Code'
def mcpage(title,main,currency=True):
 return ('<html><head><title>'+title+'</title></head><body><a class="product active" href="/Code">Code</a><div data-scope="Code" data-source="/Code/contents?interactive=true"></div><main>'+main+'</main>'+('<p>The Synthetic Municipal Code is current through Fixture 1.</p>' if currency else '')+'</body></html>').encode()
MCROOT=mcpage('Synthetic Municipal Code','<ul class="toc"><li><a href="/Code/1">Chapter 1</a></li></ul>')
MCTOC=mcpage('Contents of Synthetic Municipal Code','<ul class="contents-toc"><li><a href="/Code/1">Chapter 1</a><ul><li><a href="/Code/1-1">Section 1</a></li></ul></li></ul>',False)
MCONE=mcpage('Chapter 1','<article class="type-Chapter" id="1" data-history="/Code/1/history"><header><h2>Chapter 1</h2></header><p>Own chapter history.</p><article class="type-Section" id="1-1" data-history="/Code/1-1/history"><header><h3>Section 1</h3></header><p>Complete synthetic section.</p><table><tr><th colspan="2">Header</th></tr><tr><td>A</td><td>B</td></tr></table></article></article>')
class FakeMC(FakeBrowser):
 def fetch(self,url):return {MCBASE:MCROOT,MCBASE+'/contents':MCTOC,MCBASE+'/1':MCONE}[url],{'url':url,'requested_url':url,'status':200,'headers':{'content-type':'text/html'},'transport':'SYNTHETIC TEST ONLY','retrieved_at':'2099-01-01'}
 bootstrap=fetch
class MunicipalTests(unittest.TestCase):
 def test_complete_crawl_and_missing_descendant(self):
  with tempfile.TemporaryDirectory() as tmp:
   cfg={**CFG,'family':'municipal.codes','url':MCBASE,'publication':'Code','jurisdiction':'Synthetic','state':'ZZ'}
   out=Path(tmp)/'full'
   with patch('collectors.ecode.browser.Browser',FakeMC),patch('collectors.ecode.engine.enforce_published_advisory'):r=collect(cfg,out)
   self.assertTrue(r['complete'],r);self.assertTrue(verify(out)['complete']);self.assertEqual(r['inventory_nodes'],3);self.assertEqual(r['owned_content_nodes'],2)
   rows=(out/'records.jsonl').read_bytes().splitlines();atomic(out/'records.jsonl',rows[0]+b'\n')
   with self.assertRaisesRegex(QualificationError,'disagree'):verify(out)
