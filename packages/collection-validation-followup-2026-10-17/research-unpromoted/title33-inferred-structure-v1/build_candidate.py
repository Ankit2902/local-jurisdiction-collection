from pathlib import Path
p=Path('current_selected.py');s=p.read_text();anchor='def table_candidates(page,words):\n';helper='''def inferred_boundary_cuts(table,words,tolerance=.25):
 """Reject inferred cell ownership that crops a source word. Never expand cells.

 Merged/spanning cells are accepted when one actual candidate cell contains the
 whole source word. A grid line existing only in another row is not a boundary.
 """
 cells=[b for b in table.cells if b];cuts=[]
 for w in words:
  if not (table.bbox[0]<(w['x0']+w['x1'])/2<table.bbox[2] and table.bbox[1]<(w['top']+w['bottom'])/2<table.bbox[3]):continue
  containing=[b for b in cells if inside(w,b)]
  complete=[b for b in containing if b[0]-tolerance<=w['x0'] and w['x1']<=b[2]+tolerance and b[1]-tolerance<=w['top'] and w['bottom']<=b[3]+tolerance]
  if not complete:cuts.append({'source_word_id':w['id'],'source_word_text':w['text'],'source_word_bbox':box(w),'candidate_center_cells':[[round(v,3) for v in b] for b in containing],'reason':'No inferred cell contains this whole source word; cropped cell strings cannot establish structure.'})
 return cuts

'''
assert anchor in s;s=s.replace(anchor,helper+anchor)
s=s.replace("tid=ident+'::table:'+str(ti+1);matrix=", "unsafe=inferred_boundary_cuts(table,words) if method!='ruled' else [];tid=ident+'::table:'+str(ti+1);matrix=")
s=s.replace("ids=[w['id'] for w in words if inside(w,b) and w['id'] not in owned];owned.update(ids)","candidate_ids=[w['id'] for w in words if inside(w,b) and w['id'] not in owned];ids=[] if unsafe else candidate_ids;owned.update(ids)")
s=s.replace("'text':text,'word_ids':ids,'independent_pdfium_text'", "'text':text,'word_ids':ids,'candidate_word_ids':candidate_ids,'independent_pdfium_text'")
needle="    new_ids=[i for c in cells for i in c['word_ids']]\n"
new="""    if unsafe:
     tables[-1].update(structure_qualification=False,structure_status='rejected_unsafe_inferred_word_boundaries',source_word_boundary_failures=unsafe,page_text_disposition='Every original source word remains in canonical page text, outside this rejected table. Candidate cells, bboxes, original strings and independent disagreements are retained without qualification.')
     review.append(tid+':inferred_structure_boundary_splits_source_words')
     continue
    new_ids=[i for c in cells for i in c['word_ids']]
"""
assert needle in s;s=s.replace(needle,new);Path('candidate_selected.py').write_text(s)
