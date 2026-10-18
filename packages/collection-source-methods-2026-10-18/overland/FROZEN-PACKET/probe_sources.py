import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,time
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H/'captured'))
from collectors.encodeplus.retained_native import guards
import pypdfium2,pdfplumber
rows=json.loads((H/'native-discovery/inventory.json').read_text());results=[]
for r in rows:
 path=H/'native-discovery'/(r['id']+'.bin');data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256'];indexes=([0,1,2,r['pages']//2,r['pages']-1]if r['pages']in[276,200]else[0,1]);start=time.monotonic();pages=[]
 with guards()as calls:
  doc=pypdfium2.PdfDocument(data)
  with pdfplumber.open(path)as pd:
   for i in indexes:
    p=doc[i];tp=p.get_textpage();text=tp.get_text_range();pp=pd.pages[i];words=pp.extract_words();images=pp.images
    pages.append({'physical_page':i+1,'pdfium_characters':tp.count_chars(),'pdfium_text':text,'pdfplumber_words':len(words),'pdfplumber_glyphs':len(pp.chars),'metadata_only_image_objects':len(images),'image_bboxes':[{'x0':im['x0'],'top':im['top'],'x1':im['x1'],'bottom':im['bottom'],'source_name':im.get('name'),'source_objid':getattr(im.get('stream'),'objid',None)}for im in images]});tp.close();p.close()
  doc.close()
 results.append({'id':r['id'],'source_sha256':r['sha256'],'physical_pages':r['pages'],'pages':pages,'elapsed_seconds':time.monotonic()-start,'forbidden_operations':calls,'scope':'Bounded source text/font/glyph and image-object metadata only; no image streams/render/OCR; not whole-publication qualification'})
(H/'source-probes.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps([{'id':r['id'],'pages':[(p['physical_page'],p['pdfplumber_words'],p['metadata_only_image_objects'])for p in r['pages']],'seconds':r['elapsed_seconds']}for r in results],indent=2))
