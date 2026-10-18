import os,sys,json,socket
from pathlib import Path
root=Path(os.environ['COLLECTION_QA_GUARD_LOG']);root.mkdir(parents=True,exist_ok=True)
def event(kind,operation):
 with (root/(str(os.getpid())+'.jsonl')).open('a') as stream:stream.write(json.dumps({'kind':kind,'operation':operation,'pid':os.getpid(),'argv':sys.argv})+'\n')
def forbid(name):
 def denied(*a,**k):
  event('forbidden_call',name)
  raise RuntimeError('QA_FORBIDDEN:'+name)
 return denied
socket.socket.connect=forbid('socket.connect');socket.socket.connect_ex=forbid('socket.connect_ex');socket.create_connection=forbid('socket.create_connection')
from PIL import Image
for name in ['open','frombytes','frombuffer']:
 setattr(Image,name,forbid('PIL.Image.'+name))
import fitz
fitz.Page.get_pixmap=forbid('fitz.Page.get_pixmap');fitz.Document.extract_image=forbid('fitz.Document.extract_image')
import pdfplumber
pdfplumber.page.Page.to_image=forbid('pdfplumber.Page.to_image')
import pypdfium2
pypdfium2.PdfPage.render=forbid('pdfium.PdfPage.render')
event('guard_loaded','socket_and_named_image_apis')
