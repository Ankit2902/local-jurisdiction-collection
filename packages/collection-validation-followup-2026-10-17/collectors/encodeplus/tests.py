"""Network-free source-backed replay, fault injection and durable resume equivalence."""
import copy,json,pathlib,tempfile,unittest,os,io
from unittest.mock import patch
from . import collect as module
from .verify import verify
from .util import atomic_json,atomic_bytes,digest,read_json
from .model import inventory,parse_document
from .transport import scope_path,Stopped
HERE=pathlib.Path(__file__).parent
class Tests(unittest.TestCase):
 def fake(self,url,out,timeout=120):
  out=pathlib.Path(out)
  if 'doc-view.aspx?' in url:data=(HERE/'fixtures/amm-body.html').read_bytes();ctype='text/html'
  elif url.endswith('doc-view.aspx'):data=(HERE/'fixtures/amm-toc.html').read_bytes();ctype='text/html'
  elif '.pdf' in url:
   from pypdf import PdfWriter
   buf=io.BytesIO();writer=PdfWriter();writer.add_blank_page(width=72,height=72);writer.write(buf);data=buf.getvalue();ctype='application/pdf'
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
  self.assertEqual(next(r for r in parse_document(str(soup),'5',cfg,known) if r['id']=='6')['kind'],'source_empty_unresolved')
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
  def guarded(url,out,timeout=120):
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
  def fake(url,out,timeout=120):
   if 'doc-view.aspx?' in url:
    soup=BeautifulSoup((HERE/'fixtures/amm-body.html').read_text(),'html.parser');soup.select_one('section[data-secid="6"]').append(BeautifulSoup('<p>Official Map incorporated by reference <a href="'+image+'">Official Map</a></p>','html.parser'));data=str(soup).encode();meta={'url':url,'http_status':200,'headers':{'Content-Type':'text/html'},'sha256':digest(data),'bytes':len(data),'challenge':False};atomic_bytes(out,data);atomic_json(pathlib.Path(str(out)+'.receipt.json'),meta);return data,meta
   if url==image:
    data=b'';meta={'url':url,'http_status':200,'headers':{'Content-Type':'image/png'},'sha256':digest(data),'bytes':0,'challenge':False,'image_body_intentionally_skipped':True};atomic_bytes(out,data);atomic_json(pathlib.Path(str(out)+'.receipt.json'),meta);return data,meta
   return self.fake(url,out)
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'run'
   with patch.object(module,'fetch',fake):r=module.collect('lincoln-access-management',out)
   self.assertTrue(r['attachments_complete']);self.assertEqual(r['missing_assets'],[]);self.assertIn(image,r['image_skips']);self.assertIn('[IMAGE]',(out/'records.jsonl').read_text())
 def test_required_empty_truncated_pdf_and_rehashed_faults(self):
  from .documents import qualify_document
  for data in [b'',b'%PDF-truncated',b'%PDF-1.4\ninvalidxref\n%%EOF']:
   with self.assertRaises(ValueError):qualify_document(data,'https://example.gov/document.pdf','application/pdf')
   def broken(url,out,timeout=120):
    if '.pdf' not in url:return self.fake(url,out)
    meta={'url':url,'http_status':200,'headers':{'Content-Type':'application/pdf'},'sha256':digest(data),'bytes':len(data),'challenge':False};atomic_bytes(out,data);atomic_json(pathlib.Path(str(out)+'.receipt.json'),meta);return data,meta
   with tempfile.TemporaryDirectory() as td:
    out=pathlib.Path(td)/'collection'
    with patch.object(module,'fetch',broken):report=module.collect('lincoln-access-management',out)
    self.assertFalse(report['attachments_complete']);self.assertEqual(report['assets_acquired'],0);self.assertTrue(report['missing_assets'])
   with tempfile.TemporaryDirectory() as td:
    out=pathlib.Path(td)/'corruption';self.full(out);s=read_json(out/'checkpoint.json');url,a=next(iter(s['assets'].items()));p=out/a['path'];p.write_bytes(data);a['sha256']=digest(data);a.pop('document_integrity',None);m=read_json(p.with_name(p.name+'.receipt.json'));m['sha256']=a['sha256'];m['bytes']=len(data);atomic_json(p.with_name(p.name+'.receipt.json'),m);atomic_json(out/'checkpoint.json',s);self.assertFalse(verify(out)['attachments_complete'])
 def test_inline_word_joins_operative_heading_and_explicit_grouping(self):
  from .model import source_text
  from bs4 import BeautifulSoup
  cfg=module.TARGETS['lincoln-access-management']
  html='<div id="thePage" secid="1"><section data-secid="1" class="_001"><h1>Title 1. General</h1><section data-secid="2" class="_001-001"><h2><strong>Article III. Obedience </strong><strong>t</strong><strong>o </strong><strong>a</strong><strong>nd Effect </strong><strong>o</strong><strong>f Traffic Laws</strong></h2></section><section data-secid="3" class="_001-002"><h3><strong class="def">Refuse</strong><span> shall mean all garbage.</span></h3><p>Each <strong>own</strong><span>er</span> shall comply.<br/>Next line.</p><table><tr><td><b>trans</b><span>portation</span><p>Second line</p></td></tr></table></section></section></div>'
  known={'1':{'heading':'Title 1. General','has_children':True},'2':{'heading':'Article III. Obedience to and Effect of Traffic Laws','has_children':False}}
  records=parse_document(html,'1',cfg,known);group=next(r for r in records if r['id']=='2');definition=next(r for r in records if r['id']=='3')
  self.assertEqual(group['heading'],'Article III. Obedience to and Effect of Traffic Laws');self.assertEqual(group['kind'],'source_empty_unresolved');self.assertEqual(definition['heading'],'Refuse');self.assertTrue(definition['operative_heading_retained_as_body']);self.assertIn('Refuse shall mean all garbage.',definition['text']);self.assertIn('Each owner shall comply.',definition['text']);self.assertEqual(definition['tables'][0][0][0]['text'],'transportation Second line')
  self.assertEqual(source_text(BeautifulSoup('<p>Inline <b>word</b> and <i>more</i>.</p>','html.parser')),'Inline word and more.')
 def test_upgrade_lineage_and_corrupt_upgrade_rejection(self):
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'run';self.full(out,interrupt=1)
   original=module.code_hashes
   # Simulate a legitimate prior revision with a hash-verified captured file.
   state=read_json(out/'checkpoint.json');old=b'# retained earlier implementation\n';oldhash=digest(old);state['code_hashes']['model.py']=oldhash;atomic_bytes(out/'script-versions'/(oldhash+'.py'),old);atomic_json(out/'checkpoint.json',state)
   with patch.object(module,'fetch',self.fake):report=module.collect('lincoln-access-management',out,resume=True,upgrade_code=True)
   self.assertTrue(report['publication_text_complete']);self.assertTrue(read_json(out/'checkpoint.json')['code_upgrades']);self.assertTrue(list((out/'checkpoint-history').glob('*.json')))
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'run';self.full(out,interrupt=1);state=read_json(out/'checkpoint.json');state['code_hashes']['model.py']='0'*64;atomic_json(out/'checkpoint.json',state)
   with self.assertRaises(Exception):
    with patch.object(module,'fetch',self.fake):module.collect('lincoln-access-management',out,resume=True,upgrade_code=True)
 def test_observed_primary_definition_and_unresolved_leaves(self):
  cfg=module.TARGETS['lincoln'];definition=parse_document((HERE/'fixtures/lincoln-definition.html').read_text(),'12585',cfg,{})[0]
  self.assertEqual(definition['heading'],'Refuse');self.assertTrue(definition['operative_heading_retained_as_body']);self.assertIn('shall mean',definition['text']);self.assertGreater(len(definition['text']),100)
  for fixture,ident,target in [('lincoln-empty-map','13438','lincoln'),('overland-empty-article','3061','overland'),('savannah-empty-leaf','6451','savannah')]:
   records=parse_document((HERE/'fixtures'/(fixture+'.html')).read_text(),ident,module.TARGETS[target],{ident:{'has_children':False,'heading':'Observed leaf'}})
   self.assertEqual(records[0]['kind'],'source_empty_unresolved',fixture)
 def test_narrow_source_hidden_date_sort_keys(self):
  from bs4 import BeautifulSoup
  from .model import omit_equivalent_date_sort_keys
  records=parse_document((HERE/'fixtures/fairfax-hidden-date-sort-keys.html').read_text(),'3044',module.TARGETS['fairfax-zoning'],{})
  self.assertEqual(len(records[0]['omitted_hidden_sort_keys']),46);self.assertNotIn('2023/05/0905/09/2023',records[0]['text']);self.assertIn('2023/05/09',records[0]['html']);self.assertNotIn('display:none',records[0]['body_html'])
  doc=BeautifulSoup('<table><tr><td><span style="display:none">Legal hidden requirement</span>Visible rule</td><td><span style="display:none">2023/05/09</span>05/10/2023</td></tr></table>','html.parser');self.assertEqual(omit_equivalent_date_sort_keys(doc),[]);self.assertIn('Legal hidden requirement',str(doc));self.assertIn('2023/05/09',str(doc))
 def test_background_and_recursive_inline_image_metadata_redaction(self):
  from bs4 import BeautifulSoup
  from .model import replace_images,source_text
  payload='PIXELS_SENTINEL';doc=BeautifulSoup('<section style="background:url(root.png)"><table><tr><td background="outer.png">Outer<table><tr><td style="background:url(inner.png)">Inner</td></tr></table></td></tr></table><img src="ordinary.png" alt="data:image/png;base64,'+payload+'"><p title="data:image/png;base64,'+payload+'">Rule</p></section>','html.parser');root=doc.section;images=replace_images(root,'https://example.gov/');self.assertNotIn(payload,json.dumps({'html':str(root),'refs':images}));self.assertNotIn('background=',str(root));self.assertNotIn('url(',str(root));self.assertTrue(all('[IMAGE]' in source_text(c) for c in root.select('td')));self.assertTrue(any(r['inline_data_sha256'] or r.get('alt_inline_data_sha256') for r in images))
 def test_native_document_capture_resume_and_corruption(self):
  from . import native_document as native
  data=(HERE/'fixtures/overland-solid-waste-native.pdf').read_bytes();cfg=read_json(HERE/'configs/native-82-4b983dc51ab6.json')
  def fake(url,out,timeout=120):
   meta={'url':url,'http_status':200,'headers':{'Content-Type':'application/pdf'},'sha256':digest(data),'bytes':len(data),'challenge':False};atomic_bytes(out,data);atomic_json(pathlib.Path(str(out)+'.receipt.json'),meta);return data,meta
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'resumed';full=pathlib.Path(td)/'full'
   with patch.object(module,'fetch',fake):
    self.assertFalse(native.collect(cfg,out,interrupt_after_start=True)['native_document_complete']);r=native.collect(cfg,out,resume=True);self.assertTrue(r['native_document_complete']);self.assertFalse(r['publication_text_complete']);self.assertEqual(r['physical_pages'],6);native.collect(cfg,full)
   self.assertEqual((out/'records.jsonl').read_bytes(),(full/'records.jsonl').read_bytes());p=out/'records.jsonl';p.write_text(p.read_text()+p.read_text().splitlines()[0]+'\n');self.assertFalse(native.verify(out)['native_document_complete'])
   p=full/'raw/start.pdf';p.write_bytes(b'%PDF-truncated');state=read_json(full/'checkpoint.json');state['start']['sha256']=digest(p.read_bytes());m=read_json(pathlib.Path(str(p)+'.receipt.json'));m['sha256']=state['start']['sha256'];atomic_json(pathlib.Path(str(p)+'.receipt.json'),m);atomic_json(full/'checkpoint.json',state);self.assertFalse(native.verify(full)['native_document_complete'])
 def test_native_explicit_retry_preserves_failed_poll_attempt(self):
  pdf=(HERE/'fixtures/amm-full-export.pdf').read_bytes();failed=[False]
  def fake(url,out,timeout=120):
   status=200
   if 'doc-view.js' in url:data=b'var mURL = "export2doc.aspx?pdf=1&tocid=" + id';ctype='application/javascript'
   elif 'component.aspx' in url:
    if not failed[0]:failed[0]=True;data=b'';ctype='application/json';status=None
    else:data=b'{"Ready":true,"File":"test.pdf"}';ctype='application/json'
   elif '&file=' in url:data=pdf;ctype='application/pdf'
   else:data=b"<script>$.get('component.aspx?name=export2doc',function(){});</script>";ctype='text/html'
   m={'url':url,'http_status':status,'headers':{'Content-Type':ctype},'sha256':digest(data),'bytes':len(data),'challenge':False};atomic_bytes(out,data);atomic_json(pathlib.Path(str(out)+'.receipt.json'),m)
   if status is None:raise TimeoutError('Retained original export timeout')
   return data,m
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td);state={'config':module.TARGETS['lincoln-access-management']}
   with patch.object(module,'fetch',fake):
    with self.assertRaises(TimeoutError):module.native_export(out,state,(HERE/'fixtures/amm-body.html').read_text())
    r=module.native_export(out,state,(HERE/'fixtures/amm-body.html').read_text());self.assertEqual(r['status'],'downloaded');self.assertEqual(r['document_integrity']['pages'],17)
   self.assertTrue((out/'native/attempt-0/poll-0.json.receipt.json').exists());self.assertTrue((out/'native/attempt-1/publication.pdf').exists());self.assertEqual(read_json(out/'native/attempt-0/poll-0.json.receipt.json')['http_status'],None)
 def test_live_source_revision_drift_fails_closed(self):
  versions=module.code_hashes();changed=[False]
  def fake(url,out,timeout=120):
   result=self.fake(url,out,timeout);changed[0]=True;return result
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'run'
   with patch.object(module,'fetch',fake),patch.object(module,'code_hashes',lambda:versions if not changed[0] else versions|{'unexecuted_revision.py':'f'*64}):
    report=module.collect('lincoln-access-management',out)
   self.assertFalse(report['publication_text_complete']);self.assertEqual(read_json(out/'checkpoint.json')['phase'],'failed');self.assertTrue(any('source changed' in f['reason'] for f in read_json(out/'checkpoint.json')['failures']))
 def test_finished_collection_explicit_native_retry_keeps_failure_and_refreshes_end(self):
  pdf=(HERE/'fixtures/amm-full-export.pdf').read_bytes();failed=[False];calls=[]
  def fake(url,out,timeout=120):
   calls.append(str(out));status=200
   if 'doc-view.js' in url:data=b'var mURL = "export2doc.aspx?pdf=1&tocid=" + id';ctype='application/javascript'
   elif 'component.aspx' in url:
    if not failed[0]:failed[0]=True;data=b'';ctype='application/json';status=None
    else:data=b'{"Ready":true,"File":"test.pdf"}';ctype='application/json'
   elif '&file=' in url:data=pdf;ctype='application/pdf'
   elif 'export2doc.aspx' in url:data=b"<script>$.get('component.aspx?name=export2doc',function(){});</script>";ctype='text/html'
   else:return self.fake(url,out,timeout)
   meta={'url':url,'http_status':status,'headers':{'Content-Type':ctype},'sha256':digest(data),'bytes':len(data),'challenge':False};atomic_bytes(out,data);atomic_json(pathlib.Path(str(out)+'.receipt.json'),meta)
   if status is None:raise TimeoutError('Retained original native timeout')
   return data,meta
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'run'
   with self.assertRaisesRegex(AssertionError,'requires --resume'):module.collect('lincoln-access-management',out,want_native=True,retry_native=True)
   with patch.object(module,'fetch',fake):first=module.collect('lincoln-access-management',out,want_native=True)
   self.assertTrue(first['publication_text_complete']);self.assertFalse(first['native_export_complete']);self.assertEqual(read_json(out/'checkpoint.json')['phase'],'finished');failed_receipt=out/'native/attempt-0/poll-0.json.receipt.json';before=failed_receipt.read_bytes()
   with patch.object(module,'fetch') as fetch:module.collect('lincoln-access-management',out,resume=True,want_native=True);fetch.assert_not_called()
   with patch.object(module,'fetch',fake):second=module.collect('lincoln-access-management',out,resume=True,want_native=True,retry_native=True)
   self.assertTrue(second['native_export_complete']);self.assertEqual(failed_receipt.read_bytes(),before);state=read_json(out/'checkpoint.json');self.assertEqual(state['generation'],1);self.assertTrue(state['end_blocks'][0]['path'].startswith('end-1/'));self.assertEqual(state['native_export_retries'][0]['prior_native_export']['status'],'failed');self.assertTrue((out/'native/attempt-1/publication.pdf').is_file())
   history=out/'native-retry-history'/(state['native_export_retries'][0]['prior_checkpoint_sha256']+'.json');history.write_bytes(b'corrupt native retry lineage');self.assertFalse(verify(out)['publication_text_complete'])
 def test_retained_paths_cannot_escape_relocated_package(self):
  from .util import validate_file
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);out=root/'evidence';out.mkdir();external=root/'outside.bin';external.write_bytes(b'known outside fixture');h=digest(external.read_bytes())
   for path in [str(external),'../outside.bin']:
    with self.assertRaisesRegex(ValueError,'relative inside'):validate_file(out,path,h)
   (out/'escape.bin').symlink_to(external)
   with self.assertRaisesRegex(ValueError,'escapes evidence'):validate_file(out,'escape.bin',h)
 def test_transient_resume_uses_new_immutable_attempt_and_refusals_never_retry(self):
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td);url='https://online.encodeplus.com/regs/test/doc-view.aspx?secid=1';p=out/'raw/node-1.html';meta={'url':url,'http_status':None,'headers':{},'sha256':digest(b''),'bytes':0,'challenge':False,'error':'Timeout'};atomic_bytes(p,b'');atomic_json(pathlib.Path(str(p)+'.receipt.json'),meta);original=pathlib.Path(str(p)+'.receipt.json').read_bytes()
   with patch.object(module,'fetch',self.fake):data,m=module.cached(out,url,'raw/node-1.html')
   self.assertEqual(m['_retained_path'],'raw/node-1.attempt-1.html');self.assertEqual(p.read_bytes(),b'');self.assertEqual(pathlib.Path(str(p)+'.receipt.json').read_bytes(),original);self.assertTrue(data)
   meta['blocked_by_stop']=True;meta['preexisting_stop']={'status':403};atomic_json(pathlib.Path(str(p)+'.receipt.json'),meta)
   with patch.object(module,'fetch') as fetch:
    with self.assertRaises(AssertionError):module.cached(out,url,'raw/node-1.html')
    fetch.assert_not_called()
 def test_case_insensitive_429_and_redirect_cycle_retained_without_repeated_request(self):
  from .transport import fetch,TRANSPORT_SHA256
  from urllib.error import HTTPError
  from unittest.mock import MagicMock
  url='https://online.encodeplus.com/regs/test/x'
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);opener=MagicMock();opener.open.side_effect=HTTPError(url,429,'Rate limit',{'retry-after':'1000'},io.BytesIO(b'Rate limit'))
   with patch.dict(os.environ,{'ENCODEPLUS_GATE_DIR':str(root/'gate')}),patch('urllib.request.build_opener',return_value=opener),patch('time.sleep'):
    with self.assertRaises(Stopped):fetch(url,root/'429.bin')
    with self.assertRaises(Stopped):fetch(url,root/'cooldown.bin')
   self.assertEqual(opener.open.call_count,1);self.assertGreater(read_json(root/'gate/state.json')['cooldown_until']-__import__('time').time(),990);self.assertFalse(read_json(root/'cooldown.bin.receipt.json')['request_attempted']);self.assertEqual(read_json(root/'429.bin.receipt.json')['transport_sha256'],TRANSPORT_SHA256)
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);opener=MagicMock();opener.open.side_effect=[HTTPError(url,302,'Redirect',{'Location':'/regs/test/y'},io.BytesIO(b'First redirect')),HTTPError('https://online.encodeplus.com/regs/test/y',302,'Redirect',{'location':'/regs/test/x'},io.BytesIO(b'Second redirect'))]
   with patch.dict(os.environ,{'ENCODEPLUS_GATE_DIR':str(root/'gate')}),patch('urllib.request.build_opener',return_value=opener),patch('time.sleep'):
    with self.assertRaises(Stopped):fetch(url,root/'cycle.bin')
   self.assertEqual(opener.open.call_count,2);m=read_json(root/'cycle.bin.receipt.json');self.assertTrue(m['redirect_failure']);self.assertEqual(len(m['redirects']),2);self.assertEqual(m['redirects'][0]['headers']['Location'],'/regs/test/y')
 def test_explicit_limit_never_full(self):
  with tempfile.TemporaryDirectory() as td:
   with patch.object(module,'fetch',self.fake):r=module.collect('lincoln-access-management',pathlib.Path(td)/'run',max_items=1)
   self.assertFalse(r['publication_text_complete']);self.assertIn('Explicit max-items forces incomplete',r['errors'])
 def test_case_insensitive_image_mime_and_data_uri_policy(self):
  from bs4 import BeautifulSoup
  cfg=module.TARGETS['lincoln-access-management'];inv=inventory((HERE/'fixtures/amm-toc.html').read_text(),cfg);known={n['id']:n for n in inv['nodes']}
  soup=BeautifulSoup((HERE/'fixtures/amm-body.html').read_text(),'html.parser');body=soup.select_one('section[data-secid="6"]')
  body.append(BeautifulSoup('<object type="IMAGE/PNG" data="https://example.invalid/opaque-image"></object><source src="DATA:IMAGE/PNG;base64,PIXELS_SENTINEL">','html.parser'))
  record=next(r for r in parse_document(str(soup),'5',cfg,known) if r['id']=='6')
  self.assertEqual(record['text'].count('[IMAGE]'),2);self.assertNotIn('PIXELS_SENTINEL',json.dumps(record));self.assertNotIn('opaque-image',record['body_html']);self.assertFalse(record['assets']);self.assertEqual(len(record['image_refs']),2)
 def test_completion_gate_survives_write_jitter_network_errors_and_host_scopes(self):
  from . import transport
  from unittest.mock import MagicMock
  clock=[1000.0];starts=[];completions=[];real_atomic=transport.atomic_json
  def atomic_jitter(path,value):
   real_atomic(path,value);clock[0]+=0.6
  def sleep(delay):clock[0]+=delay
  class Response:
   status=200;headers={'Content-Type':'text/plain'}
   def read(self):clock[0]+=0.8;return b'Native source bytes'
   def close(self):clock[0]+=0.2;completions.append(clock[0])
  def open_request(req,timeout=120):
   starts.append(clock[0]);clock[0]+=0.3
   if len(starts)==2:
    completions.append(clock[0]);raise TimeoutError('Source connection timed out')
   return Response()
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);gate=root/'gate';gate.mkdir();atomic_json(gate/'state.json',{'cooldown_until':999.0,'retained_history':'unchanged'});blocked='https://stopped.example.invalid/a.pdf';atomic_json(scope_path(gate,blocked),{'stopped':True,'stop_reason':{'status':403,'url':blocked}});blocked_before=scope_path(gate,blocked).read_bytes();opener=MagicMock();opener.open.side_effect=open_request
   with patch.dict(os.environ,{'ENCODEPLUS_GATE_DIR':str(gate)}),patch.object(transport.time,'time',side_effect=lambda:clock[0]),patch.object(transport.time,'sleep',side_effect=sleep),patch.object(transport,'atomic_json',side_effect=atomic_jitter),patch('urllib.request.build_opener',return_value=opener):
    transport.fetch('https://online.encodeplus.com/first',root/'first.bin')
    with self.assertRaises(Stopped):transport.fetch('https://external.example.invalid/timed-out.pdf',root/'error.bin')
    transport.fetch('https://codes.opkansas.org/third',root/'third.bin')
    with self.assertRaises(Stopped):transport.fetch(blocked,root/'blocked.bin')
   self.assertEqual(len(starts),3);self.assertGreaterEqual(starts[1]-completions[0],transport.REQUEST_GAP_SECONDS);self.assertGreaterEqual(starts[2]-completions[1],transport.REQUEST_GAP_SECONDS);state=read_json(gate/'state.json');self.assertGreaterEqual(state['last_completed'],completions[2]);self.assertEqual(state['cooldown_until'],999.0);self.assertEqual(state['retained_history'],'unchanged');self.assertEqual(scope_path(gate,blocked).read_bytes(),blocked_before);self.assertFalse(read_json(root/'blocked.bin.receipt.json')['request_attempted']);self.assertIsNone(read_json(root/'error.bin.receipt.json')['http_status'])
 def test_refusal_body_read_error_preserves_stop_and_completion(self):
  from . import transport
  from urllib.error import HTTPError
  from unittest.mock import MagicMock
  class BrokenBody(io.BytesIO):
   def read(self,*args):raise TimeoutError('Refusal body timed out')
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);url='https://online.encodeplus.com/refused';opener=MagicMock();opener.open.side_effect=HTTPError(url,403,'Forbidden',{'Content-Type':'text/plain'},BrokenBody())
   with patch.dict(os.environ,{'ENCODEPLUS_GATE_DIR':str(root/'gate')}),patch('urllib.request.build_opener',return_value=opener):
    with self.assertRaises(Stopped):transport.fetch(url,root/'refused.bin')
    with self.assertRaises(Stopped):transport.fetch(url,root/'blocked.bin')
   state=read_json(root/'gate/state.json');receipt=read_json(root/'refused.bin.receipt.json');self.assertTrue(state['stopped']);self.assertIn('last_completed',state);self.assertEqual(receipt['http_status'],403);self.assertTrue(receipt['challenge']);self.assertIn('response read failed',receipt['error']);self.assertEqual(opener.open.call_count,1);self.assertFalse(read_json(root/'blocked.bin.receipt.json')['request_attempted'])
 def test_native_explicit_upgrade_revalidates_raw_and_refreshes_closing(self):
  from . import native_document as native
  import shutil
  data=(HERE/'fixtures/overland-solid-waste-native.pdf').read_bytes();cfg=read_json(HERE/'configs/native-82-4b983dc51ab6.json');requests=[]
  def fake(url,out,timeout=120):
   requests.append(str(out));meta={'url':url,'http_status':200,'headers':{'Content-Type':'application/pdf'},'sha256':digest(data),'bytes':len(data),'challenge':False};atomic_bytes(out,data);atomic_json(pathlib.Path(str(out)+'.receipt.json'),meta);return data,meta
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'native';bad=pathlib.Path(td)/'corrupt'
   with patch.object(module,'fetch',fake):native.collect(cfg,out,interrupt_after_start=True)
   state=read_json(out/'checkpoint.json');prior_script=b'Synthetic preceding native parser revision fixture';prior_sha=digest(prior_script);atomic_bytes(out/'script-versions'/(prior_sha+'.py'),prior_script);state['code_hashes']['native_document.py']=prior_sha;atomic_json(out/'checkpoint.json',state);prior=(out/'checkpoint.json').read_bytes();start=(out/'raw/start.pdf').read_bytes();shutil.copytree(out,bad);(bad/'raw/start.pdf').write_bytes(b'corrupt')
   with self.assertRaisesRegex(AssertionError,'explicit --upgrade-code'):native.collect(cfg,out,resume=True)
   with patch.object(module,'fetch',fake):report=native.collect(cfg,out,resume=True,upgrade_code=True)
   self.assertTrue(report['native_document_complete']);upgraded=read_json(out/'checkpoint.json');self.assertEqual(upgraded['end']['path'],'raw/end-1.pdf');history=out/'checkpoint-history'/(digest(prior)+'.json');self.assertEqual(history.read_bytes(),prior);self.assertEqual((out/'raw/start.pdf').read_bytes(),start);self.assertEqual(upgraded['code_upgrades'][0]['prior_code_hashes']['native_document.py'],prior_sha);self.assertEqual(len(requests),2);history.write_bytes(b'corrupt upgrade lineage');self.assertFalse(native.verify(out)['native_document_complete'])
   with patch.object(module,'fetch') as fetch:
    with self.assertRaises(ValueError):native.collect(cfg,bad,resume=True,upgrade_code=True)
    fetch.assert_not_called()
 def test_public_open_encrypted_integrity_and_actual_password_refusal(self):
  from .documents import qualify_document
  from pypdf import PdfWriter
  data=(HERE/'fixtures/public-open-pfm-sheet.pdf').read_bytes();before=digest(data);q=qualify_document(data,'https://example.gov/public.pdf','application/pdf');self.assertEqual(q['pages'],1);self.assertTrue(q['public_open_encryption']['encrypted']);self.assertFalse(q['public_open_encryption']['credentials_supplied']);self.assertEqual(q['public_open_encryption']['independent_page_count'],1);self.assertEqual(digest(data),before);self.assertEqual(digest((HERE/'fixtures/public-open-pfm-sheet.pdf').read_bytes()),before)
  writer=PdfWriter();writer.add_blank_page(width=72,height=72);writer.encrypt(user_password='known-synthetic-user-password',owner_password='known-synthetic-owner-password',algorithm='AES-128');stream=io.BytesIO();writer.write(stream)
  with self.assertRaisesRegex(ValueError,'unqualified'):qualify_document(stream.getvalue(),'https://example.gov/password-required.pdf','application/pdf')
 def test_public_open_encrypted_corruption_and_dependency_fail_closed(self):
  from .documents import qualify_document
  data=(HERE/'fixtures/public-open-pfm-sheet.pdf').read_bytes()
  for bad in [b'',data[:1000],data[:-2000]]:
   with self.assertRaises(ValueError):qualify_document(bad,'https://example.gov/public.pdf','application/pdf')
  with patch.dict('sys.modules',{'pypdfium2':None}):
   with self.assertRaisesRegex(ValueError,'unqualified'):qualify_document(data,'https://example.gov/public.pdf','application/pdf')
 def test_exact_authority_relation_source_witness_and_unknown_required(self):
  cfg={'base':'https://online.encodeplus.com/regs/fairfaxcounty-va-pfm/'};board='https://www.fairfaxcounty.gov/boardofsupervisors/';raw=(HERE/'fixtures/pfm-node-9-source.html').read_text();row=parse_document(raw,'9',cfg,{})[0];self.assertNotIn(board,[x['url'] for x in row['assets']]);self.assertTrue(row['qualified_reference_dispositions']);ledger=row['qualified_reference_dispositions'][0];self.assertEqual(ledger['type'],'qualified_authority_cross_reference');self.assertEqual(ledger['source_context_sha256'],digest(ledger['source_context'].encode()));self.assertIn('9',ledger['source_witness']['source_node_ids']);self.assertEqual(ledger['source_witness']['raw_sha256'],'185128e4c386d243433dc9150fbe6542d2c057f40b1f466cc4e08723cf7605b0');self.assertIn('Board',row['text'])
  # A genuinely described adopted soils map remains unresolved at its advertised location.
  soil=parse_document((HERE/'fixtures/pfm-node-544-source.html').read_text(),'544',cfg,{})[0];self.assertIn('https://www.fairfaxcounty.gov/',[x['url'] for x in soil['assets']]);self.assertNotIn(board,[x['url'] for x in soil['assets']])
  changed=raw.replace('1975','1974');unknown=parse_document(changed,'9',cfg,{})[0];self.assertIn(board,[x['url'] for x in unknown['assets']]);other=parse_document(raw,'9',{'base':'https://online.encodeplus.com/regs/other-publication/'},{})[0];self.assertIn(board,[x['url'] for x in other['assets']])
  pdf=raw.replace('href="https://www.fairfaxcounty.gov/boardofsupervisors/"','href="https://example.gov/adopted-map.pdf"');direct=parse_document(pdf,'9',cfg,{})[0];self.assertIn('https://example.gov/adopted-map.pdf',[x['url'] for x in direct['assets']])
if __name__=='__main__':unittest.main(verbosity=2)
