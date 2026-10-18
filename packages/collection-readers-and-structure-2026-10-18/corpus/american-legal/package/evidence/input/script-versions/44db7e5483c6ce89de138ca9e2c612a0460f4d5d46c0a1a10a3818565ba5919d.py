"""Native PDF text geometry and table candidates; never rasterize or extract image binaries."""
import collections,re,unicodedata
import pymupdf

def rounded(box):return [round(float(v),4) for v in box]
def characters(text):return collections.Counter(c for c in unicodedata.normalize('NFKC',text).casefold() if c.isalnum())
def layout_page(page,reference_text):
 # TEXT_PRESERVE_IMAGES must remain disabled: no image payload enters a text record.
 raw=page.get_text('dict',flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES,sort=False)
 blocks=[];lines=[]
 for b in raw['blocks']:
  assert b['type']==0 and 'image' not in b,'Unexpected image payload'
  out={'source_block_index':b['number'],'bbox':rounded(b['bbox']),'lines':[]}
  for line in b['lines']:
   spans=[{'text':s['text'],'bbox':rounded(s['bbox']),'size':round(s['size'],4),'font':s['font'],'flags':s['flags']} for s in line['spans']]
   row={'bbox':rounded(line['bbox']),'direction':list(line['dir']),'spans':spans,'text':''.join(s['text'] for s in spans)};out['lines'].append(row);lines.append(row)
  blocks.append(out)
 text='\n'.join(l['text'] for l in lines);expected_chars=characters(reference_text);observed_chars=characters(text);common=sum((expected_chars&observed_chars).values());agreement=(2*common/(sum(expected_chars.values())+sum(observed_chars.values()))) if expected_chars or observed_chars else 1.0
 drawings=page.get_drawings();tables=[]
 for table in page.find_tables(paths=drawings).tables:
  textrows=table.extract();cells=[];xs=sorted(set(round(c[j],2) for r in table.rows for c in r.cells if c for j in [0,2]));ys=sorted(set(round(c[j],2) for r in table.rows for c in r.cells if c for j in [1,3]))
  for i,row in enumerate(table.rows):
   rr=[]
   for j,box in enumerate(row.cells):
    if box is None:rr.append(None);continue
    colspan=sum(box[0]-.2<=x and y<=box[2]+.2 for x,y in zip(xs,xs[1:]));rowspan=sum(box[1]-.2<=x and y<=box[3]+.2 for x,y in zip(ys,ys[1:]))
    rr.append({'text':textrows[i][j],'bbox':rounded(box),'rowspan':max(1,rowspan),'colspan':max(1,colspan)})
   cells.append(rr)
  occupied=[c for row in cells for c in row if c and c['text'] and c['text'].strip()];short=sum(len(re.sub(r'\s','',c['text']))<=2 for c in occupied);widths=[b-a for a,b in zip(xs,xs[1:])];reasons=[]
  if table.row_count<2 or table.col_count<2:reasons.append('Fewer than two rows/columns')
  if widths and min(widths)<12:reasons.append('Narrow graphical cells; diagram fragments possible')
  if not occupied or short>len(occupied)/2:reasons.append('Mostly empty or isolated-character cells')
  if len(xs)!=table.col_count+1 or len(ys)!=table.row_count+1:reasons.append('Grid boundaries do not reconcile to candidate dimensions')
  tables.append({'bbox':rounded(table.bbox),'row_count':table.row_count,'column_count':table.col_count,'cells':cells,'qualification':'ruled-grid-geometry' if not reasons else 'unqualified-candidate','reasons':reasons})
 body=[l for l in lines if l['text'].strip() and 45<l['bbox'][1]<page.rect.height-35];backtracks=[i for i in range(1,len(body)) if body[i]['bbox'][1]<body[i-1]['bbox'][1]-3]
 cross=[]
 for i,x in enumerate(blocks):
  a=x['bbox']
  for j in range(i+1,len(blocks)):
   b=blocks[j]['bbox'];overlap=min(a[3],b[3])-max(a[1],b[1]);disjoint=a[2]+8<b[0] or b[2]+8<a[0]
   if overlap>8 and disjoint:
    covered=any(t['qualification']=='ruled-grid-geometry' and all(t['bbox'][0]-.2<=r[0] and t['bbox'][1]-.2<=r[1] and r[2]<=t['bbox'][2]+.2 and r[3]<=t['bbox'][3]+.2 for r in [a,b]) for t in tables)
    if not covered:cross.append([i,j])
 images=[{'xref':x[0],'width':x[2],'height':x[3],'colorspace':x[5]} for x in page.get_images(full=True)]
 return {'engine':'PyMuPDF '+pymupdf.VersionBind,'page_size':rounded(page.rect),'text_blocks':blocks,'geometric_line_order':sorted(range(len(lines)),key=lambda i:(round(lines[i]['bbox'][1],1),lines[i]['bbox'][0])),'independent_text_character_agreement':round(agreement,8),'independent_text_characters_equal':expected_chars==observed_chars,'reading_order_qualified':expected_chars==observed_chars and not backtracks and not cross,'reading_order_backtracks':backtracks,'parallel_text_block_pairs':cross,'table_candidates':tables,'table_completeness_qualified':False,'table_scope':'Native ruled-grid candidates only; diagrams and unruled tables require explicit qualification','image_resources_metadata':images,'vector_graphics_present':bool(drawings),'vector_graphics_disposition':'[IMAGE]' if drawings else None,'image_binary_extraction_count':0}
