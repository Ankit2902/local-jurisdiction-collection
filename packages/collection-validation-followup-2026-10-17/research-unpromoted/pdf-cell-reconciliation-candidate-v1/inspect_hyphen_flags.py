import sys
sys.dont_write_bytecode=True
import json,io
from pathlib import Path
import pdfplumber,pypdfium2
root=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');ledger=json.loads((root/'outputs/collection-readiness-next-2026-10-17/pdf-concrete-cell-review-ledger.json').read_text())
paths={'fire':root/'outputs/collection-readiness-next-2026-10-17/fire-final-retained-driver/source/raw/143515c165dfca752208.bin','cleveland':root/'outputs/collection-readiness-next-2026-10-17/official-final-pdf-driver/cleveland-real-cell-study/native.pdf'}
rows=[]
for family,path in paths.items():
 raw=path.read_bytes();pdf=pdfplumber.open(io.BytesIO(raw));doc=pypdfium2.PdfDocument(raw);n=13 if family=='fire' else 0;p=doc[n];tp=p.get_textpage();page=pdf.pages[n];flags=[]
 for ci in range(tp.count_chars()):
  unicode=pypdfium2.raw.FPDFText_GetUnicode(tp,ci);hyphen=pypdfium2.raw.FPDFText_IsHyphen(tp,ci)
  if hyphen or (unicode<32 and chr(unicode).isspace() is False):
   x0,y0,x1,y1=tp.get_charbox(ci);b=[x0,float(page.height)-y1,x1,float(page.height)-y0];cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2
   near=[{k:c.get(k) for k in ['text','x0','top','x1','bottom','fontname','size','adv']} for c in page.chars if c['x0']-.5<=cx<=c['x1']+.5 and c['top']-.5<=cy<=c['bottom']+.5]
   flags.append({'char_index':ci,'unicode':unicode,'is_hyphen':hyphen,'is_generated':pypdfium2.raw.FPDFText_IsGenerated(tp,ci),'bbox':b,'pdfminer':near,'range_character':tp.get_text_range(ci,1),'range_context':tp.get_text_range(max(0,ci-10),22)})
 case=next(c for c in ledger['cases'] if c['native_sha256']==__import__('hashlib').sha256(raw).hexdigest())
 b=case['bbox'];bounded=tp.get_text_bounded(b[0],float(page.height)-b[3],b[2],float(page.height)-b[1]);rows.append({'family':family,'flags':flags,'bounded':bounded,'bounded_codepoints':[(i,ord(c)) for i,c in enumerate(bounded) if ord(c)<32 and not c.isspace()]})
 tp.close();p.close();doc.close();pdf.close()
Path('hyphen-flag-inspection.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
