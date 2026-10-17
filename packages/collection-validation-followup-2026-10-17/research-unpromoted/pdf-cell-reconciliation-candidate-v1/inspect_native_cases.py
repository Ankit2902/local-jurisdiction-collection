"""Read-only native PDF glyph/font/word geometry inspection. No image APIs."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,io,socket
from pathlib import Path
import pdfplumber,pypdfium2
from pypdf import PdfReader
base=Path(__file__).resolve().parent;project=base.parents[2]
def deny(*a,**k):raise AssertionError('No network')
socket.socket.connect=deny;socket.create_connection=deny
sources={
 'fire':('outputs/collection-readiness-next-2026-10-17/fire-final-retained-driver/source/raw/143515c165dfca752208.bin',[14]),
 'cleveland':('outputs/collection-readiness-next-2026-10-17/official-final-pdf-driver/cleveland-real-cell-study/native.pdf',[1]),
 'infrastructure':('outputs/collection-readiness-next-2026-10-17/encodeplus/pdf-candidate-infrastructure-caf641e0/source.pdf',[2,3,6,46])}
ledger=json.loads((project/'outputs/collection-readiness-next-2026-10-17/pdf-concrete-cell-review-ledger.json').read_text());reports=[]
for family,(relative,pages) in sources.items():
 path=project/relative;raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();miner=pdfplumber.open(io.BytesIO(raw));ium=pypdfium2.PdfDocument(raw);reader=PdfReader(io.BytesIO(raw));result={'family':family,'source':relative,'sha256':digest,'pages':[]}
 for physical in pages:
  page=miner.pages[physical-1].dedupe_chars(tolerance=.5);p=ium[physical-1];tp=p.get_textpage();text=tp.get_text_range();chars=[]
  for index,ch in enumerate(text):
   if ord(ch)<32 and not ch.isspace():
    x0,y0,x1,y1=tp.get_charbox(index);bbox=[x0,float(page.height)-y1,x1,float(page.height)-y0];cx=(bbox[0]+bbox[2])/2;cy=(bbox[1]+bbox[3])/2
    near=[{k:c.get(k) for k in ['text','x0','top','x1','bottom','fontname','size','adv','matrix']} for c in page.chars if c['x0']-1<=cx<=c['x1']+1 and c['top']-1<=cy<=c['bottom']+1]
    chars.append({'index':index,'codepoint':ord(ch),'context':text[max(0,index-30):index+30],'bbox':bbox,'pdfminer_same_position':near})
  words=page.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size']);cases=[]
  for case in ledger['cases']:
   if case['native_sha256']!=digest or case['physical_page']!=physical:continue
   b=case['bbox'];cross=[w for w in words if w['bottom']>b[1] and w['top']<b[3] and any(w['x0']<x<w['x1'] for x in [b[0],b[2]])]
   row=[w for w in words if b[1]-.5<=(w['top']+w['bottom'])/2<=b[3]+.5]
   cases.append({'cell_id':case['cell_id'],'bbox':b,'source_text':case['source_extractable_cell_text'],'pdfium_text':case['independent_pdfium_cell_text'],'cross_boundary_source_words':cross,'complete_source_row_words':row,'source_row_text':' '.join(w['text'] for w in sorted(row,key=lambda w:w['x0']))})
  fonts=[]
  for name,ref in reader.pages[physical-1]['/Resources'].get('/Font',{}).items():
   font=ref.get_object();cm=font.get('/ToUnicode');fonts.append({'resource_name':name,'base_font':str(font.get('/BaseFont')),'encoding':str(font.get('/Encoding')),'subtype':str(font.get('/Subtype')),'to_unicode':cm.get_object().get_data().decode('latin1') if cm else None})
  result['pages'].append({'physical_page':physical,'width':float(page.width),'height':float(page.height),'nonwhitespace_control_glyphs':chars,'fonts':fonts,'cases':cases})
  tp.close();p.close();page.close()
 miner.close();ium.close();assert path.read_bytes()==raw;reports.append(result)
(base/'native-glyph-geometry-inspection.json').write_text(json.dumps({'network_requests':0,'image_operations':0,'source_files_unchanged':True,'reports':reports},indent=2)+'\n')
for result in reports:
 print(result['family'])
 for p in result['pages']:
  print(' page',p['physical_page'],'control glyphs',len(p['nonwhitespace_control_glyphs']),'cases',len(p['cases']))
  for c in p['nonwhitespace_control_glyphs']:print(repr(c['context']),c['bbox'],c['pdfminer_same_position'])
