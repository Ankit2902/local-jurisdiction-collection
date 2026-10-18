import contextlib,hashlib,io,json,pathlib,socket,sys
from unittest.mock import patch
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parent
prior=ROOT.parent/'infrastructure-native-default-integration-candidate-v1'
rows=[json.loads(x) for x in (prior/'final-default-native/records.jsonl').read_text().splitlines()]
r=rows[54];raw=prior/'final-default-native'/r['raw_ref'];data=raw.read_bytes();assert hashlib.sha256(data).hexdigest()==r['raw_sha256']
calls=[];original=PDFStream.get_data

def deny(name):
 def fail(*a,**k):calls.append(name);raise AssertionError('Forbidden '+name)
 return fail

def stream(s):
 if getattr(s.attrs.get('Subtype'),'name',None)=='Image' or ('W' in s.attrs and 'H' in s.attrs):return deny('PDFStream image data')()
 return original(s)
with contextlib.ExitStack() as stack:
 stack.enter_context(patch.object(PDFStream,'get_data',stream))
 for obj,names in [(Image,['open']),(socket,['socket']),(pypdfium2.PdfImage,['get_bitmap','extract','get_data']),(pypdfium2.PdfPage,['render']),(pdfplumber.page.Page,['to_image'])]:
  for name in names:
   if hasattr(obj,name):stack.enter_context(patch.object(obj,name,deny(name)))
 with pdfplumber.open(io.BytesIO(data)) as p:
  assert len(p.pages)==62
  page=p.pages[25];chars=page.chars;blocks=[]
  for f in r['source_fragments']:
   b=f['block'];box=b['bbox'];selected=[c for c in chars if box[0]-.2<=(c['x0']+c['x1'])/2<=box[2]+.2 and box[1]-.2<=(c['top']+c['bottom'])/2<=box[3]+.2]
   assert ''.join(''.join(c['text'] for c in selected).split())==''.join(b['text'].split()),(f['block_index'],''.join(c['text'] for c in selected))
   blocks.append({'page':26,'block_index':f['block_index'],'bbox':box,'text':b['text'],'glyphs':[{k:c.get(k) for k in ['text','fontname','size','x0','x1','top','bottom','stroking_color','non_stroking_color']} for c in selected]})
 witness={'schema_version':1,'source_sha256':r['raw_sha256'],'source_url':r['source_document_url'],'record_id':r['id'],'physical_page':26,'blocks':blocks,'image_operations':0,'native_text_only':True}
 (ROOT/'source/native-page26-glyph-witness.json').write_text(json.dumps(witness,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 (ROOT/'source/selected-record.json').write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 (ROOT/'source/source-binding.json').write_text(json.dumps({'prior_full_packet_manifest_sha256':hashlib.sha256((prior/'MANIFEST.json').read_bytes()).hexdigest(),'records_jsonl_sha256':hashlib.sha256((prior/'final-default-native/records.jsonl').read_bytes()).hexdigest(),'source_pdf_sha256':hashlib.sha256(data).hexdigest(),'source_pdf_bytes':len(data),'record_id':r['id'],'captured_native_physical_pages':[26],'full_native_reparse':False,'forbidden_calls':calls,'scope':'One bounded PDF text/glyph page; no visual inspection/rendering/decoding/extraction/OCR'},indent=2)+'\n')
assert not calls
print(json.dumps({'native_page':26,'blocks':len(blocks),'glyphs':sum(len(x['glyphs']) for x in blocks),'forbidden_calls':calls,'fonts':sorted({g['fontname'] for b in blocks for g in b['glyphs']})}))
