"""Conservative source-wide qualification for one closed native grid per page.

This profile rejects unruled/multiple/merged/rotated/annotated layouts. It checks
every nonwhitespace Unicode glyph, original drawing edge and image placement;
ordinary table-candidate detection alone never qualifies the page.
"""
import unicodedata,collections,re
def norm(s):return ''.join(unicodedata.normalize('NFC',s).split())
def has_unprofiled_metadata(page):
 """Fail closed on annotations or ActualText, reading only command/Form streams."""
 seen=set()
 def visit(resources,stream):
  if stream is not None and b'/ActualText' in stream:return True
  resources=resources.get_object() if hasattr(resources,'get_object') else resources or {}
  properties=resources.get('/Properties',{});properties=properties.get_object() if hasattr(properties,'get_object') else properties
  if '/ActualText' in str(properties):return True
  objects=resources.get('/XObject',{});objects=objects.get_object() if hasattr(objects,'get_object') else objects
  for obj in objects.values():
   key=getattr(obj,'idnum',id(obj))
   if key in seen:continue
   seen.add(key);obj=obj.get_object()
   if obj.get('/Subtype')=='/Form' and visit(obj.get('/Resources',resources),obj.get_data()):return True
  return False
 return bool(page.get('/Annots')) or visit(page.get('/Resources'),page.get_contents().get_data() if page.get_contents() else None)
def qualify(page,reference,layout,native,placements,source_has_actual_text=False):
 reasons=[];tables=layout['table_candidates'];edges=[]
 for drawing in page.get_drawings():
  vertices=[]
  for item in drawing['items']:
   if item[0]=='l':
    a,b=item[1:];edges.append((a.x,a.y,b.x,b.y));vertices.extend([a,b])
   elif item[0]=='re':
    box=item[1];edges.extend([(box.x0,box.y0,box.x1,box.y0),(box.x1,box.y0,box.x1,box.y1),(box.x1,box.y1,box.x0,box.y1),(box.x0,box.y1,box.x0,box.y0)])
   else:reasons.append('Nonlinear original drawing outside closed-grid profile')
  if vertices and 'f' in drawing['type']:
   a,b=vertices[-1],vertices[0];edges.append((a.x,a.y,b.x,b.y))
 if len(tables)!=1:reasons.append('Exactly one grid required')
 if page.rotation or page.rect.width!=page.mediabox.width or page.rect.height!=page.mediabox.height:reasons.append('Rotated/cropped coordinate profile unsupported')
 if native['unmapped_glyph_count']:reasons.append('Unmapped original Unicode glyphs')
 if source_has_actual_text:reasons.append('Literal source ActualText/property variants need separate qualification')
 if norm(native['glyph_text'])!=norm(reference):reasons.append('Original native Unicode order differs from pypdf, retaining punctuation and case')
 def covered(x0,y0,x1,y1):
  horizontal=abs(y1-y0)<.1;vertical=abs(x1-x0)<.1
  if not(horizontal or vertical):return False
  fixed=(y0+y1)/2 if horizontal else (x0+x1)/2;lo,hi=sorted([x0,x1] if horizontal else [y0,y1]);spans=[]
  for a,b,c,d in edges:
   if horizontal and abs(b-d)<.1 and abs((b+d)/2-fixed)<=1:spans.append(sorted([a,c]))
   elif vertical and abs(a-c)<.1 and abs((a+c)/2-fixed)<=1:spans.append(sorted([b,d]))
  cursor=lo
  for a,b in sorted(spans):
   if b<cursor-1:continue
   if a>cursor+1:return False
   cursor=max(cursor,b)
  return cursor>=hi-1
 cells=[c for t in tables for row in t['cells'] for c in row if c];assigned=collections.defaultdict(list);unowned=[];outside=[]
 for index,g in enumerate(native['glyphs']):
  if not g['text'] or not g['text'].strip():continue
  owners=[i for i,c in enumerate(cells) if c['bbox'][0]-.1<=g['x']<c['bbox'][2]+.1 and c['bbox'][1]-.1<=g['y']<c['bbox'][3]+.1]
  if not owners:outside.append(index)
  elif len(owners)!=1:unowned.append(index)
  else:assigned[owners[0]].append(g['text'])
 outside_text=''.join(native['glyphs'][i]['text'] for i in outside);outside_note=None
 if outside:
  points=[native['glyphs'][i] for i in outside];bottom=max((c['bbox'][3] for c in cells),default=page.rect.height);positions=all(p['y']>bottom and p['x']<=q['x']+.1 and abs(p['y']-q['y'])<.1 for p,q in zip(points,points[1:]));citation=bool(re.fullmatch(r'\(Ord\.No\.[A-Za-z0-9.-]+\.Passed[0-9-]+,eff\.[0-9-]+\)',norm(outside_text)))
  if positions and citation:outside_note={'kind':'source-trailing-ordinance-note','text':outside_text,'source_glyph_indices':outside,'source_nonwhitespace_glyph_count':len(outside)}
  else:unowned.extend(outside)
 if unowned:reasons.append('Every original nonwhitespace glyph must have exactly one cell owner')
 checks=[]
 for index,c in enumerate(cells):
  x0,y0,x1,y1=c['bbox'];closed=all(covered(*edge) for edge in [(x0,y0,x1,y0),(x1,y0,x1,y1),(x1,y1,x0,y1),(x0,y1,x0,y0)])
  text_equal=norm((c['text'] or '').replace('[IMAGE]',''))==norm(''.join(assigned[index]));span=c['rowspan']==c['colspan']==1
  checks.append({'cell_index':index,'closed_original_border':closed,'original_unicode_order_equal':text_equal,'unmerged_source_span':span,'source_nonwhitespace_glyph_count':len(assigned[index])})
  if not(closed and text_equal and span):reasons.append('Cell source border/Unicode/span mismatch at '+str(index))
 image_owners=[]
 for image in placements:
  x0,y0,x1,y1=image['bbox'];point=((x0+x1)/2,page.rect.height-(y0+y1)/2);owners=[i for i,c in enumerate(cells) if c['bbox'][0]<=point[0]<c['bbox'][2] and c['bbox'][1]<=point[1]<c['bbox'][3]];image_owners.append({'source_ordinal':image['ordinal'],'cell_indices':owners})
  if len(owners)!=1 or cells[owners[0]].get('image_placement_ordinals',[]).count(image['ordinal'])!=1:reasons.append('Image draw operation must own one cell placeholder')
 if norm((''.join(c['text'] or '' for c in cells)+(outside_text if outside_note else '')).replace('[IMAGE]',''))!=norm(native['glyph_text']):reasons.append('Whole-grid cell and trailing-note order differs from native Unicode source order')
 qualified=bool(cells) and not reasons
 return {'profile':'single-closed-native-grid-source-wide-v1','source_text_qualified':qualified,'source_tables_qualified':qualified,'source_reading_order_qualified':qualified,'legal_provision_segmentation_qualified':False,'policy_not_applicable_to_text_glyph_fidelity':False,'original_edge_count':len(edges),'source_text_glyph_count':native['glyph_count'],'original_nonwhitespace_glyph_count':sum(len(v) for v in assigned.values())+len(outside) if outside_note else sum(len(v) for v in assigned.values()),'unowned_or_duplicate_glyph_indices':unowned,'trailing_source_note':outside_note,'cells':checks,'image_cell_owners':image_owners,'reasons':list(dict.fromkeys(reasons)),'basis':'All original native glyphs and their exact source order, pypdf Unicode, every closed cell drawing border, unmerged spans, optional single-line trailing ordinance citation and every image draw placeholder reconcile; no raster decoding'}
