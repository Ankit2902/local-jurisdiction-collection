"""Offline full-native normalization and read-only artifact verification.

No fetch path: the ordinary gated native_document collector remains the publisher
acquisition method. This command never invents a closing acquisition receipt.
"""
import sys
sys.dont_write_bytecode=True
import argparse,collections,contextlib,copy,hashlib,io,json,pathlib,platform,socket
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]))
from collectors.encodeplus import native_document as native
from collectors.encodeplus.collect import code_hashes,HERE,runtime_info
from collectors.encodeplus.documents import qualify_document
from collectors.encodeplus.util import atomic_bytes,atomic_json,digest,hash_json,read_json,validate_file

def validate_source(data,receipt,cfg):
 native.validate_config(cfg)
 assert digest(data)==cfg['expected_sha256'],'Wrong source edition/hash before native parsing'
 assert receipt.get('url')==receipt.get('final_url')==cfg['url'],'Actual receipt URL differs; catalog aliases are not acquisition evidence'
 assert receipt.get('http_status')==200 and not receipt.get('challenge') and not receipt.get('error'),'Source receipt not successful/unmitigated'
 assert receipt.get('sha256')==cfg['expected_sha256'] and receipt.get('bytes')==len(data),'Receipt/body hash or length mismatch'
 headers={str(k).lower():str(v)for k,v in receipt.get('headers',{}).items()};assert headers.get('content-type','').split(';',1)[0].strip().lower()=='application/pdf','Receipt does not identify a native PDF'
 expected=cfg.get('qualification',{}).get('observed_content_disposition')
 if expected:assert headers.get('content-disposition')==expected,'Native filename/identity header mismatch'
 return {'http_status':200,'url':receipt['url'],'final_url':receipt['final_url'],'content_type':headers['content-type'],'content_disposition':headers.get('content-disposition'),'source_observed_at':receipt.get('finished_at'),'catalog_alias_acquisition_verified':False}

@contextlib.contextmanager
def guards():
 """Allow text/glyph/source-stream access; refuse image pixel operations/network."""
 import urllib.request,pypdfium2,pdfplumber
 from PIL import Image
 from pdfminer.pdftypes import PDFStream
 from pypdf.generic import EncodedStreamObject,DecodedStreamObject
 calls=[]
 def deny(*a,**k):calls.append('forbidden_network_or_image_operation');raise AssertionError(calls[-1])
 def image_stream_guard(original):
  def guarded(stream,*a,**k):
   attrs=getattr(stream,'attrs',None)
   mapping=attrs if attrs is not None else stream
   subtype=mapping.get('Subtype',mapping.get('/Subtype'))
   width=any(k in mapping for k in ['W','Width','/W','/Width'])
   height=any(k in mapping for k in ['H','Height','/H','/Height'])
   if str(subtype).strip("/'").lower()=='image' or width and height:return deny()
   return original(stream,*a,**k)
  return guarded
 with contextlib.ExitStack()as stack:
  for obj,key in [(socket,'socket'),(urllib.request,'urlopen'),(native,'cached'),(Image,'open'),(Image,'frombytes'),(Image,'fromarray'),(pdfplumber.page.Page,'to_image'),(pypdfium2.PdfPage,'render')]:stack.enter_context(patch.object(obj,key,deny))
  for key in ['FPDFImageObj_GetBitmap','FPDFImageObj_GetRenderedBitmap','FPDFImageObj_GetImageDataDecoded','FPDFImageObj_GetImageDataRaw']:
   if hasattr(pypdfium2.raw,key):stack.enter_context(patch.object(pypdfium2.raw,key,deny))
  for cls in [PDFStream,EncodedStreamObject,DecodedStreamObject]:stack.enter_context(patch.object(cls,'get_data',image_stream_guard(cls.get_data)))
  yield calls
  assert not calls,'Forbidden operation was attempted'

def summarize(records,details,cfg,source_headers):
 native.validate_record_identity(records,details,cfg)
 for w in cfg.get('qualification',{}).get('native_identity_witnesses',[]):
  record=records[w['physical_page']-1];assert w['literal']in record['text'],'Native historical identity witness missing at page '+str(w['physical_page'])
 q=[r['pdf_qualification']for r in records];bad=lambda key:[r['physical_page']for r in records if not r['pdf_qualification'].get(key)]
 cid=[r['physical_page']for r in records if r['pdf_qualification'].get('undecoded_cid_literals')]
 return {'schema_version':1,'status':'retained_native_complete_semantics_unqualified','target':cfg['id'],'publication_identity':cfg['title'],'source_url':cfg['url'],'catalog_source_url':cfg.get('qualification',{}).get('catalog_source_url'),'source_headers':source_headers,'source_sha256':cfg['expected_sha256'],'native_document_complete':True,'source_page_traversal_complete':True,'physical_pages':cfg['expected_pages'],'normalized_record_count':len(records),'physical_page_sequence':[r['physical_page']for r in records],'source_word_count':sum(x['source_word_count']for x in q),'image_placeholders':sum(r['image_placeholder_count']for r in records),'word_ownership_failure_pages':bad('source_word_ownership_complete'),'source_word_character_failure_pages':bad('normalized_source_word_characters_agree'),'word_glyph_coverage_failure_pages':bad('source_words_cover_deduplicated_glyph_characters'),'independent_engine_failure_pages':bad('independent_text_engine_characters_agree'),'undecoded_CID_literal_pages':cid,'detected_table_cells':sum(x['detected_table_cells']for x in q),'independent_detected_cells_agree':sum(x['independent_table_cells_agree']for x in q),'source_printed_index_dimensions':details.get('source_printed_index_dimensions'),'native_identity_witnesses_verified':bool(cfg.get('qualification',{}).get('native_identity_witnesses')),'pdf_extractable_text_reconciled':details['pdf_extractable_text_reconciled'],'detected_table_cells_qualified':details['detected_table_cells_qualified'],'all_tables_detected':False,'source_logical_structure_qualified':False,'publication_text_complete':False,'publication_complete':False,'attachments_complete':False,'required_external_legal_dependencies_complete':False,'start_end_consistent':None,'closing_acquisition_performed':False,'edition_complete':False,'current_adopted_edition_qualified':False,'jurisdiction_complete':False,'image_policy':'[IMAGE]; exact original PDF retained, no image extraction/decoding/render/OCR','errors':[],'limits':['Historical source location/bytes and all native pages qualified; original single acquisition is not fabricated into opening/closing evidence.','Unresolved source CID literals and independent text disagreements remain; no source-backed font mappings are silently applied.','Detected cells and finite source index reconstruction do not establish whole book legal table/section/list/reading-order semantics.',('40th/POC-3460/2024 historical identity does not close current42nd/POC-3529/2026 edition or external dependency gaps.' if cfg['id']=='82-8fbdce15716d' else 'Pinned source identity/catalog effective-period label does not establish current adopted applicability, closing currency or external dependency completeness.')]}

def extract(cfg,input_path,receipt_path,out):
 input_path=pathlib.Path(input_path).resolve();receipt_path=pathlib.Path(receipt_path).resolve();out=pathlib.Path(out).resolve();assert not out.exists(),'Fresh output directory required; retained evidence is never overwritten'
 data=input_path.read_bytes();rb=receipt_path.read_bytes();receipt=json.loads(rb);headers=validate_source(data,receipt,cfg);versions=code_hashes();before=(digest(data),digest(rb));assert out not in input_path.parents and out not in receipt_path.parents,'Output cannot contain source inputs'
 with guards()as calls:
  integrity=qualify_document(data,cfg['url'],'application/pdf');assert integrity['pages']==cfg['expected_pages'],'Wrong physical page count'
  records,details=native.page_records(data,cfg,'raw/source.pdf');report=summarize(records,details,cfg,headers);outputs=native.outputs(records)
 assert before==(digest(input_path.read_bytes()),digest(receipt_path.read_bytes())),'Source input changed';assert versions==code_hashes(),'Collector source changed during retained normalization'
 out.mkdir(parents=True,exist_ok=False)
 for name,b in outputs.items():atomic_bytes(out/name,b)
 atomic_bytes(out/'raw/source.pdf',data);atomic_bytes(out/'raw/source.pdf.receipt.json',rb)
 for name,h in versions.items():atomic_bytes(out/'collector-source/collectors/encodeplus'/name,(HERE/name).read_bytes())
 atomic_bytes(out/'collector-source/collectors/__init__.py',b'')
 checkpoint={'schema_version':1,'mode':'offline_retained_native','config':cfg,'config_sha256':hash_json(cfg),'code_hashes':versions,'runtime':runtime_info(),'source':{'path':'raw/source.pdf','sha256':digest(data),'receipt_path':'raw/source.pdf.receipt.json','receipt_sha256':digest(rb)},'full_native_parser_executed_once':True,'normalized_records':len(records),'normalized_outputs':{name:digest(b)for name,b in outputs.items()},'details':details,'integrity':integrity,'report_sha256':hash_json(report),'forbidden_operations':calls,'closing_acquisition_performed':False}
 atomic_json(out/'config.json',cfg);atomic_json(out/'checkpoint.json',checkpoint);atomic_json(out/'coverage.json',report)
 return report

def verify(out):
 """Pure captured-IR/artifact replay; fresh extraction command reexecutes native parser."""
 out=pathlib.Path(out);s=read_json(out/'checkpoint.json');cfg=read_json(out/'config.json');assert s['mode']=='offline_retained_native' and cfg==s['config']and hash_json(cfg)==s['config_sha256'],'Retained config binding changed'
 assert s['code_hashes']==code_hashes(),'Use the exact captured collector source for read-only replay'
 for name,h in s['code_hashes'].items():validate_file(out,'collector-source/collectors/encodeplus/'+name,h)
 data=validate_file(out,s['source']['path'],s['source']['sha256']).read_bytes();rb=validate_file(out,s['source']['receipt_path'],s['source']['receipt_sha256']).read_bytes();headers=validate_source(data,json.loads(rb),cfg)
 for name,h in s['normalized_outputs'].items():validate_file(out,name,h)
 records=[json.loads(l)for l in(out/'records.jsonl').read_text().split('\n')if l];report=summarize(records,s['details'],cfg,headers);assert native.outputs(records)=={name:(out/name).read_bytes()for name in s['normalized_outputs']},'Normalized serialization changed'
 assert report==read_json(out/'coverage.json')and hash_json(report)==s['report_sha256'],'Coverage differs from complete captured IR';assert not s['forbidden_operations']and s['full_native_parser_executed_once']and not s['closing_acquisition_performed']
 return dict(report,artifact_replay_verified=True,native_parser_reexecuted=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=pathlib.Path);p.add_argument('--input',type=pathlib.Path);p.add_argument('--receipt',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path);p.add_argument('--verify',type=pathlib.Path);a=p.parse_args()
 if a.verify:r=verify(a.verify)
 else:
  if not all([a.config,a.input,a.receipt,a.out]):p.error('--config --input --receipt --out required')
  r=extract(read_json(a.config),a.input,a.receipt,a.out)
 print(json.dumps(r,indent=2));return 0 if r.get('native_document_complete')else 2
if __name__=='__main__':raise SystemExit(main())
