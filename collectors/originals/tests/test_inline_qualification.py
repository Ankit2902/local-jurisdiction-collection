"""Concrete inline payload/context regressions: no image or inline-document decoding."""
import base64,io,json,sys,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bs4 import BeautifulSoup
from pypdf import PdfWriter
from source_common import load,save,sha
from model import semantics
import king_normalize as king,flagstaff_html_normalize as flag
from flagstaff_root import root_inventory,ROOT_TOC_URL
from flagstaff_html import URL,inventory,CURRENCY_URL
from test_operational import sources,ROOT

def payloads():
 b=io.BytesIO();w=PdfWriter();w.add_blank_page(width=72,height=72);w.write(b)
 return [('empty',b''),('truncated',b'%PDF-1.7\ntruncated'),('valid_native_but_unsupported',b.getvalue())]

def flag_source(root,uri=None):
 root.mkdir();rawroot=(ROOT/'fixtures/flagstaff-native-root.html').read_bytes();roots=root_inventory(rawroot);readers=[];bodies={};art=[];records=[]
 for i,r in enumerate(roots):
  child=URL+f'html/synthetic-child-{i}.html#s';fragment=f'<p><input name="code" value="{child}"><a href="{child}" id="s">Synthetic child {i}</a></p>'.encode();reader={'root':r,'url':URL+'cgi/reader.pl?cite='+r['source_id']+'&archive=html'};readers.append(reader);records.append(dict(reader,raw=fragment));bodies[r['source_url']]=f'<div id="mainContent"><h1>{r["label"]}</h1><p>Synthetic container body.</p></div>'.encode();extra=f'<p><a href="{uri}">PDF</a></p>' if uri and i==0 else '';bodies[child.split('#')[0]]=f'<div id="mainContent"><h3 id="s">Synthetic child {i}</h3><p>Synthetic legal body.</p>{extra}</div>'.encode()
 def add(role,url,data):
  n=len(art);rel=f'raw/{n:04d}.bin';(root/rel).parent.mkdir(exist_ok=True);(root/rel).write_bytes(data);start=datetime(2026,10,17,12,tzinfo=timezone.utc)+timedelta(seconds=n*2);art.append({'role':role,'source_url':url,'final_url':url,'status':200,'path':rel,'sha256':sha(data),'bytes':len(data),'started_at':start.isoformat(),'finished_at':(start+timedelta(seconds=1)).isoformat()})
 currency=b'<p>The Flagstaff City Charter and City Code are current through Ordinance 2026-19, passed August 25, 2026.</p>';add('root-toc-start',ROOT_TOC_URL,rawroot)
 for record in records:add('toc-start',record['url'],record['raw'])
 add('currency-start',CURRENCY_URL,currency)
 for u,body in bodies.items():add('content',u,body)
 for record in records:add('toc-end',record['url'],record['raw'])
 add('root-toc-end',ROOT_TOC_URL,rawroot);add('currency-end',CURRENCY_URL,currency);state={'source_url':URL,'observed_readers':readers,'inventory':inventory(records),'artifacts':art,'errors':[],'blocked':[],'synthetic_fixture':True};save(root/'checkpoint.json',state)
 return root

class InlineQualification(unittest.TestCase):
 def test_all_named_image_contexts_classify_before_any_decoder(self):
  uri='DATA:application/octet-stream;base64,QUJD\nUElYRUxT';cases=['<p><img src="'+uri+'"></p>','<picture><source src="'+uri+'"></picture>','<svg><image href="'+uri+'"></image><use xlink:href="'+uri+'"></use></svg>','<video poster="'+uri+'">Caption</video>','<p background="'+uri+'">Caption</p>','<p style="background:url('+uri+')">Caption</p>','<object type="IMAGE/PNG" data="'+uri+'"></object>','<a type="IMAGE/PNG" href="'+uri+'">Image label</a>']
  for markup in cases:
   with self.subTest(markup=markup),patch.object(base64,'b64decode',side_effect=AssertionError('decoder forbidden')):r=semantics(BeautifulSoup(markup,'html.parser').find(),'https://example.invalid/code')
   dumped=json.dumps(r);self.assertNotIn('QUJD',dumped);self.assertNotIn('UElYRUxT',dumped);self.assertIn('[IMAGE]',r['text']);self.assertTrue(r['assets']);self.assertTrue(all(not a['required'] and a['status']=='policy_omitted_image' for a in r['assets']))
 def test_image_reference_metadata_hashes_other_mime_payload_and_keeps_caption(self):
  uri='data:application/octet-stream;base64,QUJD\nUElYRUxT';node=BeautifulSoup('<p>Visible legal caption<img src="'+uri+'" alt="'+uri+'" title="Published map label"></p>','html.parser').p
  with patch.object(base64,'b64decode',side_effect=AssertionError('decoder forbidden')):r=semantics(node,'https://example.invalid/code')
  self.assertEqual(r['text'],'Visible legal caption[IMAGE]');self.assertEqual(r['assets'][0]['source_descriptive_attributes']['title'],'Published map label');self.assertNotIn('UElYRUxT',json.dumps(r));self.assertIn(sha(uri.encode()),json.dumps(r))
 def test_ordinary_anchor_image_style_metadata_is_hash_only(self):
  uri='data:application/octet-stream;base64,UNIQUE_INLINE_PIXEL_SENTINEL';node=BeautifulSoup('<p><a href="/law" style="background:url('+uri+')">Visible caption</a></p>','html.parser').p
  with patch.object(base64,'b64decode',side_effect=AssertionError('decoder forbidden')):r=semantics(node,'https://example.invalid/code')
  self.assertNotIn('UNIQUE_INLINE_PIXEL_SENTINEL',json.dumps(r));self.assertEqual(r['links'][0]['url'],'https://example.invalid/law');self.assertEqual(r['links'][0]['attributes']['style'],'[IMAGE]');self.assertIn('Visible caption',r['text'])
 def test_nonimage_iframe_and_object_inline_reference_is_inert_hash_only(self):
  uri='data:application/octet-stream;base64,UNIQUE_INLINE_DOCUMENT_SENTINEL';node=BeautifulSoup('<div><iframe src="'+uri+'"></iframe><object data="'+uri+'">Visible label</object></div>','html.parser').div
  with patch.object(base64,'b64decode',side_effect=AssertionError('decoder forbidden')):r=semantics(node,'https://example.invalid/code')
  self.assertNotIn('UNIQUE_INLINE_DOCUMENT_SENTINEL',json.dumps(r));self.assertIn('Visible label',r['text']);self.assertEqual(len(r['assets']),2);self.assertTrue(all(a['required'] and not a['format_qualified'] for a in r['assets']));self.assertIn('unqualified-inline-document-ref:sha256:',r['html'])
 def test_empty_truncated_and_valid_inline_pdf_all_block_king_closure_without_decode(self):
  for label,data in payloads():
   with self.subTest(case=label),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);source,native=sources(root);state=load(source/'checkpoint.json');a=next(a for a in state['artifacts'] if a['role']=='content');uri='data:application/pdf;base64,'+base64.b64encode(data).decode();body=(source/a['path']).read_bytes().replace(b'</body>',('<p><a href="'+uri+'">PDF</a></p></body>').encode());(source/a['path']).write_bytes(body);a.update(sha256=sha(body),bytes=len(body));save(source/'checkpoint.json',state)
    with patch.object(base64,'b64decode',side_effect=AssertionError('inline decoder forbidden')):r=king.run(source,root/'normalized')
    self.assertFalse(r['complete']);self.assertFalse(r['attachments_complete']);self.assertEqual(r['unresolved_nonimage_dependencies'],1);d=next(a for a in load(root/'normalized/dependencies.json') if a.get('inline_data'));self.assertTrue(d['required']);self.assertFalse(d['format_qualified']);self.assertEqual(d['status'],'unresolved_nonimage_attachment');self.assertEqual(d['encoded_characters'],len(base64.b64encode(data)))
 def test_inline_pdf_cannot_pass_flagstaff_whole_inventory_closure(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);baseline=flag_source(root/'control');self.assertTrue(flag.run(baseline,root/'control-normalized')['complete'])
  for label,data in payloads():
   with self.subTest(case=label),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);uri='data:application/pdf;base64,'+base64.b64encode(data).decode();source=flag_source(root/'source',uri)
    with patch.object(base64,'b64decode',side_effect=AssertionError('inline decoder forbidden')):r=flag.run(source,root/'normalized')
    self.assertFalse(r['complete']);self.assertEqual(r['unresolved_nonimage_dependencies'],1);self.assertEqual(r['missing_toc_edges'],0);self.assertEqual(r['source_documents'],36);d=next(a for a in load(root/'normalized/dependencies.json') if a.get('inline_data'));self.assertFalse(d['format_qualified']);self.assertTrue(d['required'])
if __name__=='__main__':unittest.main()
