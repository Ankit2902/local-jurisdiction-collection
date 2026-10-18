"""Portable read-only actual six-page canonical replay; unchanged630IR binding."""
from pathlib import Path
from collections import Counter
import copy,csv,gzip,hashlib,inspect,io,json,sys
from unittest.mock import patch,PropertyMock
import pdfplumber,pypdfium2 as p
from pdfminer.pdftypes import PDFStream
from pypdf._page import PageObject
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'candidate'))
from collectors.encodeplus import pdf_structure,native_document,sto_appendix_b
FIX=ROOT/'candidate/collectors/encodeplus/fixtures/sto-appendix-b'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def read(f):return json.loads(f.read_text())
def main():
 files=[q for q in ROOT.rglob('*') if q.is_file() and '__pycache__'not in q.parts and not q.name.endswith('.log')];before={q.relative_to(ROOT).as_posix():sha(q) for q in files};raw=gzip.decompress((ROOT/'source/composed-base-636.jsonl.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()=='6b5c5212b047f69a6a941ab2ba2b2eb88af19bda9a40b88c36636d839a100547';base=[json.loads(l) for l in raw.decode().splitlines()];del raw;actual=[json.loads(l) for l in (ROOT/'derived/records.jsonl').read_text().splitlines()];cfg=read(FIX/'source.json');it=cfg['item'];source=FIX/'source.pdf';assert sha(source)==sto_appendix_b.PDF_SHA
 code=inspect.getsource(pdf_structure.pages);old='for n,original in enumerate(pdf.pages):';assert code.count(old)==1;finite=code.replace(old,'for n,original in ((n,pdf.pages[n]) for n in range(197,203)):');assert hashlib.sha256(finite.encode()).hexdigest()==sha(ROOT/'finite-pages-source.py');exec(compile(finite,str(ROOT/'finite-pages-source.py'),'exec'),pdf_structure.__dict__)
 calls=[];parsed=[];getdata=PDFStream.get_data;wordextract=pdfplumber.page.Page.extract_words
 def no(*a,**kw):calls.append('forbidden');raise AssertionError('No images/render/OCR/network')
 def stream(s):
  if getattr(s.attrs.get('Subtype'),'name',None)=='Image':return no()
  return getdata(s)
 def words(page,*a,**kw):parsed.append(page.page_number);assert page.page_number in range(198,204);return wordextract(page,*a,**kw)
 row=next(r for r in base if r['document_id']==it['id'] and r['physical_page']==198);config={k:row[k] for k in ['publication','jurisdiction','state']}
 with patch('socket.socket',side_effect=no),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=no),patch.object(p.PdfPage,'render',side_effect=no),patch.object(p.PdfPage,'get_objects',side_effect=no),patch.object(p.PdfImage,'get_bitmap',side_effect=no),patch.object(p.PdfImage,'extract',side_effect=no),patch.object(PDFStream,'get_data',stream),patch.object(pdfplumber.page.Page,'extract_words',words):fresh,errors=pdf_structure.pages(source.read_bytes(),it,config)
 assert not calls and not errors and set(parsed)==set(range(198,204))
 for r in fresh:r['primary_source_owners']=copy.deepcopy(it['owners']);r['document_source_title']=it['heading']
 selected={r['id']:r for r in fresh};expected=[selected.get(r['id'],r) for r in base];assert actual==expected,'Canonical output differs from actual finite native source replay or unchangedbaseIR'
 oldmarkers=[(r['id'],r['image_placeholder_count'],[b for b in r['ordered_blocks'] if b['kind']=='image_placeholder']) for r in base];newmarkers=[(r['id'],r['image_placeholder_count'],[b for b in r['ordered_blocks'] if b['kind']=='image_placeholder']) for r in actual];assert oldmarkers==newmarkers
 outputs=native_document.outputs(expected);assert all((ROOT/'derived'/name).read_bytes()==data for name,data in outputs.items());assert len(actual)==636 and len(selected)==6
 for r,z in zip(base,actual):
  if r['id']in selected:assert z['superseded_detector_diagnostics']['original_record_fields']=={k:r[k] for k in ['tables','ordered_blocks','text','ordering','pdf_qualification']}
  else:assert r==z
 assert before=={q.relative_to(ROOT).as_posix():sha(q) for q in files},'Read-only replay modified evidence';print(json.dumps({'passed':True,'actual_native_content_pages_parsed':sorted(set(parsed)),'full224or636content_reparse':False,'fresh_canonical_records':6,'unchanged_source_bound_IR_records':630,'prior7canonical_selections_unchanged':True,'canonical_record_and_csv_bytes_reproduced':True,'original5fields_exact_in_superseded_diagnostics':True,'image_positions_ownership_identical':True,'image_placeholders':sum(r['image_placeholder_count'] for r in actual),'network_image_decode_extract_render_OCR_calls':0,'readonly_evidence_unchanged':True,'derived_records_sha256':sha(ROOT/'derived/records.jsonl'),'derived_csv_sha256':sha(ROOT/'derived/records.csv'),'scope_dimensions':sto_appendix_b.summary(fresh)},indent=2,sort_keys=True))
if __name__=='__main__':main()
