"""Actual six-page family parser integration + unchanged 630 IR records; no full-PDF parse."""
from pathlib import Path
from collections import Counter
import copy,csv,hashlib,inspect,io,json,sys,time
from unittest.mock import patch,PropertyMock
import pdfplumber,pypdfium2 as p
from pdfminer.pdftypes import PDFStream
from pypdf._page import PageObject
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'candidate'))
from collectors.encodeplus import pdf_structure,native_document,sto_appendix_b
BASE=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/collection-readiness-post1997ee1-2026-10-17/upoc-parser-integration-candidate-v1/derived-records.jsonl')
FIX=ROOT/'candidate/collectors/encodeplus/fixtures/sto-appendix-b'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def read(f):return json.loads(f.read_text())
def main():
 assert sha(BASE)=='6b5c5212b047f69a6a941ab2ba2b2eb88af19bda9a40b88c36636d839a100547';cfg=read(FIX/'source.json');item=cfg['item'];source=FIX/'source.pdf';assert sha(source)==sto_appendix_b.PDF_SHA;base=[json.loads(l) for l in BASE.read_text().splitlines()];assert len(base)==636;before={p.relative_to(ROOT/'candidate').as_posix():sha(p) for p in (ROOT/'candidate').rglob('*') if p.is_file() and '__pycache__'not in p.parts};calls=[];parse_pages=[];stream=PDFStream.get_data;words=pdfplumber.page.Page.extract_words
 def no(*a,**kw):calls.append('forbidden');raise AssertionError('No images/render/OCR/network')
 def guard(s):
  if getattr(s.attrs.get('Subtype'),'name',None)=='Image':return no()
  return stream(s)
 def wordguard(page,*a,**kw):
  parse_pages.append(page.page_number);assert page.page_number in [198,199,200,201,202,203],'Unexpected content parse outside finite scope';return words(page,*a,**kw)
 code=inspect.getsource(pdf_structure.pages);needle='for n,original in enumerate(pdf.pages):';assert code.count(needle)==1;finite=code.replace(needle,'for n,original in ((n,pdf.pages[n]) for n in range(197,203)):');instrument=ROOT/'finite-pages-source.py';assert not instrument.exists();instrument.write_text(finite);exec(compile(finite,str(instrument),'exec'),pdf_structure.__dict__)
 first=next(r for r in base if r['document_id']==item['id'] and r['physical_page']==198);config={k:first[k] for k in ['publication','jurisdiction','state']};start=time.monotonic()
 with patch('socket.socket',side_effect=no),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=no),patch.object(p.PdfPage,'render',side_effect=no),patch.object(p.PdfPage,'get_objects',side_effect=no),patch.object(p.PdfImage,'get_bitmap',side_effect=no),patch.object(p.PdfImage,'extract',side_effect=no),patch.object(PDFStream,'get_data',guard),patch.object(pdfplumber.page.Page,'extract_words',wordguard):new,errors=pdf_structure.pages(source.read_bytes(),item,config)
 
 for r in new:
  r['primary_source_owners']=copy.deepcopy(item['owners']);r['document_source_title']=item['heading']
 assert not errors and not calls and set(parse_pages)=={198,199,200,201,202,203} and [r['physical_page'] for r in new]==[198,199,200,201,202,203]
 newmap={r['id']:r for r in new};derived=[];changes=[]
 for r in base:
  if r['id']not in newmap:derived.append(r);continue
  z=newmap[r['id']];assert z['superseded_detector_diagnostics']['original_record_fields']=={k:r[k] for k in ['tables','ordered_blocks','text','ordering','pdf_qualification']},'Fresh family baseline differs from composed IR; refuse cache substitution';
  for k,v in r.items():
   if k not in ['tables','ordered_blocks','text','ordering','pdf_qualification']:assert z[k]==v,('Unrelated field changed',r['id'],k)
  derived.append(z);changes.append(z['id'])
 assert len(changes)==6 and all(a==b for a,b in zip(base,derived) if a['id']not in newmap)
 existing=[r for r in base if r.get('canonical_structure_selection')];assert len(existing)==7;assert all(next(z for z in derived if z['id']==r['id'])==r for r in existing)
 summary=sto_appendix_b.summary(new);assert summary['physical_cell_fidelity_complete'] and not summary['whole_pdf_table_semantics_complete'];oldimages=[(r['id'],r['image_placeholder_count'],[b for b in r['ordered_blocks'] if b['kind']=='image_placeholder']) for r in base];newimages=[(r['id'],r['image_placeholder_count'],[b for b in r['ordered_blocks'] if b['kind']=='image_placeholder']) for r in derived];assert oldimages==newimages
 out=ROOT/'derived';assert not out.exists();out.mkdir();serialized=native_document.outputs(derived)
 for name,data in serialized.items():(out/name).write_bytes(data)
 csvrows=list(csv.DictReader(io.StringIO(serialized['records.csv'].decode())));assert len(csvrows)==636 and all(row['id']==r['id'] and row['text']==r['text'] for row,r in zip(csvrows,derived))
 assert before=={p.relative_to(ROOT/'candidate').as_posix():sha(p) for p in (ROOT/'candidate').rglob('*') if p.is_file() and '__pycache__'not in p.parts};report={'passed':True,'scope':'Exact original six Appendix B pages parsed through composed family function; all other630IRrecords unchanged, no full224/636parse','base_records_sha256':sha(BASE),'base_composition_manifest_sha256':'fe3eb10a9317bb7a749407d0f859660868186b9dcf3a6844c0b052c8d9ad1d6c','derived_records_sha256':sha(out/'records.jsonl'),'derived_csv_sha256':sha(out/'records.csv'),'changed_records':changes,'unchanged_records':630,'prior7canonical_selections_unchanged':True,'actual_content_parse_page_numbers':sorted(set(parse_pages)),'loop_instrumentation_only':{'original':needle,'executed':'for n,original in ((n,pdf.pages[n]) for n in range(197,203)):','executed_function_sha256':sha(instrument)},'canonical_table_cells':sum(len(t['cells']) for r in new for t in r['tables']),'canonical_text_csv_match':True,'original5fields_exact_superseded_diagnostics':True,'image_markers_ownership_identical':True,'image_placeholder_count':sum(r['image_placeholder_count'] for r in derived),'network_image_decode_extract_render_OCR_calls':0,'appendix_b_dimensions':summary,'executed_family_hashes':{n:sha(ROOT/'candidate/collectors/encodeplus'/n) for n in ['sto_appendix_b.py','pdf_structure.py','native_document.py']},'elapsed_seconds':time.monotonic()-start};(ROOT/'CANONICAL-DERIVATIVE-REPORT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
