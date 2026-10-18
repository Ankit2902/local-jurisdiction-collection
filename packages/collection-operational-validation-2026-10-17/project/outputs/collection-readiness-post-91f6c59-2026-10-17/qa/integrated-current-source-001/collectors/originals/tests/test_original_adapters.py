import copy,hashlib,io,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from source_common import *
import king_normalize as kn
import shared_transport as tr
from word_model import inspect

INDEX='''<html><head><title>King County Code</title></head><body><main>{}</main></body></html>'''
def fixture(root):
 root=Path(root);root.mkdir();items=[]
 for i in range(1,11):items.append(f'<h3><a href="https://aqua.kingcounty.gov/council/clerk/code/{i}_Title_{i}.htm">Title {i}: Test</a></h3><p>(Updated: 10/17/2026)</p>')
 index=INDEX.format(''.join(items)).encode();docs=kn.inventory(index);arts=[]
 def add(role,url,data):
  rel=f'raw/{len(arts):03d}.bin';(root/rel).parent.mkdir(exist_ok=True);(root/rel).write_bytes(data);sequence=len(arts);arts.append({'started_at':f'2026-10-17T12:00:{sequence*2:02d}+00:00','finished_at':f'2026-10-17T12:00:{sequence*2+1:02d}+00:00','role':role,'source_url':url,'final_url':url,'status':200,'path':rel,'sha256':sha(data)})
 add('index-start',kn.URL,index)
 for i,d in enumerate(docs,1):add('content',d['url'],f'<html><body><p>Title {i}</p><p>UPDATED: October 17, 2026</p><p><b>{i}.01.010 Test.</b> Operative body.</p></body></html>'.encode())
 add('index-end',kn.URL,index);state={'source_url':kn.URL,'artifacts':arts,'inventory':docs,'errors':[]};save(root/'checkpoint.json',state);return state

def word(drawing=True,note=False):
 buf=io.BytesIO();draw='<w:r><w:drawing><a:blip r:embed="rId1"/></w:drawing></w:r>' if drawing else ''
 with zipfile.ZipFile(buf,'w') as z:
  z.writestr('[Content_Types].xml','<Types/>')
  z.writestr('word/document.xml',f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body><w:p><w:r><w:t>Before </w:t></w:r>{draw}<w:r><w:t>After</w:t></w:r></w:p></w:body></w:document>')
  z.writestr('word/_rels/document.xml.rels','<Relationships><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/map.png"/></Relationships>')
  z.writestr('word/media/map.png',b'PIXELS_MUST_NEVER_BE_READ')
 return buf.getvalue()
class Offline(unittest.TestCase):
 def check_fault(self,mutator):
  with tempfile.TemporaryDirectory() as tmp:
   src=Path(tmp)/'source';s=fixture(src);mutator(src,s);save(src/'checkpoint.json',s)
   try:r=kn.run(src,Path(tmp)/'out')
   except (ValueError,StopIteration):return
   self.assertFalse(r['complete'])
 def test_complete_synthetic_source_is_separate(self):
  with tempfile.TemporaryDirectory() as tmp:
   src=Path(tmp)/'source';fixture(src);r=kn.run(src,Path(tmp)/'out');self.assertTrue(r['complete']);self.assertEqual(r['inventory_documents'],10)
 def test_missing(self):self.check_fault(lambda p,s:s['artifacts'].pop(2))
 def test_duplicate(self):self.check_fault(lambda p,s:s['artifacts'].append(dict(s['artifacts'][2])))
 def test_corrupt(self):self.check_fault(lambda p,s:(p/s['artifacts'][2]['path']).write_bytes(b'corrupt'))
 def test_interrupted(self):self.check_fault(lambda p,s:s['artifacts'].pop())
 def test_wrong_edition(self):
  def mutate(p,s):
   a=s['artifacts'][2];b=(p/a['path']).read_bytes().replace(b'October 17, 2026',b'October 16, 2026');(p/a['path']).write_bytes(b);a['sha256']=sha(b)
  self.check_fault(mutate)
 def test_wrong_document_identity(self):
  def mutate(p,s):
   a=s['artifacts'][2];b=(p/a['path']).read_bytes().replace(b'Title 2',b'Title 99');(p/a['path']).write_bytes(b);a['sha256']=sha(b)
  self.check_fault(mutate)
 def test_wrong_publication_identity(self):self.check_fault(lambda p,s:s.update(source_url='https://example.invalid/other'))
 def test_heading_only_fails(self):
  r,a=kn.parse(b'<html><body><p>Title 1</p><p><b>1.01.010 Heading.</b></p></body></html>',{'id':'a','url':'https://aqua.kingcounty.gov/council/clerk/code/1.htm','heading':'Title 1: Test','kind':'title','updated':'10/17/2026'});self.assertEqual(len(a['heading_only_unresolved']),1)
 def test_editorial_citations_not_sections(self):
  r,a=kn.parse(b'<html><body><p><b>1.01.010 History.</b> Ord. 1.</p></body></html>',{'id':'a','url':'https://aqua.kingcounty.gov/council/clerk/code/1.htm','heading':'Disposition table','kind':'editorial','updated':'10/17/2026'});self.assertEqual(a['section_records'],0);self.assertIn('Ord. 1.',r[0]['full_text'])
 def test_image_only_kept(self):
  r,a=kn.parse(b'<html><body><p>Title 1</p><p><b>1.01.010 Map.</b><img id="map" src="map.png"></p></body></html>',{'id':'a','url':'https://aqua.kingcounty.gov/council/clerk/code/1.htm','heading':'Title 1: Test','kind':'title','updated':'10/17/2026'});self.assertEqual(r[-1]['image_placeholder_count'],1);self.assertIn('[IMAGE]',r[-1]['full_text']);self.assertNotIn('<img',r[-1]['semantic_html'])
 def test_nested_tables_owned_once(self):
  r,a=kn.parse(b'<html><body><p>Title 1</p><p><b>1.01.010 Fees.</b></p><table><tr><td>Outer<table><tr><td>Inner</td></tr></table></td></tr></table></body></html>',{'id':'a','url':'https://aqua.kingcounty.gov/council/clerk/code/1.htm','heading':'Title 1: Test','kind':'title','updated':'10/17/2026'});self.assertEqual(a['source_tables'],2);self.assertEqual(a['owned_tables'],2)
 def test_no_image_member_read(self):
  original=zipfile.ZipFile.read
  def guarded(z,name,*a,**kw):
   self.assertFalse(str(name).startswith('word/media/'));return original(z,name,*a,**kw)
  with patch.object(zipfile.ZipFile,'read',guarded):r=inspect(word())
  self.assertIn('Before [IMAGE]After',r['text']);self.assertEqual(r['image_placeholder_count'],1);self.assertTrue(r['image_members_never_read']);self.assertFalse(r['images_extracted'])
 def test_empty_native_rejected(self):
  with self.assertRaises(ValueError):inspect(b'')
 def test_corrupt_native_rejected(self):
  with self.assertRaises((ValueError,zipfile.BadZipFile)):inspect(word()[:50])
 def test_external_image_relationship_omitted(self):
  r=inspect(word());self.assertEqual(r['relationships'][0]['status'],'policy_omitted_image');self.assertFalse(r['relationships'][0]['required'])
 def test_stopped_hosts_never_requested(self):
  for u in ['https://ecode360.com/123','https://phoenix.municipal.codes/CC','https://library.municode.com/a','https://static.spokanecity.org/a.pdf','https://ldh.la.gov/a.pdf','https://example.invalid/map.png']:
   with self.assertRaises(ValueError):forbid(u)
 def test_persisted_gate_stop(self):
  with tempfile.TemporaryDirectory() as t,patch.object(tr,'ROOT',Path(t)):
   u='https://example.invalid/code';tr.stop(u,429,{},'synthetic stop')
   with self.assertRaises(RuntimeError):tr.reserve(u)

class MorePolicy(unittest.TestCase):
 def package(self,body,rels='',footnotes=None):
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w') as z:
   z.writestr('[Content_Types].xml','<Types/>');z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:o="urn:schemas-microsoft-com:office:office"><w:body>'+body+'</w:body></w:document>');z.writestr('word/_rels/document.xml.rels','<Relationships>'+rels+'</Relationships>')
   if footnotes:z.writestr('word/footnotes.xml',footnotes)
  return data.getvalue()
 def test_native_picture_ole_omitted_without_binary_read(self):
  raw=self.package('<w:p><w:object><o:OLEObject ProgID="PBrush" r:id="r1"/></w:object></w:p>','<Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject" Target="embeddings/oleObject1.bin"/>')
  r=inspect(raw);self.assertEqual(r['text'],'[IMAGE]');self.assertFalse(r['relationships'][0]['required']);self.assertEqual(r['relationships'][0]['status'],'policy_omitted_image');self.assertNotIn('word/embeddings/oleObject1.bin',r['members_read'])
 def test_unknown_ole_remains_required(self):
  raw=self.package('<w:p><w:object><o:OLEObject ProgID="Excel.Sheet.8" r:id="r1"/></w:object></w:p>','<Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject" Target="embeddings/oleObject1.bin"/>')
  r=inspect(raw);self.assertTrue(r['relationships'][0]['required']);self.assertEqual(r['relationships'][0]['status'],'unresolved_nonimage_dependency')
 def test_word_hyperlink_incorporation_required(self):
  raw=self.package('<w:p><w:r><w:t>Appendix C incorporated by reference </w:t></w:r><w:hyperlink r:id="r1"><w:r><w:t>source</w:t></w:r></w:hyperlink></w:p>','<Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.invalid/appendix.pdf" TargetMode="External"/>')
  r=inspect(raw);self.assertTrue(r['relationships'][0]['required']);self.assertEqual(r['relationships'][0]['status'],'unresolved_nonimage_dependency')
 def test_word_note_reference_retained_and_missing_fails(self):
  raw=self.package('<w:p><w:r><w:t>Legal text</w:t><w:footnoteReference w:id="1"/></w:r></w:p>');r=inspect(raw);self.assertIn('[NOTE 1]',r['text']);self.assertEqual(len(r['missing_notes']),1)
 def test_word_metadata_image_bytes_redacted(self):
  raw=self.package('<w:p><w:drawing/></w:p>','<Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="DATA:IMAGE/PNG;base64,SENTINEL" TargetMode="External"/>');r=inspect(raw);self.assertNotIn('SENTINEL',json.dumps(r));self.assertEqual(r['relationships'][0]['target'],'[IMAGE]')
 def test_image_mime_not_read(self):
  from email.message import Message
  class Response:
   status=200;url='https://example.invalid/opaque';headers=Message()
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,*a):raise AssertionError('Image body read')
  Response.headers['Content-Type']='IMAGE/PNG'
  class Opener:
   def open(self,*a,**kw):return Response()
  with patch.object(tr,'reserve'),patch.object(tr.urllib.request,'build_opener',return_value=Opener()):raw,m=tr.fetch(Response.url)
  self.assertEqual(raw,b'');self.assertTrue(m['policy_omitted_image'])
 def test_repeated_charter_ids_keep_distinct_owners(self):
  from flagstaff_html_normalize import parse
  u='https://www.codepublishing.com/AZ/Flagstaff/html/FlagstaffCH.html';edges=[{'edge_id':'article1','source_url':u+'#1','label':'1 Term'},{'edge_id':'article2','source_url':u+'#1','label':'1 Powers'}]
  raw=b'<html><body><div id="mainContent"><h3><a id="1"></a>1 Term</h3><p>First body.</p><h3><a id="1"></a>1 Powers</h3><p>Second body.</p></div></body></html>'
  rr,report=parse(raw,u,edges);self.assertEqual(report['matched_toc_edges'],2);self.assertEqual(len(set(r['record_id'] for r in rr)),2);self.assertEqual(report['source_blocks'],report['unique_owned_blocks'])

class DOMBoundary(unittest.TestCase):
 def test_inline_adjacency_and_block_boundaries(self):
  from model import dom_text
  self.assertEqual(dom_text(BeautifulSoup('<div>1<sup>st</sup> ft<sup>3</sup><p>Next<br>Line</p><p><b>T</b><b>itle 3</b></p></div>','html.parser')),'1st ft3 Next Line Title 3')
 def test_comments_not_legal_text(self):
  from model import dom_text
  self.assertEqual(dom_text(BeautifulSoup('<p>Legal<!--SECRET-->text</p>','html.parser')),'Legaltext')
 def test_table_cell_inline_joins(self):
  from model import semantics
  s=BeautifulSoup('<table><tr><td>1<sup>st</sup></td><td>ft<sup>3</sup></td></tr></table>','html.parser');r=semantics(s.table,'https://example.invalid/code');self.assertEqual([c['text'] for c in r['tables'][0]['rows'][0]],['1st','ft3'])
 def test_standard_word_symbol_and_hard_hyphen(self):
  from word_model import ordered_text
  import xml.etree.ElementTree as E
  e=E.fromstring('<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:r><w:sym w:font="Courier New" w:char="0022"/><w:t>LOS</w:t><w:sym w:font="Courier New" w:char="0022"/><w:noBreakHyphen/><w:t>test</w:t></w:r></w:p>');self.assertEqual(ordered_text(e)[0],'"LOS"\u2011test')
if __name__=='__main__':unittest.main()
