import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'MANIFEST.json').read_text())
for item in manifest['files']:
 p=(root/item['path']).resolve();assert p.is_relative_to(root) and p.is_file()
 assert sha(p)==item['sha256'],item['path']
summary=json.loads((root/'validation-summary.json').read_text());binding=summary['source_binding']
assert sha(root/'launcher-baseline.py')==binding['production_launcher_sha256']
assert sha(root/'launcher-candidate.py')==binding['candidate_launcher_sha256']
assert sha(root/'encodeplus-documents.py')==binding['provider_sha256']
asts=[ast.parse((root/f).read_text()) for f in ('launcher-baseline.py','launcher-candidate.py')]
for a in asts:a.body=[n for n in a.body if not isinstance(n,ast.FunctionDef) or n.name!='publication_acceptance']
assert ast.dump(asts[0])==ast.dump(asts[1])
assert summary['status']=='isolated_candidate_passed_not_promoted' and summary['tests']['passed']
assert summary['tests']['total']==46 and not summary['acquired_nonpdf_document_witness_claimed']
print(json.dumps({'passed':True,'read_only':True,'files':len(manifest['files']),'candidate_not_promoted':True,'only_acceptance_function_changed':True}))
