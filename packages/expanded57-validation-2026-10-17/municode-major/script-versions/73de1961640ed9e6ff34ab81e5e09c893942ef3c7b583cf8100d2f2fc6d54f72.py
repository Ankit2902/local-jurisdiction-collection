"""Offline PDF integrity/readability check; does not infer full-corpus currency."""
import hashlib,json,re
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
def run():
 results=[]
 for family in ['browser','recovery','http']:
  for p in (ROOT/family).glob('*/publisher-export.pdf'):
   r=PdfReader(p);text=r.pages[0].extract_text() or '';result={'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pdf_reader_opened':True,'page_count':len(r.pages),'first_page_nonempty':bool(text.strip()),'first_page_text_excerpt':text[:1000],'complete_corpus':False}
   receipt=json.loads((p.parent/'receipt.json').read_text());job=receipt.get('job',{});m=re.search(r'Supplement\s+(\d+)',job.get('Name',''),re.I);pdfm=re.search(r'SUPPLEMENT\s+NO\.?\s*(\d+)',text,re.I);result.update(api_job_name=job.get('Name'),api_banner=job.get('BannerText'),cover_supplement_matches_api=bool(m and pdfm and m[1]==pdfm[1]),edition_alignment_limit='Cover supplement label only; no full-body equivalence, currency, or completeness assertion')
   p.with_name('publisher-export.validation.json').write_text(json.dumps(result,indent=2));results.append(result)
 (ROOT/'publisher-download-verification.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if __name__=='__main__':run()
