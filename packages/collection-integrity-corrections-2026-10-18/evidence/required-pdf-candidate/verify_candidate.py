"""Read-only compact evidence integrity; no repository/runtime/network required."""
import ast,difflib,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'MANIFEST.json').read_text())
for item in manifest['files']:
 path=(root/item['path']).resolve()
 assert path.is_relative_to(root) and path.is_file(),item['path']
 assert sha(path)==item['sha256'],item['path']
binding=json.loads((root/'source-binding.json').read_text());summary=json.loads((root/'validation-summary.json').read_text())
assert sha(root/'launcher-baseline.py')==binding['production_launcher_sha256']
assert sha(root/'launcher-candidate.py')==binding['candidate_launcher_sha256']
assert sha(root/'fixtures/overland-coverage.json')==binding['actual_coverage_sha256']
asts=[ast.parse((root/file).read_text()) for file in ('launcher-baseline.py','launcher-candidate.py')]
for parsed in asts:parsed.body=[n for n in parsed.body if not isinstance(n,ast.FunctionDef) or n.name!='publication_acceptance']
assert ast.dump(asts[0])==ast.dump(asts[1])
assert summary['status']=='isolated_candidate_passed_not_promoted' and summary['tests']['passed']
comparison=json.loads((root/'actual-overland-acceptance-comparison.json').read_text())
assert comparison['baseline']['publication_coverage_accepted'] and not comparison['candidate']['publication_coverage_accepted']
assert comparison['candidate']['publication_text_complete'] and comparison['candidate']['required_nonimage_documents_complete']
assert not comparison['candidate']['legal_structure_qualified']
print(json.dumps({'passed':True,'read_only':True,'files':len(manifest['files']),'actual_false_acceptance_reproduced':True,'candidate_not_promoted':True}))
