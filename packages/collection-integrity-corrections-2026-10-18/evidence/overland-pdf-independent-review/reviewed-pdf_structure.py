"""Coordinate-aware PDF text/table normalization. Never renders or reads image pixels."""
import collections,hashlib,io,json,math,re,unicodedata
import pdfplumber,pypdfium2
from .bounded_decoder import bounded_decoder_aliases

def clean(s):return re.sub(r'\s+',' ',s or '').strip()
def chars(s):return collections.Counter(c for c in unicodedata.normalize('NFKC',s or '') if not c.isspace() and c not in '\u200b\u00ad\ufeff')
def box(o):return [round(float(o[k]),3) for k in ['x0','top','x1','bottom']]
def inside(w,b):return b[0]<=((w['x0']+w['x1'])/2)<=b[2] and b[1]<=((w['top']+w['bottom'])/2)<=b[3]
def lines(words):
 result=[]
 for word in sorted(words,key=lambda x:(x['top'],x['x0'])):
  if not result or abs(result[-1]['top']-word['top'])>3:result.append({'top':word['top'],'words':[]})
  result[-1]['words'].append(word)
 out=[]
 for row in result:
  ws=sorted(row['words'],key=lambda x:x['x0']);out.append({'kind':'text','bbox':[min(w['x0'] for w in ws),min(w['top'] for w in ws),max(w['x1'] for w in ws),max(w['bottom'] for w in ws)],'text':' '.join(w['text'] for w in ws),'word_ids':[w['id'] for w in ws]})
 return out

def order(words,objects,width):
 # A persistent low-occupancy vertical gutter distinguishes two text columns.
 bins=range(int(width*.28),int(width*.72),2);threshold=max(1,int(len(words)*.002));low=[]
 for x in bins:
  if sum(w['x0']<x<w['x1'] for w in words)<=threshold:low.append(x)
 groups=[]
 for x in low:
  if not groups or x-groups[-1][-1]>2:groups.append([x])
  else:groups[-1].append(x)
 gutter=max(groups,key=len,default=[]);gutter=[gutter[0],gutter[-1]+2] if len(gutter)>=8 else None
 if gutter:
  midpoint=sum(gutter)/2;left=[w for w in words if w['x1']<=midpoint];right=[w for w in words if w['x0']>=midpoint];cross=[w for w in words if w not in left and w not in right]
  if min(len(left),len(right))<max(20,len(words)*.15):gutter=None
 if not gutter:return sorted(lines(words)+objects,key=lambda b:(b['bbox'][1],b['bbox'][0])),{'method':'physical lines top-to-bottom, left-to-right','gutter':None}
 # Full-width rows/tables/figures divide the page into independent column bands.
 crosslines=lines(cross);cross_ids=set()
 for line in crosslines:
  related=[w for w in words if abs(w['top']-line['bbox'][1])<=3];cross_ids.update(w['id'] for w in related)
  if related:line.update(text=' '.join(w['text'] for w in sorted(related,key=lambda w:w['x0'])),word_ids=[w['id'] for w in related],bbox=[min(w['x0'] for w in related),min(w['top'] for w in related),max(w['x1'] for w in related),max(w['bottom'] for w in related)])
 spanning=sorted(crosslines+[b for b in objects if b['bbox'][0]<midpoint<b['bbox'][2]],key=lambda b:b['bbox'][1]);remaining=[w for w in words if w['id'] not in cross_ids];out=[]
 for boundary in spanning+[{'bbox':[0,math.inf,width,math.inf],'sentinel':True}]:
  band=[w for w in remaining if w['top']<boundary['bbox'][1]];ids={w['id'] for w in band};remaining=[w for w in remaining if w['id'] not in ids]
  out+=lines([w for w in band if (w['x0']+w['x1'])/2<midpoint]);out+=lines([w for w in band if (w['x0']+w['x1'])/2>=midpoint])
  if not boundary.get('sentinel'):out.append(boundary)
 # Objects in one column get a stable geometry slot alongside the relevant text.
 for obj in [b for b in objects if b not in spanning]:
  loc=next((i for i,b in enumerate(out) if b['bbox'][1]>=obj['bbox'][1] and (b['bbox'][0]<midpoint)==(obj['bbox'][0]<midpoint)),len(out));out.insert(loc,obj)
 return out,{'method':'persistent-gutter column bands; full-width rows/tables/figures delimit bands','gutter':[round(x,3) for x in gutter]}

def table_candidates(page,words):
 if len(page.edges)>5000:return [],['more_than_5000_vector_edges_table_detection_review']
 ruled=page.find_tables();found=[(t,'ruled') for t in ruled]
 code=lambda v: bool(re.fullmatch(r'[$€£]?\(?[-+\d.,%/]+\)?|[A-Z]{1,3}|[YN]',v))
 rows=lines(words);coded_rows=[r for r in rows if len(r['word_ids'])>=2 and sum(code(t) for t in r['text'].split())/len(r['text'].split())>=.35]
 if len(coded_rows)<3:return found,[]
 # Borderless schedules must show repeated aligned columns and predominantly
 # numeric/currency/short-use codes, rather than ordinary two-column prose.
 text=page.find_tables({'vertical_strategy':'text','horizontal_strategy':'text','min_words_vertical':3,'min_words_horizontal':1,'text_x_tolerance':2,'text_y_tolerance':3})
 for t in text:
  matrix=t.extract();values=[clean(c) for row in matrix for c in row if clean(c)];rows=sum(any(clean(c) for c in row) for row in matrix);columns=max(map(len,matrix),default=0)
  coded=sum(bool(re.fullmatch(r'[$€£]?\(?[-+\d.,%/]+\)?|[A-Z]{1,3}|[YN]',v)) for v in values)
  if rows<3 or columns<2 or not values or coded/len(values)<.25:continue
  if any(max(0,min(t.bbox[2],x.bbox[2])-max(t.bbox[0],x.bbox[0]))*max(0,min(t.bbox[3],x.bbox[3])-max(t.bbox[1],x.bbox[1]))>min((t.bbox[2]-t.bbox[0])*(t.bbox[3]-t.bbox[1]),(x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]))*.5 for x in ruled):continue
  found.append((t,'aligned_text_numeric_schedule'))
 return found,[]

def invalid_decoder_resolutions(text,textpage,page):
 # A PDFium noncharacter is recoverable only when its actual glyph bbox has a
 # unique closest pdfminer Unicode glyph at that same physical position.
 resolutions=[];resolved=text
 for index,char in enumerate(text):
  if char not in ['\ufffe','\uffff','\ufffd']:continue
  x0,y0,x1,y1=textpage.get_charbox(index);cx=(x0+x1)/2;cy=float(page.height)-(y0+y1)/2
  candidates=[c for c in page.chars if c['x0']-1<=cx<=c['x1']+1 and c['top']-1<=cy<=c['bottom']+1 and c['text'] and not any(ord(x)>=0xfffe or x=='\ufffd' or 0xe000<=ord(x)<=0xf8ff for x in c['text'])]
  candidates.sort(key=lambda c:abs((c['x0']+c['x1'])/2-cx))
  if candidates and (len(candidates)==1 or abs((candidates[0]['x0']+candidates[0]['x1'])/2-cx)+.25<abs((candidates[1]['x0']+candidates[1]['x1'])/2-cx)):
   c=candidates[0];resolutions.append({'pdfium_character_index':index,'pdfium_codepoint':ord(char),'pdfminer_unicode':c['text'],'glyph_bbox_pdfium':[x0,float(page.height)-y1,x1,float(page.height)-y0],'glyph_bbox_pdfminer':box(c),'fontname':c['fontname'],'qualification':'PDFium invalid noncharacter only; uniquely closest independently decoded source glyph at the same physical location.'})
 resolved=''.join(next((r['pdfminer_unicode'] for r in resolutions if r['pdfium_character_index']==i),c) for i,c in enumerate(text))
 return resolved,resolutions

def redact_image_text(value):
 # A complete declared literal-SVG envelope is a whole image value. Do not
 # interpret SVG markup, decode pixels, or consume following legal prose.
 svg_prefix=re.match(r'\s*data:image/svg\+xml(?:;[^,\s]*)?,\s*',value,re.I)
 if svg_prefix:
  payload=value[svg_prefix.end():].strip()
  # Generic extracted text has no typed-URI boundary: accept only a plain
  # unambiguous root opening. Attributes/quoted delimiters remain unsupported.
  if re.fullmatch(r'<svg\s*/>',payload,re.I):return '[IMAGE]'
  if re.match(r'<svg\s*>',payload,re.I) and re.search(r'</svg\s*>$',payload,re.I) and len(re.findall(r'<svg\b',payload,re.I))==1 and len(re.findall(r'</svg\s*>',payload,re.I))==1:return '[IMAGE]'
 chunks=[];position=0
 def ambiguous():raise ValueError('Unsupported ambiguous inline-image text boundary; source sha256='+hashlib.sha256(value.encode()).hexdigest())
 for match in re.finditer(r'data:image/',value,re.I):
  if match.start()<position:continue
  start=match.start();chunks.append(value[position:start]);quote=value[start-1] if start and value[start-1] in ['"',"'"] else None
  if quote:
   end=value.find(quote,match.end())
   if end<0:ambiguous()
   if '<' in value[start:end] or '>' in value[start:end]:ambiguous()
  else:
   token=re.match(r'[^\s"\'<>]+',value[start:]);end=start+len(token.group()) if token else start
   if value[end:].strip():ambiguous()
  chunks.append('[IMAGE]');position=end
 chunks.append(value[position:]);return ''.join(chunks)

def redact_metadata(value,_field=None):
 if isinstance(value,str):
  # URI is a typed PDF annotation address, not extracted legal text/captions.
  if str(_field).lower()=='uri' and value.lstrip().lower().startswith('data:image/'):return '[IMAGE]'
  return redact_image_text(value)
 if isinstance(value,list):return [redact_metadata(v,_field) for v in value]
 if isinstance(value,dict):return {k:redact_metadata(v,k) for k,v in value.items()}
 return value

def pages(data,item,config):
 if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-1024:]:raise ValueError('Native PDF envelope incomplete')
 stream=pypdfium2.PdfDocument(data);pdf=pdfplumber.open(io.BytesIO(data));digest=hashlib.sha256(data).hexdigest();output=[]
 try:
  if not len(stream) or len(stream)!=len(pdf.pages):raise ValueError('Independent PDF page counts disagree or empty')
  for n,original in enumerate(pdf.pages):
   page=original.dedupe_chars(tolerance=.5);native=stream[n];tp=native.get_textpage();native_text=tp.get_text_range();comparable_text,decoder_resolutions=invalid_decoder_resolutions(native_text,tp,original);ident=item['id']+'::page:'+str(n+1);review=[]
   words=page.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size'])
   for i,w in enumerate(words):w['id']=ident+'::word:'+str(i+1)
   candidates,flags=table_candidates(page,words);review+=flags;tables=[];objects=[];owned=set()
   for ti,(table,method) in enumerate(candidates):
    tid=ident+'::table:'+str(ti+1);matrix=table.extract(x_tolerance=1.5,y_tolerance=3);values={}
    for ri,row in enumerate(table.rows):
     for ci,b in enumerate(row.cells):
      if b is not None and b not in values:values[b]=(matrix[ri][ci] or '')
    xs=sorted({round(v,3) for b in table.cells if b for v in [b[0],b[2]]});ys=sorted({round(v,3) for b in table.cells if b for v in [b[1],b[3]]});cells=[]
    for ci,(b,text) in enumerate(sorted(values.items(),key=lambda p:(p[0][1],p[0][0]))):
     bounded=tp.get_text_bounded(b[0],float(page.height)-b[3],b[2],float(page.height)-b[1]);ids=[w['id'] for w in words if inside(w,b) and w['id'] not in owned];owned.update(ids);qualified_bounded=bounded
     for recovery in decoder_resolutions:
      b0=recovery['glyph_bbox_pdfium'];center=((b0[0]+b0[2])/2,(b0[1]+b0[3])/2)
      if b[0]<=center[0]<=b[2] and b[1]<=center[1]<=b[3]:qualified_bounded=qualified_bounded.replace(chr(recovery['pdfium_codepoint']),recovery['pdfminer_unicode'],1)
     qualified_bounded,bounded_alias_proof=bounded_decoder_aliases(qualified_bounded,b,decoder_resolutions,tp,original,native_text)
     agree=chars(text)==chars(qualified_bounded);x0,x1=xs.index(round(b[0],3)),xs.index(round(b[2],3));y0,y1=ys.index(round(b[1],3)),ys.index(round(b[3],3));cells.append({'id':tid+'::cell:'+str(ci+1),'bbox':[round(v,3) for v in b],'row':y0,'column':x0,'rowspan':y1-y0,'colspan':x1-x0,'text':text,'word_ids':ids,'independent_pdfium_text':bounded,'qualified_pdfium_text':qualified_bounded,'bounded_decoder_alias_resolutions':bounded_alias_proof,'independent_character_agreement':agree})
    if any(not c['independent_character_agreement'] for c in cells):review.append(tid+':independent_cell_text_disagreement')
    tabletext='\n'.join('\t'.join(c['text'] for c in cells if c['row']==r) for r in range(max((c['row'] for c in cells),default=-1)+1));tables.append({'id':tid,'bbox':[round(v,3) for v in table.bbox],'detection':method,'row_boundaries':ys,'column_boundaries':xs,'cells':cells});
    new_ids=[i for c in cells for i in c['word_ids']]
    if new_ids:
     word_by_id={w['id']:w for w in words};canonical_text='\n'.join(' '.join(line['text'] for line in lines([word_by_id[w] for w in c['word_ids']])) for c in cells if c['word_ids']);tables[-1]['page_text_serialization']='Each whole source word is emitted once by its unique geometry owner. Original detector cell text, bboxes and independent disagreements remain unchanged; no cell-boundary/table semantic qualification inferred.';objects.append({'kind':'table','id':tid,'bbox':[round(v,3) for v in table.bbox],'text':canonical_text,'word_ids':new_ids})
    elif tabletext.strip():tables[-1]['page_text_disposition']='Nested/overlapping detected region has no newly owned source words; cells retained as structure, its glyphs already appear in canonical parent/earlier table, not emitted twice.'
   images=[]
   for i,im in enumerate(page.images):
    b=box(im);image={'id':ident+'::image:'+str(i+1),'kind':'image_placeholder','bbox':b,'text':'[IMAGE]','word_ids':[],'source_name':str(im.get('name','')),'pixel_extraction':False};images.append(image);objects.append(image)
   vector_count=len(page.curves)+len(page.lines)+len(page.rects)
   if vector_count and (not words or re.search(r'\b(?:map|plan|street.?sections?)\b',item.get('heading',''),re.I) and len(page.curves)>20):
    figure={'id':ident+'::vector-illustration','kind':'image_placeholder','bbox':[0,0,float(page.width),float(page.height)],'text':'[IMAGE]','word_ids':[],'source_vector_object_count':vector_count,'pixel_extraction':False};images.append(figure);objects.append(figure)
   non_table=[w for w in words if w['id'] not in owned];blocks,ordering=order(non_table,objects,float(page.width));assigned=[i for b in blocks for i in b['word_ids']];counts=collections.Counter(assigned);missing=[w['id'] for w in words if counts[w['id']]!=1];text='\n'.join(b['text'] for b in blocks);source_words=''.join(w['text'] for w in words);normalized=text.replace('[IMAGE]','');raw_char_agree=chars(native_text)==chars(''.join(c['text'] for c in original.chars));char_agree=chars(comparable_text)==chars(''.join(c['text'] for c in original.chars));owned_agree=chars(normalized)==chars(source_words);source_glyph_agree=chars(source_words)==chars(''.join(c['text'] for c in page.chars));cid_literals=sorted(set(re.findall(r'\(cid:\d+\)',source_words)))
   if missing:review.append('missing_or_duplicate_source_word_ownership')
   if not char_agree:review.append('independent_pdfium_pdfminer_character_disagreement')
   if not owned_agree:review.append('normalized_text_source_word_character_disagreement')
   if not source_glyph_agree:review.append('source_words_do_not_cover_deduplicated_glyph_characters')
   if cid_literals:review.append('undecoded_source_CID_literals')
   bad=sorted({ord(c) for c in source_words if c=='\ufffd' or 0xe000<=ord(c)<=0xf8ff or ord(c)<32 and not c.isspace()})
   if bad:review.append('unmapped_or_private_use_glyphs')
   if not clean(source_words):review.append('image_only_or_no_extractable_legal_text')
   if len(page.curves):review.append('vector_illustration_interpretation_not_established')
   output.append({'id':ident,'document_id':item['id'],'unit':'pdf_page','heading':item['heading'],'path':[config['publication'],item['heading']],'source_url':item['url']+'#page='+str(n+1),'text':text,'pdfium_stream_text':native_text,'pdfium_qualified_comparison_text':comparable_text,'ordered_blocks':blocks,'ordering':ordering,'physical_page':n+1,'page_count':len(pdf.pages),'width':float(page.width),'height':float(page.height),'tables':tables,'links':[{k:a.get(k) for k in ['uri','title','contents','x0','top','x1','bottom'] if a.get(k) is not None} for a in page.annots or []],'assets':[],'image_placeholder_count':len(images),'image_policy':'Metadata-only raster bboxes and detected map/blank vector-page placeholders; no image pixels, rendering or OCR. General vector illustration classification and legal interpretation remain explicit review.','raw_ref':item['raw_ref'],'raw_sha256':digest,'jurisdiction':config['jurisdiction'],'state':config['state'],'publication':config['publication'],'semantic_review_required':True,'pdf_qualification':{'source_word_count':len(words),'source_words_cover_deduplicated_glyph_characters':source_glyph_agree,'undecoded_cid_literals':cid_literals,'deduplicated_overprint_character_count':len(original.chars)-len(page.chars),'source_word_ownership_complete':not missing,'word_ownership_failures':missing,'normalized_source_word_characters_agree':owned_agree,'independent_text_engine_characters_agree':char_agree,'raw_independent_text_engine_characters_agree':raw_char_agree,'invalid_decoder_glyph_resolutions':decoder_resolutions,'unmapped_or_private_use_codepoints':bad,'detected_table_count':len(tables),'detected_table_cells':sum(len(t['cells']) for t in tables),'independent_table_cells_agree':sum(c['independent_character_agreement'] for t in tables for c in t['cells']),'vector_curve_count':len(page.curves),'review_conditions':review,'table_scope':'Ruled grids and qualifying aligned numeric/use-code schedules; arbitrary borderless/non-numeric layouts and all legal semantics are not universally established.'}})
   tp.close();native.close();page.close();original.close()
 finally:pdf.close();stream.close()
 return redact_metadata(output),[]
