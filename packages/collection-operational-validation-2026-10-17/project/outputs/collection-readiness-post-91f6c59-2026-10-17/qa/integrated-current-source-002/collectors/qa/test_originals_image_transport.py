"""Independent no-image gates for the actual original-source implementation."""
import io,json,sys,unittest,zipfile
from email.message import Message
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];FAMILY=ROOT/'collectors/originals';sys.path.insert(0,str(FAMILY))
import shared_transport as transport
from word_model import inspect
from king_normalize import parse

def word_fixture():
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w') as z:
  z.writestr('[Content_Types].xml','<Types/>')
  z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body><w:p><w:r><w:t>Before </w:t></w:r><w:r><w:drawing><a:blip r:embed="r1"/></w:drawing></w:r><w:r><w:t>After</w:t></w:r></w:p></w:body></w:document>')
  z.writestr('word/_rels/document.xml.rels','<Relationships><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/map.png"/></Relationships>')
  z.writestr('word/media/map.png',b'PIXELS_MUST_NEVER_BE_READ')
 return b.getvalue()
class OriginalsImages(unittest.TestCase):
 def test_image_content_type_body_never_read(self):
  class Response:
   status=200;url='https://example.invalid/opaque';headers=Message()
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,*a):raise AssertionError('Image body read')
  Response.headers['Content-Type']='IMAGE/PNG'
  class Opener:
   def open(self,*a,**kw):return Response()
  with patch.object(transport,'reserve'),patch.object(transport.urllib.request,'build_opener',return_value=Opener()):raw,receipt=transport.fetch(Response.url)
  self.assertEqual(raw,b'');self.assertTrue(receipt['policy_omitted_image'])
 def test_word_image_member_never_opened(self):
  original=zipfile.ZipFile.read
  def denied(z,name,*a,**kw):
   self.assertFalse(str(name).startswith(('word/media/','word/embeddings/')));return original(z,name,*a,**kw)
  with patch.object(zipfile.ZipFile,'read',denied):result=inspect(word_fixture())
  self.assertIn('Before [IMAGE]After',result['text']);self.assertTrue(result['image_members_never_read']);self.assertFalse(result['images_extracted']);self.assertNotIn('PIXELS_MUST_NEVER_BE_READ',json.dumps(result))
 def test_actual_html_parser_keeps_image_only_section_and_cell(self):
  raw=b'<html><body><p>Title 1</p><p><b>1.01.010 Map.</b><img src="map.png"></p><table><tr><td background="cell.png">Cell rule</td></tr></table></body></html>'
  rows,_=parse(raw,{'id':'a','url':'https://aqua.kingcounty.gov/council/clerk/code/1.htm','heading':'Title 1: Test','kind':'title','updated':'10/17/2026'})
  row=rows[-1];self.assertIn('[IMAGE]',row['full_text']);self.assertIn('[IMAGE]',row['tables'][0]['rows'][0][0]['text']);self.assertNotIn('<img',row['semantic_html']);self.assertNotIn('background=',row['semantic_html'])
if __name__=='__main__':unittest.main(verbosity=2)
