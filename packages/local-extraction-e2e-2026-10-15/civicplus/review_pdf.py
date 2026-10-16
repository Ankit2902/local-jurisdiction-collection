"""Apply narrowly reviewed recoveries, bound to immutable source and visual evidence."""
from copy import deepcopy
from pathlib import Path
from civicplus import sha,readj,writej,norm

def apply_review(path,document_id,raw_hash,pages,blocks,issues,package):
 config_path=Path(path);config=readj(config_path);entry=config.get('documents',{}).get(document_id)
 if entry is None:return pages,blocks,issues,[]
 if entry['raw_sha256']!=raw_hash:raise ValueError('Reviewed recovery source hash mismatch: '+document_id)
 evidence=[]
 for e in entry['evidence']:
  file=(config_path.parent/e['path']).resolve()
  if sha(file.read_bytes())!=e['sha256']:raise ValueError('Reviewed source rendering hash mismatch: '+e['path'])
  target=package/'raw'/('review-'+e['sha256']+file.suffix);target.write_bytes(file.read_bytes());evidence.append({'path':str(target.relative_to(package)),'sha256':e['sha256'],'page':e['page']})
 pages=deepcopy(pages);blocks=deepcopy(blocks);issues=deepcopy(issues);events=[]
 def find(locator):
  hits=[b for b in blocks if b['page']==locator['page'] and b['kind']==locator['kind'] and abs(b['bbox'][1]-locator['top'])<.02]
  if len(hits)!=1:raise ValueError('Reviewed locator is missing or ambiguous: '+str(locator))
  return hits[0]
 for op in entry['operations']:
  if op['kind']=='table_semantics':
   block=find(op['locator'])
   if [[norm(c or '') for c in r] for r in block['rows']]!=op['expected_rows']:raise ValueError('Reviewed table cells changed')
   block['html']=op['html'];block['review_id']=op['id'];block['review_evidence']=evidence
  elif op['kind']=='merge_table_continuation':
   first=find(op['first']);second=find(op['second'])
   if [[norm(c or '') for c in r] for r in first['rows']]!=op['expected_first_rows'] or [[norm(c or '') for c in r] for r in second['rows']]!=op['expected_second_rows']:raise ValueError('Reviewed continuation rows changed')
   first['html']=op['html'];first['source_fragments']=[{'page':x['page'],'bbox':x['bbox']} for x in [first,second]];first['rows']+=second['rows'];first['review_id']=op['id'];first['review_evidence']=evidence;blocks.remove(second)
  elif op['kind']=='insert_visual_transcription':
   anchor=find(op['anchor'])
   if op.get('expected_image_name')!=anchor.get('name'):raise ValueError('Reviewed image identity changed')
   pos=blocks.index(anchor)
   blocks.insert(pos,{'kind':'line','page':anchor['page'],'bbox':anchor['bbox'],'text':op['text'],'fonts':[],'font_sizes':[],'review_id':op['id'],'review_evidence':evidence,'recovery_method':'manual_visual_transcription','remaining_uncertainty':op['remaining_uncertainty']})
   issues.append({'page':anchor['page'],'condition':'unreadable_source_symbol_after_reviewed_transcription','disposition':'unresolved','review_id':op['id'],'detail':op['remaining_uncertainty']})
  else:raise ValueError('Unknown reviewed operation')
  events.append({'review_id':op['id'],'operation':op['kind'],'source_sha256':raw_hash,'evidence':evidence,'reviewer':entry['reviewer'],'reviewed_at':entry['reviewed_at']})
 # Only a wholly reviewed page/table set can discharge the broad page table gate.
 for page in entry.get('fully_reviewed_table_pages',[]):
  issues=[i for i in issues if not (i.get('page')==page and i['condition']=='table_semantics_and_cross_page_review')]
 for p in pages:
  if any(e['page']==p['page'] for e in evidence):p['reviewed_recovery_events']=[x for x in events]
 return pages,blocks,issues,events
