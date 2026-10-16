#!/usr/bin/env python3
"""Build the handoff index from final evidence, without network access."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
h=read('ecode360/HEADED-VALIDATION.json'); reviewed=read('independent-review/REVIEW.json'); reviewers={x['slug']:x for x in reviewed['cities']}
downloads={x['slug']:x for x in read('publisher-downloads/DOWNLOAD-VALIDATION.json')['results']}
rows=[]
for x in h['jurisdictions']:
 r=reviewers[x['slug']];pdf=x['publisher_download']
 assert x['source_sha256']==r['raw_source_sha256'], 'Newest selected source must match independently reviewed bytes'
 assert x['output_records']==r['output_records']
 rows.append({'slug':x['slug'],'jurisdiction':x['jurisdiction'],'source_url':x['source_url'],'primary_method':x['best_method_status'],'sample_records':x['output_records'],'publisher_edition':x['edition'],'source_sha256':x['source_sha256'],'independently_reviewed_source_bytes_equal':True,'csv_json_exports':'ecode360/'+x['pipeline_report_path'].rsplit('/',1)[0]+'/exports','pipeline_report':'ecode360/'+x['pipeline_report_path'],'acquisition_receipt':'ecode360/'+x['pipeline_acquisition_receipt'],'publisher_pdf_acquired':pdf['file_acquired'],'publisher_pdf_status':pdf['status'],'publisher_pdf_selected_citation':pdf.get('selected_citations'),'publisher_pdf_file':'ecode360/'+pdf['path'] if pdf.get('path') else None,'publisher_pdf_sha256':pdf.get('sha256'),'publisher_pdf_validation_report':'publisher-downloads/DOWNLOAD-VALIDATION.json','publisher_pdf_semantic_status':downloads[x['slug']].get('semantic_text_preservation_status', downloads[x['slug']].get('download_status')),'full_publication_inventory_verified':False,'whole_corpus_verified':False,'next_action':x['next_action'],'limitations':x['blockers']})
assert len(rows)==14 and sum(x['sample_records'] for x in rows)==134 and sum(x['publisher_pdf_acquired'] for x in rows)==13
result={'created_at':datetime.now(timezone.utc).isoformat(),'jurisdictions':14,'bounded_standalone_primary_method_passes':14,'primary_sample_records':134,'publisher_pdf_files_acquired':13,'pdf_and_dom_samples_overlap_do_not_sum_as_unique_provisions':True,'source_review_scope':'Fresh original14 sources independently checked. Selected later receipts have byte-identical legal source to reviewed sources.','whole_corpus_verified':False,'rows':rows}
(ROOT/'SOURCE-MATRIX.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['# eCode360 standalone acquisition results','','All 14 previously unqualified primary-code routes passed a bounded fresh headed acquisition and CSV/JSON export. Thirteen also produced an actual selected-section publisher PDF without login. Santa Clara had no available Download control in the tested anonymous publication session.','','These are method qualifications, not completed corpora. The PDF samples overlap the 134 DOM provisions; do not count them as additional unique provisions. PDF semantic/layout results are separate in [the download review](publisher-downloads/DOWNLOAD-VALIDATION.json).','','| Jurisdiction | Fresh DOM → CSV/JSON | Records | Actual publisher PDF | Publisher edition marker |','|---|---|---:|---|---|']
for x in rows:
 pdf=f"[Downloaded]({x['publisher_pdf_file']})" if x['publisher_pdf_acquired'] else 'Download control unavailable'
 if x['slug']=='san-leandro-ca':pdf+='; map review required'
 lines.append(f"| [{x['jurisdiction']}]({x['source_url']}) | [Passed]({x['pipeline_report']}) | {x['sample_records']} | {pdf} | {x['publisher_edition']['currency_raw']} |")
lines += ['','The edition column is the publisher’s code-date marker, not a guarantee that every uncodified amendment is included. Customer, code ID and date are retained together in the JSON matrix and receipts. Official city-to-publisher discovery is inherited from the reviewed earlier inventory; this pass did not recrawl every city portal.','','## Technical handoff','','- [Primary acquisition, parser and export runbook](ecode360/README.md)','- [Actual PDF download, local intake and selected-section parsing](publisher-downloads/README.md)','- [Independent 14-source / 134-provision semantic review](independent-review/REVIEW.json)','- [Runtime and rate-limit guard review](runtime-review/RUNTIME-REVIEW.json)','- [Machine-readable per-city matrix](SOURCE-MATRIX.json)','','A full collection still needs publication-wide enumeration, coverage/disposition reconciliation, attachment handling and full-run edition checks. Headless and direct HTTP paths were not requalified.','']
(ROOT/'SOURCE-MATRIX.md').write_text('\n'.join(lines))
print('14 city matrix built;134 records;13 actual PDFs; independent source hashes match.')
