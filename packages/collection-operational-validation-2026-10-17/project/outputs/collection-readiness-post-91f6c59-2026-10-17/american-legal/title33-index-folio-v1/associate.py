"""Bounded source-index row associations, never inferred legal table cells."""
import hashlib,re

def associate(text,words,page_id):
 """Require exact native line text AND independent whole-word row geometry.

 Caller must establish that the page belongs to a source index; this helper does
 not classify arbitrary multi-column prose as an index. No characters are fixed.
 """
 entries=[];unassigned=[];used=set();offset=0
 for line in text.splitlines(keepends=True):
  plain=line.rstrip('\r\n');m=re.fullmatch(r'(?P<citation>\d{3}) (?P<label>\S.*) (?P<folio>\d{3}-\d+)',plain)
  if not m:unassigned.append({'start':offset,'end':offset+len(line),'text':line});offset+=len(line);continue
  starts=[w for w in words if w['text']==m['citation'] and w['x0']<100 and w['id'] not in used];matches=[]
  for start in starts:
   row=sorted([w for w in words if abs(w['top']-start['top'])<=.25 and abs(w['bottom']-start['bottom'])<=.25],key=lambda w:w['x0'])
   if ' '.join(w['text'] for w in row)==plain and row[-1]['x0']>450 and all(a['x1']<=b['x0']+.25 for a,b in zip(row,row[1:])):matches.append(row)
  assert len(matches)==1,'Native index line lacks unique exact independent whole-word row'
  row=matches[0];ids=[w['id'] for w in row];assert not used.intersection(ids),'Duplicate source word ownership';used.update(ids)
  entries.append({'id':page_id+'::index-row:'+str(len(entries)+1),'source_text_start':offset,'source_text_end':offset+len(line),'source_span':line,'source_span_sha256':hashlib.sha256(line.encode()).hexdigest(),'citation':m['citation'],'label':m['label'],'folio':m['folio'],'citation_folio_stem_agrees':m['citation']==m['folio'].split('-')[0],'source_word_ids':ids,'word_boxes':[{k:w[k] for k in ['id','text','x0','x1','top','bottom']} for w in row],'association_qualified':True,'scope':'Exact original native line and unique whole-word baseline association only; not a table-cell, destination-validity or whole-publication reading-order claim'})
  offset+=len(line)
 assert offset==len(text)
 spans=sorted([(e['source_text_start'],e['source_text_end'],e['source_span']) for e in entries]+[(e['start'],e['end'],e['text']) for e in unassigned]);assert ''.join(s[2] for s in spans)==text
 return {'entries':entries,'unassigned_spans':unassigned,'native_stream_sha256':hashlib.sha256(text.encode()).hexdigest(),'source_stream_retained_once':True,'associated_word_ids':sorted(used),'unassociated_word_ids':[w['id'] for w in words if w['id'] not in used],'source_spelling_or_folio_corrected':False,'whole_publication_reading_order_qualified':False,'inferred_cell_disagreements_waived':False}
