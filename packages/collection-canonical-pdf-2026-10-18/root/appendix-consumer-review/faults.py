"""Corrupt actual serialized output; original files remain untouched."""
import csv,hashlib,importlib.util,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('consumer',root/'audit.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
records,baseline,export,out=map(Path,sys.argv[1:])
rows=[json.loads(s) for s in records.read_text().split('\n') if s];prior=[json.loads(s) for s in baseline.read_text().split('\n') if s]
with export.open(newline='') as f:exports=list(csv.DictReader(f))
i=next(i for i,r in enumerate(rows) if r.get('canonical_structure_selection',{}).get('profile')=='sto_appendix_b' and r['physical_page']==199);r=rows[i];checks=[]
def reject(name,expected):
 try:m.audit(rows,prior,exports)
 except AssertionError as e:
  assert expected in str(e),(name,str(e));checks.append({'case':name,'rejected':True,'reason':str(e)})
 else:raise AssertionError('Accepted corrupt output '+name)
old=r['tables'][0]['header_rows'];r['tables'][0]['header_rows']=[0,1];reject('move_header_before_original_preheader','physical headers');r['tables'][0]['header_rows']=old
old=r['tables'][0]['cells'].pop();reject('drop_canonical_source_cell','source cells/order');r['tables'][0]['cells'].append(old)
q=r['superseded_detector_diagnostics']['original_record_fields']['pdf_qualification'];old=q['detected_table_count'];q['detected_table_count']+=1;reject('alter_retained_detector_evidence','old fields');q['detected_table_count']=old
old=exports[i]['text'];exports[i]['text']='stale prior export';reject('stale_csv','CSV differs');exports[i]['text']=old
c=m.audit(rows,prior,exports);assert c['canonical_false_cells']==44 and c['context_blocks']==9 and c['folio_blocks']==6
assert not out.exists();out.write_text(json.dumps({'passed':True,'tests':checks,'originals_unchanged':True,'audit_sha256':hashlib.sha256((root/'audit.py').read_bytes()).hexdigest(),'source_records_sha256':hashlib.sha256(records.read_bytes()).hexdigest()},indent=2)+'\n');print(json.dumps({'passed':True,'negative_cases':len(checks)}))
