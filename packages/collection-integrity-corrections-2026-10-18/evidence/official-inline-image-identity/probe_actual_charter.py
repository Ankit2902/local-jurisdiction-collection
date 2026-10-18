#!/usr/bin/env python3
"""Full71-page retainednative replay under independentprocess image/network tripwires."""
import argparse,contextlib,hashlib,io,json,pathlib,socket,subprocess,sys
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--runtime',type=pathlib.Path,required=True);p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();sys.path.insert(0,str(a.runtime.resolve()));import pdf_structure,pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
item=json.loads((a.source/'item.json').read_text());config=json.loads((a.source/'config.json').read_text());data=(a.source/item['raw_ref']).read_bytes();original=PDFStream.get_data;calls=[];guards=[]
def no_image_data(stream):
 attrs=stream.attrs;sub=attrs.get('Subtype');name=getattr(sub,'name',None)
 if name=='Image'or('W'in attrs and'H'in attrs):calls.append('PDFStream.image.get_data');raise AssertionError('Forbidden image stream decoding')
 return original(stream)
def forbidden(name):
 def fail(*args,**kwargs):calls.append(name);raise AssertionError('Forbidden '+name)
 return fail
with contextlib.ExitStack()as stack:
 stack.enter_context(patch.object(PDFStream,'get_data',no_image_data));guards.append('PDFStream.get_data image-only guard; content/font text streams permitted')
 for obj,names in [(pypdfium2.PdfPage,['render']),(pypdfium2.PdfImage,['get_bitmap','extract','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open']),(socket,['socket']),(subprocess,['run','Popen'])]:
  for name in names:
   if hasattr(obj,name):stack.enter_context(patch.object(obj,name,forbidden(str(obj)+'.'+name)));guards.append(str(obj)+'.'+name)
 records,dispositions=pdf_structure.pages(data,item,config)
 assert not calls
 native=[]
 with pdfplumber.open(io.BytesIO(data))as document:
  for n,page in enumerate(document.pages):
   for i,image in enumerate(page.images):
    stream=image.get('stream');objid=getattr(stream,'objid',None)
    native.append({'physical_page':n+1,'source_image_ordinal':i+1,'object_id':objid,'source_name_is_engine_generated':objid is None,'named_source_resource':image.get('name')if objid is not None else None,'bbox':pdf_structure.box(image)})
 assert not calls
assert len(records)==71 and not dispositions
a.out.mkdir();rows=b''.join(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()+b'\n'for r in records);(a.out/'records.jsonl').write_bytes(rows);report={'schema':1,'runtime_pdf_sha256':hashlib.sha256((a.runtime/'pdf_structure.py').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(data).hexdigest(),'pages':len(records),'records_sha256':hashlib.sha256(rows).hexdigest(),'table_count':sum(len(r['tables'])for r in records),'image_placeholder_count':sum(r['image_placeholder_count']for r in records),'source_images':native,'forbidden_calls':calls,'guards':guards,'scope':'Whole71pageCharternativeoriginal only. ExistingPDF text/table qualification preserved; no imagepixels/data/render/OCR ornetwork.'};(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['source_images','guards']},indent=2))
