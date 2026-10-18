"""Independent serialized consumer/diagnostic-lineage audit; no parser imports or network."""
import argparse,collections,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--records',type=Path,required=True);p.add_argument('--csv',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return [json.loads(s) for s in path.read_text().split('\n') if s.strip()]
def demand(condition,message):
 if not condition:raise AssertionError(message)
records=read(a.records);baseline=read(a.baseline)
with a.csv.open(newline='') as stream:csvrows=list(csv.DictReader(stream))
demand(len(records)==len(baseline)==len(csvrows),'Record/CSV/baseline counts differ')
demand(len({x['id'] for x in records})==len(records),'Duplicate records')
fields=['tables','ordered_blocks','text','ordering','pdf_qualification'];changed=[];counts=collections.Counter();hashes={str(f):sha(f) for f in [a.records,a.csv,a.baseline]}
for record,prior,csvrow in zip(records,baseline,csvrows):
 ident=record['id'];demand(ident==prior['id']==csvrow['id'],'Ordered identity differs')
 for key in csvrow:demand(csvrow[key]==str(record.get(key,'')),'CSV field differs: '+ident+'/'+key)
 counts['records']+=1
 demand([b for b in record['ordered_blocks'] if b['kind']=='image_placeholder']==[b for b in prior['ordered_blocks'] if b['kind']=='image_placeholder'],'Image positions/ownership changed')
 demand(record['image_placeholder_count']==prior['image_placeholder_count'],'Image count changed');counts['image_placeholders']+=record['image_placeholder_count']
 selected=record.get('canonical_structure_selection')
 if not selected:demand(record==prior,'Unselected record changed');counts['unchanged_records']+=1;original=record
 else:
  demand(selected['authoritative_fields']==fields,'Unknown authoritative fields')
  demand(selected['source_sha256']==record['raw_sha256'] and selected['source_url']==record['source_url'] and selected['physical_page']==record['physical_page'],'Selection source binding mismatch')
  diag=record['superseded_detector_diagnostics'];original=diag['original_record_fields']
  demand(diag['raw_ref']==record['raw_ref'] and diag['raw_sha256']==record['raw_sha256'],'Diagnostic source binding mismatch')
  demand(original=={k:prior[k] for k in fields},'Exact original fields were not preserved')
  demand(all(record[k]==prior[k] for k in prior if k not in fields),'Unselected original field changed')
  demand(selected['canonical_table_ids']==[t['id'] for t in record['tables']],'Canonical table selection differs')
  indexes=record.get('source_printed_indexes',[]);schedules=record.get('source_physical_schedules',[])
  demand(bool(indexes)!=bool(schedules),'Missing/ambiguous source representation')
  source=(indexes or schedules)[0];demand(len(indexes or schedules)==1,'Ambiguous source evidence count');demand(selected['source_evidence_id']==source['id'],'Selection does not reference actual source proof')
  if indexes:
   demand(not record['tables'],'Printed index still exports spurious grid')
   demand([b['text'] for b in record['ordered_blocks']]==[u['canonical_printed_text'] for u in source['units']],'Canonical index order/content differs from source units')
   expected='\n'.join(u['canonical_printed_text'] for u in source['units']);wordids=[w for b in record['ordered_blocks'] for w in b['word_ids']]
   counts['canonical_index_regions']+=1
  else:
   demand(len(record['tables'])==1,'Source schedule needs one selected table');table=record['tables'][0]
   cells=sorted(source['cells'],key=lambda c:(c['row'],c['column']));actual=sorted(table['cells'],key=lambda c:(c['row'],c['column']))
   demand([(c['row'],c['column'],c['text']) for c in cells]==[(c['row'],c['column'],c['text']) for c in actual],'Canonical cells differ from source cells')
   rows=sorted({c['row'] for c in cells});expected='\n'.join('\t'.join(c['text'] for c in cells if c['row']==n) for n in rows)
   demand(all(c.get('rowspan',1)==1 and c.get('colspan',1)==1 for c in actual),'Invented source span')
   for sourcecell,cell in zip(cells,actual):
    demand(cell['word_ids']==sourcecell['source_word_ids'] and cell['source_glyph_ids']==sourcecell['source_glyph_ids'],'Cell source ownership differs')
    demand(cell['extraction_bbox']==sourcecell['extraction_bbox'],'Native cell query geometry differs')
    demand(cell['kind']==sourcecell['kind'] and cell['role']==sourcecell['role'],'Header or source column role differs')
   demand(table['header_rows']==sorted({c['row'] for c in cells if c['kind']=='header'}),'Source header rows differ')
   demand(len(record['ordered_blocks'])==1 and record['ordered_blocks'][0]['kind']=='table','Canonical source table not selected by page blocks')
   block=record['ordered_blocks'][0];wordids=block.get('word_ids',block.get('source_word_ids',[]))
   counts['canonical_schedule_regions']+=1;counts['canonical_schedule_cells']+=len(cells)
  demand(record['text']==expected,'Canonical text not source representation')
  demand(collections.Counter(wordids)==collections.Counter(w['id'] for w in source['source_words']),'Canonical word ownership differs')
  demand(len(wordids)==len(set(wordids)),'Duplicate canonical word owner')
  q=record['pdf_qualification'];demand(q['detected_table_count']==len(record['tables']),'Canonical table count differs');demand(q['detected_table_cells']==sum(len(t['cells']) for t in record['tables']),'Canonical cell count differs');demand(q['independent_table_cells_agree']==sum(c['independent_character_agreement'] for t in record['tables'] for c in t['cells']),'Canonical cell-agreement count differs')
  for key in ['unmapped_or_private_use_codepoints','undecoded_cid_literals','independent_text_engine_characters_agree']:demand(q[key]==prior['pdf_qualification'][key],'Unresolved source decoding evidence changed')
  changed.append({'id':ident,'profile':selected['profile'],'source_words':len(wordids),'superseded_false_cells':sum(not c['independent_character_agreement'] for t in original['tables'] for c in t['cells'])})
 counts['superseded_or_unchanged_original_false_cells']+=sum(not c['independent_character_agreement'] for t in original['tables'] for c in t['cells'])
 counts['canonical_false_cells']+=sum(not c['independent_character_agreement'] for t in record['tables'] for c in t['cells'])
demand(hashes=={str(f):sha(f) for f in [a.records,a.csv,a.baseline]},'Inputs changed')
result={'passed':True,'scope':'Independent serialized canonical consumer, source-evidence selection, exact diagnostic lineage and unchanged-record audit; no native parser/acquisition or whole-book acceptance claim','counts':dict(counts),'changed_records':changed,'input_hashes':hashes,'script_sha256':sha(Path(__file__)),'network_or_image_operations':False}
demand(not a.out.exists(),'Fresh report required');a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
