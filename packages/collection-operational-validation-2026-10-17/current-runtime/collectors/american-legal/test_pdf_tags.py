"""Synthetic source-tag continuation/table/resume/corruption tests; no network or raster images."""
import io,json,tempfile,copy,hashlib,sys
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject as D,NameObject as N,ArrayObject as A,NumberObject as I,FloatObject,TextStringObject as T,DecodedStreamObject,NullObject,BooleanObject
from pdf_tags import parse,inventory,canonical,sha

def fixture(unknown=False,unmarked=False,duplicate=False,image_actual=False,unknown_role=False,caption=False):
 writer=PdfWriter();pages=[writer.add_blank_page(612,792) for _ in range(2)];font=writer._add_object(D({N('/Type'):N('/Font'),N('/Subtype'):N('/Type1'),N('/BaseFont'):N('/Helvetica')}))
 for i,page in enumerate(pages):page[N('/Resources')]=D({N('/Font'):D({N('/F1'):font})});page[N('/StructParents')]=I(i)
 pages[1]['/Resources'][N('/Properties')]=D({N('/continued'):D({N('/MCID'):I(0)})})
 stream1=b'/Artifact BMC BT /F1 10 Tf 50 770 Td (Header) Tj ET EMC\n/P <</MCID 0>> BDC BT /F1 12 Tf 50 700 Td (Styled ) Tj ET EMC\n/Span <</MCID 1>> BDC BT /F1 12 Tf 90 700 Td (wo) Tj /Span <</ActualText (RD)>> BDC (rd) Tj EMC ( continues.) Tj ET EMC\n/TH <</MCID 2>> BDC BT /F1 12 Tf 50 650 Td (Use) Tj ET EMC\n/TD <</MCID 3>> BDC BT /F1 12 Tf 50 625 Td (Office) Tj ET EMC\n/TD <</MCID 4>> BDC BT /F1 12 Tf 150 625 Td (Allowed) Tj ET EMC\n/Figure <</MCID 5>> BDC 50 500 100 50 re S BT /F1 10 Tf 50 510 Td (MAP LABEL) Tj ET EMC\n'
 if unmarked:stream1+=b'BT /F1 12 Tf 50 450 Td (Unmarked legal rule) Tj ET\n'
 if caption:stream1+=b'/Caption <</MCID 6>> BDC BT /F1 10 Tf 50 490 Td (Available graphic caption.) Tj ET EMC\n'
 stream2=b'/Artifact BMC BT /F1 10 Tf 50 770 Td (Header) Tj ET EMC\n/P /continued BDC BT /F1 12 Tf 50 700 Td ( Continued on next page.) Tj ET EMC\n'
 for page,raw in zip(pages,[stream1,stream2]):
  stream=DecodedStreamObject();stream.set_data(raw);page[N('/Contents')]=writer._add_object(stream)
 root=D({N('/Type'):N('/StructTreeRoot')});rootref=writer._add_object(root)
 def element(role,parent,page=0,k=None,extra=None):
  value=D({N('/Type'):N('/StructElem'),N('/S'):N('/'+role),N('/P'):parent,N('/Pg'):pages[page].indirect_reference})
  if k is not None:value[N('/K')]=k
  if extra:value.update(extra)
  return writer._add_object(value)
 def mcr(page,mcid):return D({N('/Type'):N('/MCR'),N('/Pg'):pages[page].indirect_reference,N('/MCID'):I(mcid)})
 document=element('Document',rootref);p=element('P',document);span=element('Span',p,k=I(1));children=A([I(0)])
 if not unknown:children.append(span)
 children.append(mcr(1,0))
 if duplicate:children.append(I(0))
 p.get_object()[N('/K')]=children
 table=element('Table',document);tr1=element('TR',table);tr2=element('TR',table);th=element('TH',tr1,k=I(2),extra={N('/C'):N('/wide')});td1=element('TD',tr2,k=I(3));td2=element('TD',tr2,k=I(4));tr1.get_object()[N('/K')]=A([th]);tr2.get_object()[N('/K')]=A([td1,td2]);table.get_object()[N('/K')]=A([tr1,tr2])
 image=element('Figure',document,k=I(5),extra={N('/Alt'):T('data:image/png;base64,SENTINEL')})
 if caption:
  child=element('Caption',image,k=I(6));image.get_object()[N('/K')]=A([I(5),child])
 if image_actual:image.get_object()[N('/ActualText')]=T('DATA:IMAGE/PNG;base64,SENTINEL')
 if unknown_role:table.get_object()[N('/S')]=N('/UnmappedLegalTable')
 document.get_object()[N('/K')]=A([p,table,image]);root[N('/K')]=document;root[N('/ClassMap')]=D({N('/wide'):D({N('/O'):N('/Table'),N('/ColSpan'):I(2)})});root[N('/ParentTree')]=writer._add_object(D({N('/Nums'):A([I(0),A([p,span,th,td1,td2,image]),I(1),A([NullObject()])])}));root[N('/ParentTreeNextKey')]=I(2);writer._root_object[N('/StructTreeRoot')]=rootref;writer._root_object[N('/MarkInfo')]=D({N('/Marked'):BooleanObject(True)})
 out=io.BytesIO();writer.write(out);return out.getvalue()

def tests():
 results=[];data=fixture()
 with patch('PIL.Image.open',side_effect=AssertionError('Image decoder invoked')):
  document=parse(data)
 q=document['qualification'];assert q['source_structure_supported'] and q['source_table_count']==1 and q['source_table_cells']==3 and q['actual_text_variant_count']==1;assert 'Styled word continues. Continued on next page.' in document['logical_text'];assert 'MAP LABEL' not in document['logical_text'] and document['available_figure_text'][0]['original_glyph_text']=='MAP LABEL' and 'SENTINEL' not in json.dumps(document);assert document['logical_text'].count('[IMAGE]')==1;assert 'Header' not in document['logical_text'] and all(p['artifact_text']=='Header' for p in document['pages']);assert document['tables'][0]['rows'][0][0]['colspan']==2
 results.append({'name':'forward_source_MCIDs_keep_cross_page_continuation_nested_style_word_ActualText_class_span_and_IMAGE_without_decoder','passed':True})
 assert not parse(fixture(unknown=True))['qualification']['source_text_qualified'];results.append({'name':'missing_middle_source_tag_unknown_marked_text_cannot_qualify','passed':True})
 assert not parse(fixture(unmarked=True))['qualification']['source_text_qualified'];results.append({'name':'unmarked_operative_text_is_not_an_Artifact','passed':True})
 try:parse(fixture(duplicate=True));raise RuntimeError('Duplicated source reference accepted')
 except AssertionError:results.append({'name':'duplicate_source_MCID_cannot_duplicate_owned_body','passed':True})
 with tempfile.TemporaryDirectory() as t:
  cache=Path(t)
  try:parse(data,cache,interrupt_after=1);raise RuntimeError('Interruption missing')
  except KeyboardInterrupt:pass
  assert (cache/'page-0001.json').exists() and not(cache/'page-0002.json').exists();resumed=parse(data,cache);assert resumed==document;results.append({'name':'interrupted_page_cache_resumes_to_identical_full_document','passed':True})
  page=cache/'page-0001.json';original=page.read_bytes();packet=json.loads(original);packet['payload']['blocks'][0]['text']='Corrupt legal requirement';page.write_text(json.dumps(packet))
  try:parse(data,cache);raise RuntimeError('Corrupt cache accepted')
  except AssertionError:results.append({'name':'corrupt_page_cache_rejected','passed':True})
  page.write_bytes(original);binding=cache/'binding.json';value=json.loads(binding.read_text());value['source_sha256']='wrong-source';binding.write_text(json.dumps(value))
  try:parse(data,cache);raise RuntimeError('Wrong-source cache accepted')
  except AssertionError:results.append({'name':'wrong_source_binding_rejected','passed':True})
 from audit_pdf_tags import audit
 assert audit(data,document)['passed'];results.append({'name':'independent_original_tree_MCIDs_ActualText_cells_and_native_two_page_glyphs_match','passed':True})
 for name,mutate in [
  ('original_source_cell_span_tampering',lambda d:d['tables'][0]['rows'][0][0].update(colspan=9)),
  ('omitted_middle_body_keeps_source_roots',lambda d:d['pages'][0]['blocks'].pop(1)),
  ('duplicated_normalized_body',lambda d:d['pages'][0]['blocks'].append(copy.deepcopy(d['pages'][0]['blocks'][0]))),
  ('source_inline_ActualText_omitted',lambda d:d['pages'][0]['inline_actual_text'].clear()),
  ('source_K_children_reordered',lambda d:d['source_inventory']['nodes'][1]['children'].reverse()),
  ('operative_continuation_mislabeled_Artifact',lambda d:d['pages'][1].update(artifact_text=d['pages'][1]['artifact_text']+d['pages'][1]['blocks'][0]['glyph_text'],blocks=[])),
  ('source_hash_changed',lambda d:d.update(source_sha256='wrong'))]:
  changed=copy.deepcopy(document);mutate(changed);assert not audit(data,changed)['passed'],name;results.append({'name':name,'passed':True})
 redacted_data=fixture(image_actual=True);redacted=parse(redacted_data);assert 'SENTINEL' not in json.dumps(redacted) and audit(redacted_data,redacted)['passed'];results.append({'name':'source_Figure_ActualText_data_image_payload_hash_only','passed':True})
 assert not parse(fixture(unknown_role=True))['qualification']['source_tables_qualified'];results.append({'name':'unmapped_source_table_role_cannot_silently_qualify','passed':True})
 caption_data=fixture(caption=True);caption_doc=parse(caption_data);assert '[IMAGE]\nAvailable graphic caption.' in caption_doc['logical_text'] and caption_doc['available_figure_text'][0]['original_glyph_text']=='MAP LABEL' and audit(caption_data,caption_doc)['passed'];results.append({'name':'Figure_direct_vector_labels_retained_separately_and_explicit_Caption_child_preserved_in_source_order','passed':True})
 lost=copy.deepcopy(caption_doc);lost['available_figure_text'].clear();assert not audit(caption_data,lost)['passed'];results.append({'name':'available_Figure_label_ledger_omission_cannot_pass_independent_source_or_native_glyph_audit','passed':True})
 from model import pdf_pages
 tagged_rows=pdf_pages(data,'test-book','https://example.invalid/book.pdf');assert len(tagged_rows)==2 and sum('tagged_document' in p for p in tagged_rows)==1;assert tagged_rows[0]['tagged_document']['logical_text']==document['logical_text'];assert len({b for p in tagged_rows for b in p['source_owned_block_ids']})==sum(len(p['source_owned_block_ids']) for p in tagged_rows);assert all(p['source_qualification']['source_text_qualified'] for p in tagged_rows);results.append({'name':'production_pdf_pages_integrates_full_book_source_tree_and_unique_page_body_ownership','passed':True})
 writer=PdfWriter();page=writer.add_blank_page(100,100);image=DecodedStreamObject();image.set_data(b'SENTINEL-NOT-DECODED');image.update({N('/Type'):N('/XObject'),N('/Subtype'):N('/Image'),N('/Width'):I(1),N('/Height'):I(1),N('/ColorSpace'):N('/DeviceRGB'),N('/BitsPerComponent'):I(8)});page[N('/Resources')]=D({N('/XObject'):D({N('/Im1'):writer._add_object(image)})});content=DecodedStreamObject();content.set_data(b'q 100 0 0 100 0 0 cm /Im1 Do Q');page[N('/Contents')]=writer._add_object(content);stream=io.BytesIO();writer.write(stream)
 from pdfminer.pdftypes import PDFStream
 original_get=PDFStream.get_data
 def no_image_stream(self):
  assert getattr(self.get('Subtype'),'name',None)!='Image','Image stream decoded'
  return original_get(self)
 with patch.object(PDFStream,'get_data',no_image_stream),patch('PIL.Image.open',side_effect=AssertionError('Image decoder invoked')):
  image_rows=pdf_pages(stream.getvalue(),'image-only','https://example.invalid/native.pdf')
 assert image_rows[0]['text'].strip()=='[IMAGE]' and image_rows[0]['image_placeholder_count']==1 and image_rows[0]['source_qualification']['policy_not_applicable_to_text_glyph_fidelity'] and 'SENTINEL' not in json.dumps(image_rows);results.append({'name':'source_image_only_no_glyph_page_policy_NA_exact_placeholder_no_image_stream_decode_or_payload','passed':True})
 return {'schema_version':1,'kind':'synthetic production PDF-tag parser tests; not live source proof','passed':True,'count':len(results),'tests':results}
if __name__=='__main__':
 result=tests();path=Path(__file__).parent/'pdf-tag-tests.json';path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
