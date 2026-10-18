"""Source-bound adopted model-layer candidates, no traffic or implied qualification."""
import json,re
from pathlib import Path
from source_common import save,sha
ROOT=Path(__file__).resolve().parent
PATTERN=re.compile(r'International\s+(?:Building|Residential|Fire|Plumbing|Mechanical|Fuel\s+Gas|Existing\s+Building|Energy\s+Conservation|Swimming\s+Pool\s+and\s+Spa|Property\s+Maintenance)\s+Code|Uniform\s+(?:Plumbing|Mechanical)\s+Code|National\s+Electrical\s+Code',re.I)
def run():
 rows=[]
 for name in ['flagstaff-html-normalized-qualified-v3','king-county-normalized-final-v6']:
  source=ROOT/'evidence'/name/'records.jsonl'
  for line in source.open():
   r=json.loads(line);text=r.get('full_text','');matches=list(PATTERN.finditer(text))
   if not matches:continue
   rows.append({'record_id':r['record_id'],'source_url':r['source_url'],'source_sha256':r.get('source_sha256'),'heading':r.get('heading'),'normalized_stream':str(source.relative_to(ROOT)),'matches':[{'literal_name':m.group(),'source_context':text[max(0,m.start()-180):min(len(text),m.end()+240)]} for m in matches],'status':'source_mentioned_external_model_layer_not_collected_or_edition_qualified','boundary':'Primary local published wording retained; external model-code legal dependency requires separate adoption/edition/source qualification, never inferred from title alone.'})
 ledger=json.loads((ROOT/'family-ledger-final.json').read_text());ledger['external_model_layer_candidates']={'status':'candidate mention inventory; not a complete adoption/edition or attachment qualification','model_name_pattern':PATTERN.pattern,'records':len(rows),'evidence':'evidence/adopted-model-layer-candidates.json','whole_legal_dependency_closure_complete':False};save(ROOT/'evidence/adopted-model-layer-candidates.json',{'schema':'source-adopted-model-candidates-1','qualified':False,'records':rows});save(ROOT/'family-ledger-final.json',ledger);return {'candidate_records':len(rows)}
if __name__=='__main__':print(json.dumps(run()))
