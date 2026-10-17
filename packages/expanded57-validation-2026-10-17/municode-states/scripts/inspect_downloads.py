#!/usr/bin/env python3
"""Offline inspect native PDF first pages and metadata; does not infer full-document currency."""
import pathlib,json,re,hashlib,argparse
from pypdf import PdfReader
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--render',action='store_true');a=p.parse_args()
for pdf in ROOT.glob('direct/*/publisher-export.pdf'):
 if not pdf.read_bytes().startswith(b'%PDF-'):continue
 r=PdfReader(pdf);texts=[page.extract_text() or '' for page in r.pages[:3]];meta=json.loads((pdf.parent/'receipt.json').read_text());job=meta.get('job',{});cover='\n'.join(texts)
 online=re.search(r'Supplement\s*(\d+)',job.get('Name',''),re.I);printed=re.search(r'SUPPLEMENT\s*(?:NO\.?)?\s*(\d+)',cover,re.I)
 mismatched=bool(online and printed and online.group(1)!=printed.group(1))
 report={'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'pdf_pages':len(r.pages),'pages_inspected':[1,2,3][:len(r.pages)],'first_pages_text':texts,'pdf_metadata':{str(k):str(v) for k,v in (r.metadata or {}).items()},'online_job_name':job.get('Name'),'online_banner':job.get('BannerText'),'online_supplement_number':online.group(1) if online else None,'first_pages_supplement_number':printed.group(1) if printed else None,'cover_version_mismatch':mismatched,'currency_alignment':'mismatch_or_unqualified' if mismatched else 'not_established','limitation':'Only first three PDF pages inspected. A transport success does not prove PDF/API currency equivalence; later PDF pages and update sheets not audited.'}
 (pdf.parent/'publisher-export-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps({'folder':str(pdf.parent.relative_to(ROOT)),'pages':len(r.pages),'currency_alignment':report['currency_alignment']}))
 if a.render:
  import pypdfium2 as p
  doc=p.PdfDocument(pdf);doc[0].render(scale=1).to_pil().save(pdf.parent/'publisher-export-first-page.png')
