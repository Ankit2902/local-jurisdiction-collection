"""Reuse636retainedIR+onefreshfull6logicalcapture; no native parsing or transport."""
import copy,hashlib,json,pathlib,sys
R=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(R/'candidate'))
from collectors.encodeplus.native_document import outputs
P=pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/collection-readiness-post1997ee1-2026-10-17/official/infrastructure-canonical-candidate-v2/derivative-current/records.jsonl');sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(P.read_bytes())=='95e28ea3fa4a60f30cf6b55a33d12f49ca04c3b6895ceca85bfe43af3355d58a'
base=[json.loads(l) for l in P.read_text().splitlines()];logical=[json.loads(l) for l in (R/'actual-full6/records.jsonl').read_text().splitlines()];source=logical[0]['raw_sha256'];old=[r for r in base if r['raw_sha256']==source];assert len(base)==636 and len(logical)==88 and len(old)==6 and [r['physical_page'] for r in old]==list(range(1,7))
logical=copy.deepcopy(logical)
for r in logical:r['source_asset_document_id']=old[0]['document_id']
logical[0]['mixed_source_diagnostic_lineage']={'schema_version':1,'reason':'Exact priorasset-page IR preserved separately from source-specific standalone6page diagnostics; only thissource6page group replaced with88logicalunits. No parentHTMLasset acceptance credit.','source_baseline_sha256':sha(P.read_bytes()),'original_asset_page_records':old}
rows=[];emitted=False;proof=[]
for r in base:
 if r['raw_sha256']==source:
  if not emitted:rows.extend(logical);emitted=True
 else:rows.append(r);proof.append({'id':r['id'],'before_sha256':sha(json.dumps(r,sort_keys=True).encode()),'after_sha256':sha(json.dumps(rows[-1],sort_keys=True).encode())})
assert len(rows)==718 and len(proof)==630
out=R/'derivative-mixed718';out.mkdir(exist_ok=True)
for n,b in outputs(rows).items():(out/n).write_bytes(b)
assert [json.loads(l) for l in (out/'records.jsonl').read_text().splitlines()]==rows
before_images=[(r['id'],b) for r in base for b in r.get('ordered_blocks',[]) if b['kind']=='image_placeholder'];after_images=[(r['id'],b) for r in rows for b in r.get('ordered_blocks',[]) if b['kind']=='image_placeholder'];assert before_images==after_images and len(before_images)==201
others=[r for r in rows if r.get('unit')!='pdf_logical_unit'];assert others==[r for r in base if r['raw_sha256']!=source];assert sum('canonical_structure_selection' in r for r in others)==17
report={'passed':True,'scope':'RetainedIRprojection only; oneexistingactualfull6sourcecapture reused, zero newPDFparses/network/imageoperations','input_sha256':sha(P.read_bytes()),'input_records':636,'output_records':718,'replaced_physical_source_pages':6,'new_logical_records':88,'unchanged_other_records':630,'existing_canonical_selections_preserved':17,'images_position_and_ownership_unchanged':201,'old6asset_page_records_exact':True,'original6native_page_records_also_retained':True,'own_native_text_complete':True,'required_external_documents_complete':False,'edition_currentness_qualified':False,'wholepublication_complete':False,'per_other_record_proof':proof,'outputs':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in out.iterdir()}}
(R/'mixed718-differential.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['per_other_record_proof','outputs']},indent=2))
