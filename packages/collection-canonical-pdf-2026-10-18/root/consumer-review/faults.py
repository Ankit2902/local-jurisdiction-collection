"""Actual retained-record export corruption checks for the independent consumer audit."""
import copy,csv,hashlib,io,json,subprocess,sys
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parents[1];candidate=root/'upoc-parser-integration-candidate-v1'
# root is .../collection-readiness-post1997ee1-2026-10-17
records=[json.loads(s) for s in (candidate/'derived-records.jsonl').read_text().split('\n') if s]
selected=next(r for r in records if r.get('canonical_structure_selection',{}).get('profile')=='sto_physical_schedule')
base={k:copy.deepcopy(v) for k,v in selected.items() if k not in ['canonical_structure_selection','superseded_detector_diagnostics','source_physical_schedules']};base.update(copy.deepcopy(selected['superseded_detector_diagnostics']['original_record_fields']))
fieldnames=['id','heading','physical_page','page_count','text','source_url','raw_sha256'];results=[]
for name in ['old_detector_selected','duplicate_canonical_word','changed_original_diagnostic','wrong_source_binding','stale_csv']:
 out=here/name;out.mkdir();row=copy.deepcopy(selected)
 if name=='old_detector_selected':row.update(copy.deepcopy(row['superseded_detector_diagnostics']['original_record_fields']))
 if name=='duplicate_canonical_word':row['ordered_blocks'][0]['word_ids'].append(row['ordered_blocks'][0]['word_ids'][0])
 if name=='changed_original_diagnostic':row['superseded_detector_diagnostics']['original_record_fields']['tables'][0]['cells'][0]['independent_character_agreement']=not row['superseded_detector_diagnostics']['original_record_fields']['tables'][0]['cells'][0]['independent_character_agreement']
 if name=='wrong_source_binding':row['canonical_structure_selection']['source_sha256']='0'*64
 (out/'records.jsonl').write_text(json.dumps(row)+'\n');(out/'baseline.jsonl').write_text(json.dumps(base)+'\n')
 csvrow={k:row[k] for k in fieldnames}
 if name=='stale_csv':csvrow['text']=base['text']
 with (out/'records.csv').open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fieldnames);w.writeheader();w.writerow(csvrow)
 cmd=[sys.executable,'-B',str(here/'audit.py'),'--records',str(out/'records.jsonl'),'--csv',str(out/'records.csv'),'--baseline',str(out/'baseline.jsonl'),'--out',str(out/'unexpected-pass.json')];run=subprocess.run(cmd,capture_output=True,text=True);(out/'stdout.log').write_text(run.stdout);(out/'stderr.log').write_text(run.stderr)
 expected={'old_detector_selected':'Canonical table selection differs','duplicate_canonical_word':'Canonical word ownership differs','changed_original_diagnostic':'Exact original fields were not preserved','wrong_source_binding':'Selection source binding mismatch','stale_csv':'CSV field differs'}[name]
 assert run.returncode!=0 and expected in run.stderr and not (out/'unexpected-pass.json').exists(),(name,run.returncode,run.stderr[-800:])
 results.append({'fault':name,'exit_code':run.returncode,'rejection':expected,'passed':True})
(here/'fault-results.json').write_text(json.dumps({'passed':True,'cases':results,'input_scope':'One actual corrected STO record and its exact retained diagnostic original; no synthetic legal content or parser imports','image_or_network_operations':False,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n');print(json.dumps(results,indent=2))
