"""Network-free source-backed replay, fault injection and durable resume equivalence."""
import copy,json,pathlib,tempfile,unittest,os
from unittest.mock import patch
from . import collect as module
from .verify import verify
from .util import atomic_json,atomic_bytes,digest,read_json
from .model import inventory,parse_document
from .transport import scope_path,Stopped
HERE=pathlib.Path(__file__).parent
class Tests(unittest.TestCase):
 def fake(self,url,out):
  out=pathlib.Path(out)
  if 'doc-view.aspx?' in url:data=(HERE/'fixtures/amm-body.html').read_bytes();ctype='text/html'
  elif url.endswith('doc-view.aspx'):data=(HERE/'fixtures/amm-toc.html').read_bytes();ctype='text/html'
  elif '.pdf' in url:data=b'%PDF-1.4\nsynthetic asset transport fixture only';ctype='application/pdf'
  else:data=b'\xff\xd8\xff\xd9';ctype='image/jpeg'
  meta={'url':url,'http_status':200,'headers':{'Content-Type':ctype},'sha256':digest(data),'bytes':len(data),'challenge':False};atomic_bytes(out,data);atomic_json(out.with_name(out.name+'.receipt.json'),meta);return data,meta
 def full(self,out,interrupt=None,resume=False):
  with patch.object(module,'fetch',self.fake):return module.collect('lincoln-access-management',out,resume=resume,interrupt_after=interrupt)
 def test_dynamic_real_source_and_full_replay(self):
  cfg=module.TARGETS['lincoln-access-management'];inv=inventory((HERE/'fixtures/amm-toc.html').read_text(),cfg);known={n['id']:n for n in inv['nodes']};records=parse_document((HERE/'fixtures/amm-body.html').read_text(),'5',cfg,known)
  self.assertEqual(len(records),14);self.assertEqual(sum(len(r['tables']) for r in records),6);self.assertEqual([r['id'] for r in records if r['image_only']],['18']);self.assertTrue(all('section[data-secid]' not in r['body_html'] for r in records));self.assertEqual(next(r for r in records if r['id']=='18')['heading'],'Access Management Categories Map');self.assertEqual(next(r for r in records if r['id']=='18')['parent_id'],'5')
  with tempfile.TemporaryDirectory() as td:
   r=self.full(pathlib.Path(td)/'run');self.assertTrue(r['publication_text_complete']);self.assertTrue(r['attachments_complete']);self.assertEqual(r['missing_ids'],[])
 def test_interruption_resume_equivalence(self):
  with tempfile.TemporaryDirectory() as td:
   a=pathlib.Path(td)/'uninterrupted';b=pathlib.Path(td)/'resumed';self.full(a);r=self.full(b,interrupt=1);self.assertFalse(r['publication_text_complete']);self.assertFalse(verify(b)['publication_text_complete']);r=self.full(b,resume=True);self.assertTrue(r['publication_text_complete']);self.assertEqual((a/'records.jsonl').read_bytes(),(b/'records.jsonl').read_bytes());self.assertEqual((a/'records.csv').read_bytes(),(b/'records.csv').read_bytes())
 def test_missing_duplicate_corrupt_wrongedition_and_interruption_fail_closed(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);base=root/'base';self.full(base)
   import shutil
   for fault in ['missing','duplicate','corrupt','wrongedition','end-drift','interrupted','missing-asset','wrong-base']:
    out=root/fault;shutil.copytree(base,out)
    if fault=='missing':p=out/'records.jsonl';p.write_text('\n'.join(p.read_text().splitlines()[1:])+'\n')
    elif fault=='duplicate':p=out/'records.jsonl';p.write_text(p.read_text()+p.read_text().splitlines()[0]+'\n')
    elif fault=='corrupt':(out/'raw/node-5.html').write_text('corrupt')
    elif fault=='wrongedition':s=read_json(out/'checkpoint.json');s['config']['identity']='Different edition/publication';atomic_json(out/'checkpoint.json',s)
    elif fault=='end-drift':
     s=read_json(out/'checkpoint.json');e=s['end_blocks'][0];p=out/e['path'];data=p.read_bytes().replace(b'Access Management Categories Map',b'Changed edition map');p.write_bytes(data);e['sha256']=digest(data);m=read_json(p.with_name(p.name+'.receipt.json'));m['sha256']=e['sha256'];atomic_json(p.with_name(p.name+'.receipt.json'),m);atomic_json(out/'checkpoint.json',s)
    elif fault=='wrong-base':
     s=read_json(out/'checkpoint.json');b=s['blocks'][0];b['url']='https://online.encodeplus.com/regs/different-publication/doc-view.aspx?secid='+b['requested']+'&ajax=0';p=out/(b['path']+'.receipt.json');m=read_json(p);m['url']=b['url'];atomic_json(p,m);atomic_json(out/'checkpoint.json',s)
    elif fault=='interrupted':s=read_json(out/'checkpoint.json');s['phase']='interrupted';atomic_json(out/'checkpoint.json',s)
    else:s=read_json(out/'checkpoint.json');(out/next(iter(s['assets'].values()))['path']).unlink()
    report=verify(out);self.assertFalse(report['publication_text_complete'] and report['attachments_complete'],(fault,report))
 def test_corrupt_resume_cache_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'run';self.full(out,interrupt=1);(out/'raw/node-5.html').write_text('corrupt')
   with self.assertRaises(Exception):self.full(out,resume=True)
 def test_host_scoped_stops_and_no_network(self):
  from .transport import fetch
  with tempfile.TemporaryDirectory() as td:
   gate=pathlib.Path(td);external='http://www.syracuse.ny.us/x.pdf';publisher='https://online.encodeplus.com/x';self.assertNotEqual(scope_path(gate,external),scope_path(gate,publisher));self.assertEqual(scope_path(gate,publisher),scope_path(gate,'https://codes.opkansas.org/x'))
   atomic_json(scope_path(gate,external),{'stopped':True,'stop_reason':'Retained external refusal'})
   with patch.dict(os.environ,{'ENCODEPLUS_GATE_DIR':td}),patch('urllib.request.build_opener') as opener:
    with self.assertRaises(Stopped):fetch(external,gate/'bad.bin')
    opener.assert_not_called()
   self.assertFalse((gate/'state.json').exists(),'External stop must not become publisher stop')
 def test_empty_leaf_unowned_text_and_svg_asset_guards(self):
  from bs4 import BeautifulSoup
  from .model import refs
  cfg=module.TARGETS['lincoln-access-management'];inv=inventory((HERE/'fixtures/amm-toc.html').read_text(),cfg);known={n['id']:n for n in inv['nodes']};html=(HERE/'fixtures/amm-body.html').read_text()
  soup=BeautifulSoup(html,'html.parser');leaf=soup.select_one('section[data-secid="6"]')
  for child in list(leaf.children):
   if getattr(child,'name',None)!='h2':child.extract()
  with self.assertRaisesRegex(ValueError,'Unexplained empty'):parse_document(str(soup),'5',cfg,known)
  soup=BeautifulSoup(html,'html.parser');soup.select_one('#thePage').append(BeautifulSoup('<p>Unowned substantive legal provision</p>','html.parser'))
  with self.assertRaisesRegex(AssertionError,'Unowned'):parse_document(str(soup),'5',cfg,known)
  svg=BeautifulSoup('<svg><image href="map.svg"/><image xlink:href="other.png"/><use href="#local"/></svg><img srcset="a.png 1x, b.png 2x"/>','html.parser');from .model import replace_images;images=replace_images(svg,cfg['base']);urls={r['url'] for r in refs(svg,cfg['base'])};self.assertEqual(urls,set());self.assertIn('[IMAGE]',svg.get_text());self.assertTrue(images)
 def test_real_full_native_and_toc_only_negative(self):
  from pypdf import PdfReader
  cfg=module.TARGETS['lincoln-access-management'];inv=inventory((HERE/'fixtures/amm-toc.html').read_text(),cfg);known={n['id']:n for n in inv['nodes']};records=parse_document((HERE/'fixtures/amm-body.html').read_text(),'5',cfg,known);norm=lambda v:''.join(c.casefold() for c in v if c.isalnum())
  full=PdfReader(HERE/'fixtures/amm-full-export.pdf');toc=PdfReader(HERE/'fixtures/amm-toc-only-export.pdf');self.assertEqual(len(full.pages),17);self.assertEqual(len(toc.pages),1);text=norm(' '.join(p.extract_text() for p in full.pages));toc_text=norm(' '.join(p.extract_text() for p in toc.pages));self.assertEqual(full.metadata.title,cfg['identity']);cells=[c['text'] for r in records for t in r['tables'] for row in t for c in row if norm(c['text'])];self.assertEqual(len(cells),149);self.assertTrue(all(norm(c) in text for c in cells))
  for r in records:
   if r['text'].replace('[IMAGE]','').strip():
    anchor=norm(' '.join(r['text'].replace('[IMAGE]','').split()[:12]));self.assertIn(anchor,text)
  anchor=norm('Access management balances the need to provide access to individual properties');self.assertNotIn(anchor,toc_text);self.assertIn(anchor,text)
 def test_image_policy_and_incorporated_extensionless_document(self):
  from bs4 import BeautifulSoup
  from .model import replace_images,refs
  cfg=module.TARGETS['lincoln-access-management'];doc=BeautifulSoup('<p>Official Map is incorporated by reference <a href="https://example.gov/document/123">Map</a></p><picture><source srcset="a.jpg 1x"/><img src="b.png"/></picture><svg><image xlink:href="c.jpg"/></svg><p style="background-image:url(d.png)">Map</p>','html.parser');images=replace_images(doc,cfg['base']);assets=refs(doc,cfg['base']);self.assertEqual([x['url'] for x in assets],['https://example.gov/document/123']);self.assertGreaterEqual(doc.get_text().count('[IMAGE]'),3);self.assertTrue(images)
  calls=[]
  def guarded(url,out):
   calls.append(url);self.assertFalse(any(url.lower().split('?')[0].endswith(x) for x in ['.jpg','.jpeg','.png','.svg']),'Image network request forbidden');return self.fake(url,out)
  with tempfile.TemporaryDirectory() as td:
   with patch.object(module,'fetch',guarded):r=module.collect('lincoln-access-management',pathlib.Path(td)/'run')
   self.assertTrue(r['publication_text_complete']);self.assertEqual(r['image_only_nodes'],['18']);self.assertGreater(r['image_placeholders'],0);self.assertEqual(r['asset_references'],1)
 def test_image_response_headers_never_read_body_and_css_poster_are_inert(self):
  from .transport import fetch
  from unittest.mock import MagicMock
  from bs4 import BeautifulSoup
  from .model import replace_images
  doc=BeautifulSoup('<style>.x {background:url(map.svg)}</style><video poster="cover.jpg"></video><object data="data:image/svg+xml,INLINE"></object>','html.parser');refs=replace_images(doc,'https://example.gov/');self.assertEqual(len(doc.select('[poster]')),0);self.assertNotIn('url(',str(doc));self.assertNotIn('data:image',str(doc));self.assertGreaterEqual(doc.get_text().count('[IMAGE]'),3)
  with tempfile.TemporaryDirectory() as td:
   response=MagicMock();response.status=200;response.headers={'Content-Type':'image/png'};response.read.side_effect=AssertionError('Image body must remain unread');opener=MagicMock();opener.open.return_value=response
   with patch.dict(os.environ,{'ENCODEPLUS_GATE_DIR':td}),patch('urllib.request.build_opener',return_value=opener):data,meta=fetch('https://example.gov/document/123',pathlib.Path(td)/'headers-only.bin')
   response.read.assert_not_called();self.assertEqual(data,b'');self.assertTrue(meta['image_body_intentionally_skipped'])
 def test_extensionless_image_is_placeholder_not_missing_asset(self):
  from bs4 import BeautifulSoup
  image='https://example.gov/document/map123'
  def fake(url,out):
   if 'doc-view.aspx?' in url:
    soup=BeautifulSoup((HERE/'fixtures/amm-body.html').read_text(),'html.parser');soup.select_one('section[data-secid="6"]').append(BeautifulSoup('<p>Official Map incorporated by reference <a href="'+image+'">Official Map</a></p>','html.parser'));data=str(soup).encode();meta={'url':url,'http_status':200,'headers':{'Content-Type':'text/html'},'sha256':digest(data),'bytes':len(data),'challenge':False};atomic_bytes(out,data);atomic_json(pathlib.Path(str(out)+'.receipt.json'),meta);return data,meta
   if url==image:
    data=b'';meta={'url':url,'http_status':200,'headers':{'Content-Type':'image/png'},'sha256':digest(data),'bytes':0,'challenge':False,'image_body_intentionally_skipped':True};atomic_bytes(out,data);atomic_json(pathlib.Path(str(out)+'.receipt.json'),meta);return data,meta
   return self.fake(url,out)
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'run'
   with patch.object(module,'fetch',fake):r=module.collect('lincoln-access-management',out)
   self.assertTrue(r['attachments_complete']);self.assertEqual(r['missing_assets'],[]);self.assertIn(image,r['image_skips']);self.assertIn('[IMAGE]',(out/'records.jsonl').read_text())
 def test_explicit_limit_never_full(self):
  with tempfile.TemporaryDirectory() as td:
   with patch.object(module,'fetch',self.fake):r=module.collect('lincoln-access-management',pathlib.Path(td)/'run',max_items=1)
   self.assertFalse(r['publication_text_complete']);self.assertIn('Explicit max-items forces incomplete',r['errors'])
if __name__=='__main__':unittest.main(verbosity=2)
