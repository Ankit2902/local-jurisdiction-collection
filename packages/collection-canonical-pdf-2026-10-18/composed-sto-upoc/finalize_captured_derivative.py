"""Finish captured native-output evidence read-only; no PDF/native APIs invoked."""
import collections,copy,csv,hashlib,io,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'candidate'))
from collectors.encodeplus import upoc_printed_index as scoped
from collectors.encodeplus.native_document import outputs
P=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');V=P/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/overland-five-required-v3';sha=lambda b:hashlib.sha256(b).hexdigest();canon=lambda v:json.loads(json.dumps(v));csha=lambda v:sha(json.dumps(v,sort_keys=True).encode());load=lambda p:[json.loads(l) for l in p.read_text().splitlines()]
base=load(V/'records.jsonl');sto=load(R/'source-STO-canonical-three-pages.jsonl');sto_by={r['id']:r for r in sto};rows=load(R/'derived-records.jsonl');changed=load(R/'changed-four-pages.jsonl');combined=load(R/'combined-changed-seven-pages.jsonl');counts=collections.Counter();proofs=[];native_regions=[]
assert len(base)==len(rows)==636 and len(sto)==3 and len(changed)==4 and len(combined)==7
for b,r in zip(base,rows):
 assert b['id']==r['id'];prior=copy.deepcopy(sto_by.get(b['id'],b));selected=r.get('canonical_structure_selection',{}).get('profile')=='upoc_printed_index'
 if selected:
  x=r['source_printed_indexes'][0];bare=copy.deepcopy(x);bare.pop('source_binding');bare.pop('detector_evidence_disposition');pin=scoped.PROFILES[r['raw_sha256']]['pins'][r['physical_page']]
  assert scoped._region_digest(bare,r['id'],r['document_id'])==pin['region_sha256'],'Captured native field/word/glyph/query fingerprint changed'
  assert r['superseded_detector_diagnostics']['original_record_fields']=={k:prior[k] for k in ['tables','ordered_blocks','text','ordering','pdf_qualification']}
  expected=copy.deepcopy(prior);expected.update(scoped._canonical_projection(prior,x));expected['source_printed_indexes']=[x];assert canon(expected)==r,'Canonical projection differs from actualexport'
  native_regions.append({'id':r['id'],'region_sha256':pin['region_sha256'],'native_text_sha256':pin['native_text_sha256'],'old_failed_cells':pin['old_failed_cells']})
 else:assert prior==r,'Non-UPOC output changed'
 assert [x for x in r['ordered_blocks'] if x['kind']=='image_placeholder']==[x for x in b['ordered_blocks'] if x['kind']=='image_placeholder']
 original_fields=r.get('superseded_detector_diagnostics',{}).get('original_record_fields');original_tables=original_fields['tables'] if original_fields else r['tables'];assert original_tables==b['tables']
 counts['original_false_cell_payloads_preserved']+=sum(not c['independent_character_agreement'] for t in original_tables for c in t['cells']);counts['image_placeholders_preserved']+=r['image_placeholder_count'];counts['records']+=1;counts['new_UPOC_canonical_selections']+=selected;counts['prior_STO_canonical_selections_preserved']+=r['id'] in sto_by
 proofs.append({'id':r['id'],'before_UPOC_canonical_sha256':csha(prior),'after_sha256':csha(r),'new_UPOC_selection':selected,'prior_STO_selection_preserved':r['id'] in sto_by,'nonselected_record_exact':not selected and r==prior,'original_detector_tables_sha256':csha(b['tables']),'preserved_detector_tables_sha256':csha(original_tables)})
assert counts==dict(records=636,new_UPOC_canonical_selections=4,prior_STO_canonical_selections_preserved=3,image_placeholders_preserved=201,original_false_cell_payloads_preserved=795)
assert [r for r in rows if r.get('canonical_structure_selection',{}).get('profile')=='upoc_printed_index']==changed
assert [r for r in rows if r['id'] in sto_by or r.get('canonical_structure_selection',{}).get('profile')=='upoc_printed_index']==combined
for name,body in outputs(rows).items():assert (R/('derived-'+name)).read_bytes()==body,'Operational outputs serializer differs'
assert [r['text'] for r in csv.DictReader(io.StringIO((R/'derived-records.csv').read_text()))]==[r['text'] for r in rows]
report={'passed':True,'scope':'Retained636IR composed from exactSTO3sourceoutputs plus4actualnativeUPOCqueries; notfull636reparse/liveacquisition','capture_execution':'Native capture/invariant checks/exports completed; subsequentPythoncolor-tuple-vsJSONarray harness assertion failed. Original script/log retained; this offline finalizer proves exactexports/projection/fingerprints without secondnativeparse.','input_records_sha256':sha((V/'records.jsonl').read_bytes()),'supplied_STO_records_sha256':sha((R/'source-STO-canonical-three-pages.jsonl').read_bytes()),'helper_sha256':sha((R/'candidate/collectors/encodeplus/upoc_printed_index.py').read_bytes()),'counts':dict(counts),'unchanged_by_UPOC':632,'original_noop_records':629,'dimensions':scoped.summary(changed),'canonical_CSV_JSON_serializer_byte_exact':True,'captured_native_region_fingerprints':native_regions,'native_capture_forbidden_calls':[],'native_queries_in_this_finalizer':0,'original_table_diagnostic_lineage_unchanged':True,'image_markers_position_ownership_unchanged':True,'per_record_proof':proofs,'derived_jsonl_sha256':sha((R/'derived-records.jsonl').read_bytes()),'derived_csv_sha256':sha((R/'derived-records.csv').read_bytes()),'changed_four_sha256':sha((R/'changed-four-pages.jsonl').read_bytes()),'combined_seven_sha256':sha((R/'combined-changed-seven-pages.jsonl').read_bytes())}
(R/'actual-canonical-differential.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='per_record_proof'},indent=2))
