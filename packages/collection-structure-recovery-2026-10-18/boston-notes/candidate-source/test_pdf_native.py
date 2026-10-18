"""Full-page source glyph/grid faults. No network or image decoding."""
import copy,io,json
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfWriter,PdfReader
from pypdf.generic import DictionaryObject as D,NameObject as N,NumberObject as I,DecodedStreamObject
import pymupdf
from model import pdf_pages
from pdf_grid import qualify,has_unprofiled_metadata
def fixture(open_edge=False,outside=False):
 w=PdfWriter();p=w.add_blank_page(200,200);font=w._add_object(D({N('/Type'):N('/Font'),N('/Subtype'):N('/Type1'),N('/BaseFont'):N('/Helvetica')}));p[N('/Resources')]=D({N('/Font'):D({N('/F1'):font})})
 lines=[(20,40,140,40),(20,100,140,100),(20,160,140,160),(20,40,20,160),(80,40,80,160),(140,40,140,160)]
 if open_edge:lines=lines[:-1]
 raw=b''.join(('%s %s m %s %s l S\n'%v).encode() for v in lines)
 for x,y,text in [(30,140,'Alpha'),(90,140,'Beta'),(30,80,'Gamma'),(90,80,'Delta')]:raw+=('BT /F1 9 Tf %s %s Td (%s) Tj ET\n'%(x,y,text)).encode()
 if outside:raw+=b'BT /F1 9 Tf 20 20 Td (Additional operative rule) Tj ET\n'
 s=DecodedStreamObject();s.set_data(raw);p[N('/Contents')]=w._add_object(s);out=io.BytesIO();w.write(out);return out.getvalue()
def tests():
 results=[];data=fixture()
 with patch('PIL.Image.open',side_effect=AssertionError('Image decoder invoked')):row=pdf_pages(data,'grid','https://example.invalid/grid.pdf')[0]
 q=row['source_qualification'];assert q['source_text_qualified'] and q['source_tables_qualified'] and q['source_reading_order_qualified'];assert len(q['cells'])==4 and q['original_nonwhitespace_glyph_count']==19;results.append({'name':'all_source_page_glyph_order_and_four_original_closed_cells_qualify','passed':True})
 assert not pdf_pages(fixture(open_edge=True),'grid','https://example.invalid/grid.pdf')[0]['source_qualification']['source_tables_qualified'];results.append({'name':'open_original_grid_edge_cannot_qualify','passed':True})
 assert not pdf_pages(fixture(outside=True),'grid','https://example.invalid/grid.pdf')[0]['source_qualification']['source_text_qualified'];results.append({'name':'unowned_outside_operative_text_cannot_be_mislabeled_note_or_Artifact','passed':True})
 doc=pymupdf.open(stream=data,filetype='pdf');plain=PdfReader(io.BytesIO(data)).pages[0].extract_text()
 def rejects(name,mutate):
  changed=copy.deepcopy(row);mutate(changed);report=qualify(doc[0],plain,changed['layout'],changed['native_source_evidence'],changed['native_source_evidence']['image_placements']);assert not report['source_tables_qualified'],name;results.append({'name':name,'passed':True})
 rejects('changed_native_cell_span_cannot_qualify',lambda d:d['layout']['table_candidates'][0]['cells'][0][0].update(colspan=2))
 rejects('lost_middle_cell_character_cannot_qualify',lambda d:d['layout']['table_candidates'][0]['cells'][0][0].update(text='Alph'))
 rejects('cell_case_or_punctuation_drift_cannot_qualify',lambda d:d['layout']['table_candidates'][0]['cells'][0][0].update(text='alpha!'))
 rejects('swapped_cell_reading_order_cannot_qualify',lambda d:d['layout']['table_candidates'][0]['cells'].reverse())
 rejects('duplicated_cell_body_ownership_cannot_qualify',lambda d:d['layout']['table_candidates'][0]['cells'][0].append(copy.deepcopy(d['layout']['table_candidates'][0]['cells'][0][0])))
 assert not qualify(doc[0],plain,row['layout'],row['native_source_evidence'],[],True)['source_tables_qualified'];results.append({'name':'unprofiled_ActualText_or_annotation_requires_separate_qualification','passed':True})
 doc.close();return {'schema_version':1,'kind':'Synthetic production full-page native-grid profile faults, not a live publisher proof','passed':True,'count':len(results),'tests':results}
if __name__=='__main__':
 result=tests();Path(__file__).with_name('pdf-native-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
