"""Network-free candidate replay; source inventory/raw are never modified."""
import sys,json,pathlib,hashlib,copy,collections
import spokane_bulk
base=pathlib.Path(__file__).resolve().parent
run=pathlib.Path(sys.argv[1]).resolve();out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
state=json.loads((run/'checkpoint.json').read_text());config=json.loads((run/'config.json').read_text());variants,occurrences,aliases=spokane_bulk.section_controls((run/state['identity']['section_inventory_ref']).read_bytes());reports=[];counts=collections.Counter();ids=[]
with (out/'records.jsonl').open('w') as dest:
 for item in state['items']:
  selected=copy.deepcopy(item);selected['section_heading_labels']={k:variants[k] for k in item['expected_sections']};data=(run/item['raw_ref']).read_bytes();rows,dispositions=spokane_bulk.parse(data,selected,config)
  for row in rows:dest.write(json.dumps(row,ensure_ascii=False)+'\n');counts[row['unit']]+=1;ids.append(row['id'])
  reports.append({'item_id':item['id'],'raw_ref':item['raw_ref'],'raw_sha256':hashlib.sha256(data).hexdigest(),'expected_unique_sections':len(item['expected_sections']),'parsed_records':len(rows),'conservation':rows[0].get('source_text_conservation'),'dispositions':dispositions});print(json.dumps({'done':len(reports),'total':len(state['items'])}),flush=True)
report={'schema':1,'offline':True,'candidate_only':True,'production_source_modified':False,'fresh_live_acquisition':False,'source_run':str(run),'source_checkpoint_sha256':hashlib.sha256((run/'checkpoint.json').read_bytes()).hexdigest(),'executed_sources':{name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in ['spokane_bulk.py','model.py']},'section_source_control_count':len(occurrences),'canonical_enabled_section_count':len(state['identity']['expected_sections']),'duplicate_control_aliases':aliases,'batch_count':len(reports),'record_units':dict(counts),'duplicate_record_ids':[k for k,v in collections.Counter(ids).items() if v>1],'batches':reports,'limitations':['Retained raw source replay only; required external assets and source edition remain as original source run.','All genuinely distinct native version bodies retained; no current-version choice inferred.']}
(out/'replay.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['batches','duplicate_control_aliases']},indent=2))
