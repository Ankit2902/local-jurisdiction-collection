"""Independent required-native PDF glyph/grid audit; image streams never decoded."""
import argparse,hashlib,io,json,re
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfReader
from pypdf.generic import StreamObject
from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams,LTChar,LTLine,LTRect,LTCurve
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import PDFStream

def sha(b):return hashlib.sha256(b).hexdigest()
def chars(s):return re.sub(r'\s+','',s).replace('[IMAGE]','')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('run',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 assets=json.loads((a.run/'assets.json').read_text());pages=[json.loads(x) for x in (a.run/'pdf-pages.jsonl').read_text().splitlines()];errors=[];results=[];opened_image_streams=[]
 original=PDFStream.get_data
 def no_image_data(self):
  if str(self.attrs.get('Subtype')) in ["/'Image'",'/Image','Image']:opened_image_streams.append(str(self.objid));raise AssertionError('Image stream decode forbidden')
  return original(self)
 class Device(PDFPageAggregator):
  def render_image(self,name,stream):self.images.append({'name':str(name),'ctm':list(self.ctm),'object_id':stream.objid});return
 def pypdf_no_images(self,*args,**kwargs):
  if self.get('/Subtype')=='/Image':raise AssertionError('Image stream decode forbidden')
  return saved_pypdf(self,*args,**kwargs)
 saved_pypdf=StreamObject.get_data
 with patch.object(PDFStream,'get_data',no_image_data),patch.object(StreamObject,'get_data',pypdf_no_images):
  for asset in assets:
   if not asset.get('required'):continue
   raw=(a.run/asset['file']).read_bytes();assert sha(raw)==asset['sha256'];reader=PdfReader(io.BytesIO(raw),strict=True);physical=list(PDFPage.get_pages(io.BytesIO(raw)));owned=[p for p in pages if p['owner_id']==asset['normalized_pdf_owner_id']];assert len(owned)==len(reader.pages)==len(physical)
   for index,(page,native,record) in enumerate(zip(reader.pages,physical,owned)):
    rm=PDFResourceManager();device=Device(rm,laparams=LAParams(all_texts=True));device.images=[];PDFPageInterpreter(rm,device).process_page(native);layout=device.get_result();glyphs=[];lines=[];filled_bands=[]
    def walk(obj):
     if isinstance(obj,LTChar):glyphs.append((obj.get_text(),obj.bbox))
     elif isinstance(obj,LTLine):lines.append((obj.x0,obj.y0,obj.x1,obj.y1))
     elif isinstance(obj,LTRect):lines.extend([(obj.x0,obj.y0,obj.x1,obj.y0),(obj.x0,obj.y1,obj.x1,obj.y1),(obj.x0,obj.y0,obj.x0,obj.y1),(obj.x1,obj.y0,obj.x1,obj.y1)])
     if isinstance(obj,LTCurve) and not isinstance(obj,(LTLine,LTRect)) and obj.fill and len(obj.pts)==4:
      xs=sorted(set(round(p[0],5) for p in obj.pts));ys=sorted(set(round(p[1],5) for p in obj.pts))
      if len(xs)==2 and len(ys)==2 and min(xs[1]-xs[0],ys[1]-ys[0])<=2:filled_bands.append((xs[0],ys[0],xs[1],ys[1]))
     if hasattr(obj,'__iter__'):
      for child in obj:walk(child)
    walk(layout);pypdf_text=page.extract_text();source_text=''.join(g[0] for g in glyphs);entry={'url':asset['url'],'source_sha256':asset['sha256'],'page':index+1,'glyphs':len(glyphs),'images_metadata_only':len(device.images),'glyph_nonwhitespace':len(chars(source_text)),'tables':0,'cells':0,'cell_mismatches':[],'boundary_errors':[],'source_filled_border_rectangles':len(filled_bands),'source_filled_border_path_edges':4*len(filled_bands)}
    if chars(pypdf_text)!=chars(record['text']):errors.append({'url':asset['url'],'kind':'pypdf_source_vs_normalized_text'})
    if sorted(chars(source_text))!=sorted(chars(record['text'])):errors.append({'url':asset['url'],'kind':'independent_glyph_multiset_mismatch'})
    if len(device.images)!=record['image_placeholder_count']:errors.append({'url':asset['url'],'kind':'image_metadata_vs_marker_count','source':len(device.images),'output':record['image_placeholder_count']})
    if not glyphs:
     if chars(record['text']):errors.append({'url':asset['url'],'kind':'no_source_glyphs_but_output_text'})
     entry['qualification']='Source has zero text glyphs; intentional images are [IMAGE], no OCR/transcription requested.'
    height=layout.height
    def covered(edge):
     x0,y0,x1,y1=edge;horizontal=abs(y1-y0)<.1;lo,hi=sorted((x0,x1) if horizontal else (y0,y1));pieces=[]
     for a0,b0,a1,b1 in lines:
      if horizontal and abs(b0-y0)<.15 and abs(b1-y0)<.15:pieces.append(sorted((a0,a1)))
      if not horizontal and abs(a0-x0)<.15 and abs(a1-x0)<.15:pieces.append(sorted((b0,b1)))
     for a0,b0,a1,b1 in filled_bands:
      if horizontal and b0-.01<=y0<=b1+.01:pieces.append([a0,a1])
      if not horizontal and a0-.01<=x0<=a1+.01:pieces.append([b0,b1])
     cursor=lo
     for low,high in sorted(pieces):
      if high<cursor-.2:continue
      if low>cursor+.2:break
      cursor=max(cursor,high)
     return cursor>=hi-.2
    for table in record['layout']['table_candidates']:
     entry['tables']+=1
     for ri,row in enumerate(table['cells']):
      for ci,cell in enumerate(row):
       entry['cells']+=1;x0,top,x1,bottom=cell['bbox'];y0=height-bottom;y1=height-top
       selected=[g for g in glyphs if x0-.2<=(g[1][0]+g[1][2])/2<=x1+.2 and y0-.2<=(g[1][1]+g[1][3])/2<=y1+.2]
       # Independent geometric order, preserving each source glyph, no invented spaces.
       selected.sort(key=lambda g:(-round(g[1][1],1),g[1][0]));text=''.join(g[0] for g in selected)
       if chars(text)!=chars(cell['text']):entry['cell_mismatches'].append({'row':ri,'cell':ci,'source':text,'normalized':cell['text']})
       for edge in [(x0,y0,x1,y0),(x0,y1,x1,y1),(x0,y0,x0,y1),(x1,y0,x1,y1)]:
        if not covered(edge):entry['boundary_errors'].append({'row':ri,'cell':ci,'edge':edge})
    if entry['cell_mismatches'] or entry['boundary_errors']:errors.append({'url':asset['url'],'kind':'grid_fidelity','cell_errors':len(entry['cell_mismatches']),'boundary_errors':len(entry['boundary_errors'])})
    results.append(entry)
 report={'passed':not errors,'script_sha256':sha(Path(__file__).read_bytes()),'source_pages_sha256':sha((a.run/'pdf-pages.jsonl').read_bytes()),'pages':results,'errors':errors,'image_streams_decoded':len(opened_image_streams),'network_requests_sent':0,'scope':'Actual five required originals; native glyph agreement/grid boundaries and literal image placeholders only. No source image bytes read/decoded, OCR/rendering or segmentation inference.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':not errors,'pages':len(results),'errors':errors}));return 0 if not errors else 2
if __name__=='__main__':raise SystemExit(main())
