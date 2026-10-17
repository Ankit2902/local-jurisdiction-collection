"""Extract source scope terms as evidence, never infer blanket territorial application."""
import json,re
from pathlib import Path
from collect_all import ROOT,ASSIGNMENT,slug
rows=[]
for a in ASSIGNMENT:
 if a['sequence'] not in [76,77,93,95,96,97]:continue
 matches=[]
 files=[ROOT/'browser'/slug(a)/'normalized/sections.jsonl']
 if a['sequence']==93:files += [ROOT/'supplemental/los-angeles-county-jurisdiction/normalized/sections.jsonl']
 if a['sequence']==95:files += list((ROOT/'native').glob('baton-rouge-*/normalized/pages.jsonl'))
 if a['sequence']==96:files += [ROOT/'native/clark-title30/normalized/pages.jsonl']
 for p in files:
  if not p.exists():continue
  for line in p.read_text().splitlines():
   r=json.loads(line);text=re.sub(r'\s+',' ',r['text'])
   terms=list(re.finditer(r'\b(?:unincorporated|incorporated|city.parish|parish|county|city limits|corporate limits|boundaries)\b',text,re.I))
   for m in terms[:3]:matches.append({'record_file':str(p.relative_to(ROOT)),'record_id':r.get('node_id',r.get('identifier')),'record_unit':r.get('record_unit','legal provision'),'source_url':r['source_url'],'observed_term':m.group(),'source_excerpt':text[max(0,m.start()-90):m.end()+190]})
 rows.append({'sequence':a['sequence'],'jurisdiction':a['jurisdiction'],'entity_type':a['entity_type'],'assignment_boundary_note':a['boundary_note'],'source_term_evidence':matches[:15],'specific_provision_scope_observed':('Los Angeles County10.04.070 explicitly states Title10 enforced in all unincorporated county areas and Title10/portions in contract cities as applicable; applies to Title10 only, not a blanket rule for all county enactments.' if a['sequence']==93 and (ROOT/'supplemental/los-angeles-county-jurisdiction/receipt.json').exists() else None),'blanket_territorial_applicability_validated':False,'finding':'Source excerpts preserve territorial/organizational wording only. County enactments are separate legal layers; incorporated/unincorporated applicability and combined city/parish scope require provision-specific interpretation. No county/city population sum and no city-only population for combined target.'})
(ROOT/'territorial-applicability-evidence.json').write_text(json.dumps(rows,indent=2))
