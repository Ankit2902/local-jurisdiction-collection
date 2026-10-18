import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((R/'MANIFEST.json').read_text())
for e in m['files']:
 p=R/e['path'];assert p.is_file() and sha(p)==e['sha256'] and p.stat().st_size==e['bytes']
r=json.loads((R/'review.json').read_text());assert r['material_extractor_blockers_found']==[] and r['all_source_bytes_unchanged'] and r['source_files_including_manifest']==97
assert r['native_audit']['passed'] and r['native_audit']['independent_review_tripwire_calls']==[] and r['fault_tests']['tests']==21 and r['fault_tests']['exit']==0
assert r['separate_consumer_checks']['canonical_units']==88 and r['separate_consumer_checks']['glyphs']==15574 and r['separate_consumer_checks']['MCIDrefs']==109
assert r['separate_consumer_checks']['wholepublication_acceptance'] is False and r['separate_consumer_checks']['edition_currentness_qualified'] is False
assert json.loads((R/'candidate-before.json').read_text())==json.loads((R/'candidate-after.json').read_text())
print(json.dumps({'passed':True,'files':len(m['files']),'manifest_sha256':sha(R/'MANIFEST.json'),'production_writes':0,'publisher_requests':0,'wholepublication_accepted':False},sort_keys=True))
