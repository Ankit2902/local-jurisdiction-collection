"""Selected source-font/glyph diagnosis only; no decoding or rendering images."""
import collections,hashlib,io,json,sys
from pathlib import Path
from unittest.mock import patch
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream,resolve1
from pypdf import PdfReader
BASE=Path(__file__).resolve().parent;ROOT=Path(sys.argv[1]);s=json.loads((BASE/'sources.json').read_text());data=(ROOT/s['native_source_path']).read_bytes();assert hashlib.sha256(data).hexdigest()==s['native_sha256'];out=[];original=PDFStream.get_data

def guarded(self,*a,**kw):
 assert getattr(self.get('Subtype'),'name',None)!='Image','Image stream decoded';return original(self,*a,**kw)
with patch.object(PDFStream,'get_data',guarded),patch.object(pypdfium2.PdfPage,'render',side_effect=AssertionError('Render forbidden')),patch('PIL.Image.open',side_effect=AssertionError('Image decoder forbidden')):
 pdf=pdfplumber.open(io.BytesIO(data));native=pypdfium2.PdfDocument(data);reader=PdfReader(io.BytesIO(data))
 for number in [4,634,1288]:
  p=pdf.pages[number-1];dedup=p.dedupe_chars(tolerance=.5);np=native[number-1];tp=np.get_textpage();text=tp.get_text_range();source=''.join(c['text'] for c in p.chars);select=[c for c in p.chars if any(ord(x) in [45,8226,61623] for x in c['text'])];glyphs=[]
  for c in select:
   if number==1288 and not any(ord(x)==61623 for x in c['text']):continue
   glyphs.append({k:c[k] for k in ['text','fontname','size','x0','top','x1','bottom','adv']})
  suspect=[]
  for i in range(tp.count_chars()):
   raw=pypdfium2.raw.FPDFText_GetUnicode(tp.raw,i)
   if raw in [2,45,8226,61623,65534,65535,65533]:suspect.append({'index':i,'unicode':raw,'is_hyphen':pypdfium2.raw.FPDFText_IsHyphen(tp.raw,i),'bbox':list(tp.get_charbox(i))})
  fonts={}
  for name,font in reader.pages[number-1]['/Resources'].get('/Font',{}).get_object().items():
   f=font.get_object();enc=f.get('/Encoding');enc=enc.get_object() if hasattr(enc,'get_object') else enc
   fonts[str(name)]={'BaseFont':str(f.get('/BaseFont')),'Subtype':str(f.get('/Subtype')),'Encoding':str(enc),'ToUnicode_present':'/ToUnicode' in f}
  out.append({'physical_page':number,'native_source_sha256':s['native_sha256'],'original_source_glyph_count':len(p.chars),'deduplicated_glyph_count':len(dedup.chars),'native_character_count':tp.count_chars(),'image_metadata_count':len(p.images),'source_vector_metadata_count':len(p.lines)+len(p.curves)+len(p.rects),'source_minus_count':source.count('-'),'native_minus_count':text.count('-'),'source_bullet_count':source.count('•'),'native_bullet_count':text.count('•'),'source_PUA_count':source.count('\uf0b7'),'native_PUA_count':text.count('\uf0b7'),'source_glyphs':glyphs,'native_special_glyphs':suspect,'page_font_metadata':fonts})
  tp.close();np.close();dedup.close();p.close()
 pdf.close();native.close()
print(json.dumps({'scope':'Three selected source pages only; no alias or whole-book qualification applied','source_native_sha256':s['native_sha256'],'pages':out,'image_stream_decode_calls':0,'image_render_calls':0},indent=2))
