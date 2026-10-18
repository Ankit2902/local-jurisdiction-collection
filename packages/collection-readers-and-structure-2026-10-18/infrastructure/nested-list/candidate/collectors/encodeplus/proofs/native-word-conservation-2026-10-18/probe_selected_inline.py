"""Parse only source physical pages52/57/63; logical parser pages1/2/3 explicitly mapped.
No normalized full-publication proof: this is a bounded native metadata smoke.
"""
import argparse,contextlib,hashlib,importlib.util,io,json,socket,subprocess,sys
from pathlib import Path
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--parser',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'candidate'))
spec=importlib.util.spec_from_file_location('collectors.encodeplus._selected_ep_parser',a.parser);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
selected=[52,57,63];raw=(root/'actual-charter/source.pdf').read_bytes();item=json.loads((root/'actual-charter/item.json').read_text());config=json.loads((root/'actual-charter/config.json').read_text());real_open=pdfplumber.open;real_native=pypdfium2.PdfDocument;real_get=PDFStream.get_data;calls=[]
class SelectedPlumber:
 def __init__(self,data):self.document=real_open(data);self.pages=[self.document.pages[i-1] for i in selected]
 def close(self):self.document.close()
class SelectedNative:
 def __init__(self,data):self.document=real_native(data)
 def __len__(self):return len(selected)
 def __getitem__(self,index):return self.document[selected[index]-1]
 def close(self):self.document.close()
def image_guard(stream):
 subtype=getattr(stream.attrs.get('Subtype'),'name',None)
 if subtype=='Image' or ('W' in stream.attrs and 'H' in stream.attrs):calls.append('image_stream.get_data');raise AssertionError('Image decode forbidden')
 return real_get(stream)
def forbidden(name):
 def fail(*args,**kwargs):calls.append(name);raise AssertionError(name+' forbidden')
 return fail
with contextlib.ExitStack() as stack:
 stack.enter_context(patch.object(pdfplumber,'open',SelectedPlumber));stack.enter_context(patch.object(pypdfium2,'PdfDocument',SelectedNative));stack.enter_context(patch.object(PDFStream,'get_data',image_guard))
 for obj,names in [(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['get_bitmap','extract','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open']),(socket,['socket']),(subprocess,['run','Popen'])]:
  for name in names:
   if hasattr(obj,name):stack.enter_context(patch.object(obj,name,forbidden(name)))
 records,dispositions=module.pages(raw,item,config)
 metadata=[]
 with real_open(io.BytesIO(raw)) as document:
  for physical in selected:
   page=document.pages[physical-1]
   for index,image in enumerate(page.images):
    objid=getattr(image.get('stream'),'objid',None);metadata.append({'physical_page':physical,'image_ordinal':index+1,'object_id':objid,'source_name':str(image.get('name','')) if objid is not None else None,'bbox':module.box(image)})
 assert not calls and not dispositions and len(records)==3
assert not a.out.exists();a.out.mkdir()
rows=b''.join(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()+b'\n' for r in records);(a.out/'records.jsonl').write_bytes(rows)
report={'scope':'Bounded three-physical-page metadata/parser smoke; logical parser page indices mapped explicitly, not wholepublication output.','selected_physical_pages':selected,'logical_to_physical':{str(i+1):n for i,n in enumerate(selected)},'source_sha256':hashlib.sha256(raw).hexdigest(),'parser_sha256':hashlib.sha256(a.parser.read_bytes()).hexdigest(),'records_sha256':hashlib.sha256(rows).hexdigest(),'source_image_metadata':metadata,'forbidden_calls':calls,'image_placeholders':sum(r['image_placeholder_count'] for r in records),'image_marker_count':sum(r['text'].count('[IMAGE]') for r in records),'table_count':sum(len(r['tables']) for r in records)}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
