"""Offline image-payload metadata policy probes; no transport or image decoding."""
import sys,json,io,socket,hashlib
from pathlib import Path
from unittest.mock import patch
def main():
 source_dir=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
 sys.path.insert(0,str(source_dir))
 from test_pdf_tags import fixture
 from pdf_tags import parse,safe
 from audit_pdf_tags import audit
 from pypdf import PdfReader,PdfWriter
 from pypdf.generic import NameObject as N,TextStringObject as T,DictionaryObject as D
 from pdfminer.pdftypes import PDFStream
 from model import html_record,refs
 PAYLOADS=['DATA:IMAGE/PNG;base64,QUJD\nUElYRUxTX0NPTlRJTlVBVElPTl9NVVNUX05PVF9TVVJWSVZF','Image source: DATA:IMAGE/PNG;base64,QUJD\r\nUElYRUxTX0NPTlRJTlVBVElPTl9NVVNUX05PVF9TVVJWSVZF','prefix url("data:image/svg+xml;base64,QUJD\nUElYRUxTX0NPTlRJTlVBVElPTl9NVVNUX05PVF9TVVJWSVZF") suffix']
 TAIL='UElYRUxTX0NPTlRJTlVBVElPTl9NVVNUX05PVF9TVVJWSVZF'
 def pdf(value,field):
  r=PdfReader(io.BytesIO(fixture()));w=PdfWriter();w.clone_document_from_reader(r);root=w._root_object['/StructTreeRoot'];doc=root['/K'];figure=doc['/K'][-1].get_object()
  if field=='actual':figure[N('/ActualText')]=T(value)
  if field=='attribute':figure[N('/A')]=D({N('/O'):N('/Layout'),N('/ImageMetadata'):T(value)})
  if field=='inline':
   out=io.BytesIO();T(value).write_to_stream(out);p=w.pages[0];stream=p['/Contents'];raw=stream.get_data();assert b'(RD)' in raw;stream.set_data(raw.replace(b'(RD)',out.getvalue()))
  b=io.BytesIO();w.write(b);return b.getvalue()
 results=[]
 def check(name,fn):
  try:fn();results.append({'name':name,'passed':True})
  except Exception as e:results.append({'name':name,'passed':False,'error':type(e).__name__+': '+str(e)})
 def clean(value):
  serial=json.dumps(value);assert TAIL not in serial and 'data:image/' not in serial.lower(),'inline image payload escaped redaction';assert '[IMAGE]' in serial
 original_get=PDFStream.get_data
 def no_image(self):
  assert getattr(self.get('Subtype'),'name',None)!='Image','image stream decode';return original_get(self)
 with patch.object(socket.socket,'connect',side_effect=AssertionError('network attempted')),patch.object(PDFStream,'get_data',no_image),patch('PIL.Image.open',side_effect=AssertionError('image decoder')):
  for i,value in enumerate(PAYLOADS):
   check('nested_safe_metadata_'+str(i),lambda v=value:clean(safe({'a':['ordinary',{'uri':v}]})))
   for field in ['actual','attribute','inline']:
    def pdf_check(v=value,f=field):
     data=pdf(v,f);document=parse(data);clean(document)
     assert audit(data,document)['passed'],'independent metadata audit mismatch'
     if f!='attribute' and v.startswith('Image source: '):
      assert not document['qualification']['source_text_qualified'],'ambiguous mixed metadata falsely complete'
      assert 'Image source: ' in json.dumps(document),'available source prefix lost'
      import copy
      changed=copy.deepcopy(document);changed['qualification']['source_text_qualified']=True
      assert not audit(data,changed)['passed'],'independent auditor accepted false completeness'
     if f!='attribute' and v.startswith('prefix url('):
      assert document['qualification']['source_text_qualified'],'bounded quoted URI incorrectly ambiguous'
      assert 'prefix url(' in json.dumps(document) and ') suffix' in json.dumps(document),'known surrounding text lost'
    check('production_pdf_'+field+'_'+str(i),pdf_check)
   def html(v=value):
    text='<h2 id="rid-doc">Section 1</h2><p data-image-metadata="'+v.replace('"','&quot;')+'">Rule applies.</p>'
    record=html_record({'doc_id':'doc','id':1,'html':text},{'document_id':'doc','internal_id':1,'heading':'Section 1','path':['Section 1'],'parent_id':None,'has_children':False},{'client_slug':'test','code_slug':'test','version_uuid':'v','code_uuid':'c'},'https://example.invalid/book','hash')
    clean(record);assert 'Rule applies.' in record['text']
   check('production_html_metadata_'+str(i),html)
   def ref(v=value):
    assets,links=refs('<img src="'+v.replace('"','&quot;')+'">','https://example.invalid/book');clean([assets,links]);assert all(a['disposition']=='image-placeholder' for a in assets)
   check('production_reference_metadata_'+str(i),ref)
  for field in ['actual','inline']:
   def quoted(f=field):
    value='Before legal text "DATA:IMAGE/PNG;base64,QUJD\n'+TAIL+'" after legal text';data=pdf(value,f);document=parse(data);clean(document)
    assert document['qualification']['source_text_qualified'];assert 'Before legal text' in json.dumps(document) and 'after legal text' in json.dumps(document);assert audit(data,document)['passed']
   check('known_quoted_ActualText_preserves_exact_surrounding_caption_'+field,quoted)
  for field in ['actual','inline']:
   for ambiguous in [False,True]:
    def repeated(f=field,a=ambiguous):
     uri='DATA:IMAGE/PNG;base64,QUJD\n'+TAIL
     value='Before legal text "'+uri+'" between legal text '+(uri if a else '"'+uri+'" after legal text')
     data=pdf(value,f);document=parse(data);clean(document);serial=json.dumps(document)
     assert 'Before legal text' in serial and 'between legal text' in serial,'available prose lost'
     assert document['qualification']['source_text_qualified']==(not a),'mixed URI qualification wrong'
     if not a:assert 'after legal text' in serial,'trailing legal text lost'
     assert audit(data,document)['passed'],'independent repeated URI audit mismatch'
    check('every_bounded_URI_or_ambiguous_remainder_'+field+'_'+str(ambiguous),repeated)
  check('nonimage_metadata_unchanged',lambda: (_ for _ in ()).throw(AssertionError('ordinary metadata altered')) if safe({'x':'Available caption. Legal rule.'})!={'x':'Available caption. Legal rule.'} else None)
 print(json.dumps({'source_dir':sys.argv[1] if len(sys.argv)>1 else '.','passed':all(x['passed'] for x in results),'count':len(results),'tests':results},indent=2))

 raise SystemExit(0 if all(x['passed'] for x in results) else 1)

if __name__=='__main__':main()
