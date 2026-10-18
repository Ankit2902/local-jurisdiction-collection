"""Bounded original PDF catalog/font inspection only; no image/pixel APIs."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,socket,platform
from pathlib import Path
from unittest.mock import patch,PropertyMock
from pypdf import PdfReader
from pypdf._page import PageObject
from PIL import Image
B=Path(__file__).resolve().parent;f=B/'candidate/fixtures/cleveland-frontage-printable-source';a=json.loads((f/'asset.json').read_text());path=f/a['file'];calls=[]
def no(*a,**k):calls.append('forbidden_network_image');raise AssertionError(calls[-1])
with patch.object(Image,'open',no),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=no),patch.object(socket.socket,'connect',no):
 reader=PdfReader(path);catalog=reader.trailer['/Root'];page=reader.pages[0];names=catalog.get('/Names');name_keys=list(names.get_object()) if names else []
 evidence={'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'raw_bytes':path.stat().st_size,'physical_pages':len(reader.pages),'catalog_keys':list(catalog),'names_dictionary_keys':name_keys,'named_destinations':{str(k):{'type':str(v.get('/Type')),'printed_legal_heading':False} for k,v in reader.named_destinations.items()},'has_struct_tree':bool(catalog.get('/StructTreeRoot')),'has_outlines':bool(catalog.get('/Outlines')),'has_page_labels':bool(catalog.get('/PageLabels')),'has_annotations':bool(page.get('/Annots')),'has_embedded_files':bool(names and names.get_object().get('/EmbeddedFiles')),'page_box':[float(x) for x in page.mediabox],'page_rotation':page.get('/Rotate'),'metadata':dict(reader.metadata or {}),'fonts':{str(k):{str(x):str(v.get_object().get(x)) for x in ['/BaseFont','/Subtype','/Encoding']} for k,v in page['/Resources']['/Font'].get_object().items()},'forbidden_calls':calls,'source_scope_basis':'Original file has one full closed grid plus trailing source note, linked explicitly as printable PDF by §348.02. Inner a.-h. labels remain table rows. No physical-page-to-section inference.','method':'pypdf catalog/page/font metadata only; existing fully qualified native glyph/grid IR supplies text. No rendering, OCR, image streams or separate image files.','python':sys.version,'platform':platform.platform(),'pypdf_version':__import__('pypdf').__version__,'inspection_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
assert evidence['physical_pages']==1 and not any(evidence[k] for k in ['has_struct_tree','has_outlines','has_page_labels','has_annotations','has_embedded_files']) and not calls
(B/'source-inspection.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2))
