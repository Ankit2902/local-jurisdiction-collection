"""Read-only publisher PDF structural and bounded text checks; requires pypdf."""
import argparse,hashlib,json,platform
from pathlib import Path
from pypdf import PdfReader
p=argparse.ArgumentParser();p.add_argument('pdf',type=Path);p.add_argument('--pages',type=int,default=3);a=p.parse_args();data=a.pdf.read_bytes();assert data.startswith(b'%PDF-'),'Not a PDF';r=PdfReader(a.pdf)
result={'file':a.pdf.name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'pages':len(r.pages),'metadata':{str(k):str(v) for k,v in (r.metadata or {}).items()},'selected_pages':[{'page':i+1,'text':r.pages[i].extract_text()} for i in range(min(a.pages,len(r.pages)))],'inspection_scope':'PDF container and first selected pages only; full code section completeness/currency not inferred','python':platform.python_version()}
out=a.pdf.with_name('publisher-pdf-inspection.json');out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='selected_pages'},indent=2))
