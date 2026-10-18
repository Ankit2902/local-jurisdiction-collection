"""Portable read-only compact review verification, no native parser/network imports."""
import ast,hashlib,json,re
from pathlib import Path
root=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'MANIFEST.json').read_text())
for item in manifest['files']:
 path=(root/item['path']).resolve();assert path.is_relative_to(root) and path.is_file(),item['path'];assert sha(path)==item['sha256'],item['path']
summary=json.loads((root/'validation-summary.json').read_text());plan=json.loads((root/'FINAL-PROMOTION-PLAN.json').read_text())
assert summary['status']=='independent_review_and_final56_passed_isolated_candidate_not_promoted'
assert plan['status']=='final56_passed_ready_for_root_promotion' and not plan['deletions']
for item in plan['whitelist']:assert sha(root/item['source'])==item['candidate_sha256']
assert len(plan['whitelist'])==4
log=(root/'final-family56.stderr').read_text();assert re.search(r'Ran 56 tests in 96\.340s\n\nOK\s*$',log)
assert sha(root/'final-family56.stderr')==plan['final_test_log_sha256']
invariants=json.loads((root/'v3-independent-invariants.json').read_text());counts=invariants['counts']
assert invariants['passed'] and counts['pages']==636 and counts['cells']==6248 and counts['cell_disagreements']==795 and counts['image_placeholders']==201
assert len(invariants['fullprecision_native_queries'])==5 and not invariants['forbidden_calls']
repeat=json.loads((root/'inline-independent-repeatability.json').read_text());assert repeat['passed'] and repeat['candidate_crossprocess_bytes_identical']
assert repeat['baseline_crossprocess_differences']==7 and repeat['all_other_record_fields_unchanged'] and repeat['image_placeholders_unchanged']==10
assert (root/'candidate-a/records.jsonl').read_bytes()==(root/'candidate-b/records.jsonl').read_bytes()
assert all(not json.loads((root/label/'report.json').read_text())['forbidden_calls'] for label in ('baseline-a','baseline-b','candidate-a','candidate-b'))
exposure=json.loads((root/'overland-image-name-exposure-owner.json').read_text());assert exposure['passed']
xrefs=json.loads((root/'overland-named-resource-equivalence.json').read_text());assert xrefs['passed'] and xrefs['named_occurrences']==201 and not xrefs['forbidden_calls']
assert summary['image_policy']['placeholder']=='[IMAGE]' and not summary['image_policy']['separate_image_acquisition']
assert all(v['before_diagnostic_guard']==v['after_diagnostic_guard'] for v in summary['five_document_aggregate_guard_invariants'].values())
print(json.dumps({'passed':True,'read_only':True,'files':len(manifest['files']),'final_exact_source_tests':56,'promotion_whitelist':4,'no_legal_semantic_promotion':True}))
