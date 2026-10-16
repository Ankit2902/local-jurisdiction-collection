#!/usr/bin/env python3
"""Seal the retained, reviewed pilot after running test_civicplus separately."""
import hashlib,json,platform,re,sys
from pathlib import Path
from datetime import datetime,timezone
import pdfplumber,requests,bs4,json5
ROOT=Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def main():
 log=ROOT/'test-results.txt';text=log.read_text()
 if not re.search(r'Ran 15 tests in .*?\n\nOK\s*$',text,re.S): raise RuntimeError('Run complete successful 15-test suite before sealing report.')
 reviewed=[
  {'jurisdiction':'portland-me','document':'Chapter 13','pages':[2,3],'images':['portland-ch13-p2.png','portland-ch13-p3.png'],'result':'pass_bounded_spotcheck','checks':['Page 2 bold Sec.13-2 Definitions is emitted once, despite page3 Sec.13-2/Rev running header.','Applicant definition continues from page2 ending if he to page3 is receiving general assistance at the time of application; both belong to one 13-2 record.','Application form, Back bills, Basic necessities and Dwelling unit remain in definition body; header removal did not remove definitions.'],'limits':'Full p2-p7 definition transcription was not manually compared character by character.'},
  {'jurisdiction':'portland-me','document':'Chapter 13','pages':[37],'images':['portland-ch13-p37.png'],'result':'pass_layout_spotcheck_requires_semantic_review','checks':['Rent table has Bedrooms, Unheated Weekly/Monthly and Heated Weekly/Monthly. Row0 values 100/431/112/481 match retained cells.','Food table starts Household1, Daily $3.70, Weekly $26.00, Monthly $111.00.','Exported table preserves grouped cells using fixed-spacing pre blocks; table body lines are not emitted twice.'],'limits':'Grouped subcolumn semantics and table continuation onto following pages remain unresolved.'},
  {'jurisdiction':'portland-me','document':'Chapter 13','pages':[48],'images':['portland-ch13-p48.png'],'result':'manual_review_required','checks':['Image/mask present in source; visible property-tax clause includes abatement process language not completely represented by native extraction.','Image box and ordered IMAGE placeholder retained; mixed_text_image explicitly unresolved.'],'limits':'OCR/transcription was not performed. No page48 completion claim.'},
  {'jurisdiction':'rockland-me','document':'Chapter 1','pages':[2,3],'images':['rockland-ch1-p2.png','rockland-ch1-p3.png'],'result':'pass_bounded_spotcheck_markers_require_review','checks':['Adopting ordinance introductory text retained.','Headings Adoption of Code and Official Copies Kept by City Clerk have no trailing1 in section_name.','Raw native 0.67pt glyph1 occurs near both headings; retained as source text/coordinates and flagged for review.','Definition sequence continues from Q. Statutes on page2 to R. Street through W. Year on page3 within one section1-102.','Bottom-right Ch.1,Sec.1-101/1-103 running locators removed by position and retained in ledger.'],'limits':'Microscopic glyph significance is unresolved; no guessed footnote deletion/normalization.'},
  {'jurisdiction':'rockland-me','document':'City Charter','pages':[3],'images':['rockland-charter-p3.png'],'result':'source_overlap_review_required','checks':['Charter uses numbers101/102/103 then201 onward, independent publication identity and printed TOC.','White boxed Sec.101 running locator visibly overlays part of final Mayor paragraph.','Precise baseline extraction separates locator glyphs from underlying mayor who text; locator removal is recorded.','Source overlap remains unresolved even though native text can be recovered.'],'limits':'Only page3 was visually reviewed; other flagged overlapping/off-page locator positions were detected automatically.'}
 ]
 for check in reviewed:
  check['reviewer']='Codex agent visual inspection of Poppler page renderings and extracted records';check['reviewed_at']='2026-10-15'
  check['rendered_evidence']=[{'path':'evidence/rendered/'+n,'sha256':sha(ROOT/'evidence/rendered'/n)} for n in check.pop('images')]
 write(ROOT/'SOURCE-COMPARISON.json',{'manual_review_kind':'agent visual inspection; not human signoff','coverage':'listed source pages only','comparisons':reviewed})
 reports=[]
 for slug in ['portland-me','rockland-me']:
  package=ROOT/'samples'/slug;auto=read(package/'validation-report.json');inv=read(package/'inventory.json');acq=read(package/'acquisition.json')
  block_files=list((package/'layout').rglob('blocks.jsonl'));tables=0
  for f in block_files: tables+=sum(json.loads(x)['kind']=='table' for x in f.read_text().splitlines())
  methods=[{'method':'native_pdf_layout_parser','status':'bounded_regression_pass_with_manual_review_gates','documents':[d['document_id'] for d in auto['documents']],'full_corpus_validated':False,'pages_parsed':sum(d['pages'] for d in auto['documents']),'records':auto['record_count'],'tables_retained':tables}, {'method':'offline_snapshot_replay_and_package_integrity','status':'passed','tests':'test_civicplus.py','log_sha256':sha(log),'tests_count':15,'interrupted_resume':'One Rockland document first, then restore second acquisition; clean and resumed ordered record/node/provenance/disposition bytes equal.'}]
  if slug=='portland-me':
   methods += [{'method':'official_http_index_and_pdf','status':'passed_bounded','inventory_documents':44,'acquired_documents':1,'source_root':inv['root_url'],'tls_verification':True},{'method':'ordinary_browser_rendered_widget','status':'passed_inventory_labels','widget_id':'8e1b032d-9c35-40d2-8687-17e08b2f1ff5','labels':44,'response_headers_available':False}]
  else:
   methods += [{'method':'direct_http','status':'blocked_in_current_environment','observed_status':404,'body_bytes':0,'evidence':['evidence/rockland-index.response.json','evidence/rockland-ch1.response.json','evidence/rockland-charter.response.json'],'next_action':'Use ordinary supported browser capture/download and tested import-browser-pdf, or resolve transport configuration with operator. Never infer removed/migrated publication from this response.'},{'method':'ordinary_codex_iab_browser','status':'passed_bounded_inventory_and_download','source_root':inv['root_url'],'inventory_documents':21,'acquired_documents':2,'response_headers_available':False,'portable_automated_browser_transport_qualified':False}]
  report={'jurisdiction_slug':slug,'generated_at':datetime.now(timezone.utc).isoformat(),'parser_version':'civicplus-layout-pilot-1.0','parser_sha256':sha(ROOT/'civicplus.py'),'status':'validated_bounded_subset_with_explicit_review_conditions','corpus_complete':False,'release_ready_full_corpus':False,'methods':methods,'automated_validation':auto,'source_visual_comparison':[x for x in reviewed if x['jurisdiction']==slug],'source_evidence':[{'node_id':i,'raw_path':a['raw_path'],'sha256':a['sha256'],'source_url':next(d['url'] for d in inv['documents'] if d['node_id']==i),'transport':a['receipt']['transport']} for i,a in acq.items()],'test_command':'python -m unittest -v test_civicplus','replay_commands':['python civicplus.py parse --package samples/'+slug,'python civicplus.py verify --package samples/'+slug],'blockers':['Full document and substantive-node coverage is not established.','Resolve all reported OCR/mixed, table semantics, source-overlap, microscopic marker and unnumbered-body review conditions before downstream use.','Retain and compare source versions/inventory at full-run start/end; do not equate retrieval date with code currency.'],'runtime':{'python':platform.python_version(),'pdfplumber':pdfplumber.__version__,'requests':requests.__version__,'beautifulsoup4':bs4.__version__,'json5':json5.__version__}}
  write(package/'VALIDATION-REPORT.json',report);reports.append(report)
  manifest=read(package/'run-manifest.json');manifest['artifact_hashes']={str(p.relative_to(package)):sha(p) for p in sorted(package.rglob('*')) if p.is_file() and p.name!='run-manifest.json'};write(package/'run-manifest.json',manifest)
 write(ROOT/'VALIDATION-REPORT.json',{'scope':'CivicPlus bounded official-PDF qualification; no full-corpus collection/import','corpus_complete':False,'jurisdictions':reports,'test_log':{'path':'test-results.txt','sha256':sha(log)},'visual_qa':'SOURCE-COMPARISON.json','test_count':15})
 hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='ARTIFACT-HASHES.json'}
 write(ROOT/'ARTIFACT-HASHES.json',hashes)
 print(json.dumps({'reports':len(reports),'tests':15,'artifacts_hashed':len(hashes),'corpus_complete':False}))
if __name__=='__main__':main()
