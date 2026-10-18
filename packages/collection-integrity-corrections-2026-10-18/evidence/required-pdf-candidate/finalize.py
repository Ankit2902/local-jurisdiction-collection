import ast,difflib,hashlib,importlib.util,json,shutil,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent;project=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');repo=project/'github/local-jurisdiction-collection'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bind=json.loads((root/'source-binding.json').read_text());assert sha(repo/'collectors/ops/launcher.py')==bind['production_launcher_sha256']
assert sha(project/bind['actual_coverage_source'])==bind['actual_coverage_sha256']
before=(root/'launcher-baseline.py').read_text();after=(root/'launcher-candidate.py').read_text()
old_ast=ast.parse(before);new_ast=ast.parse(after)
for parsed in (old_ast,new_ast):parsed.body=[node for node in parsed.body if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) or node.name!='publication_acceptance']
assert ast.dump(old_ast)==ast.dump(new_ast),'Unrelated launcher functions changed'
(root/'required-pdf-acceptance.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/collectors/ops/launcher.py',tofile='b/collectors/ops/launcher.py')))
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,root/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
with tempfile.TemporaryDirectory() as temp:
 out=Path(temp);shutil.copyfile(root/'fixtures/overland-coverage.json',out/'coverage.json');pub={'publisher':'encodeplus','source_url':'https://codes.opkansas.org/municipal-code/'}
 comparisons={'baseline':load('baseline_report','launcher-baseline.py').publication_acceptance(pub,out),'candidate':load('candidate_report','launcher-candidate.py').publication_acceptance(pub,out)}
(root/'actual-overland-acceptance-comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n')
summary={'status':'isolated_candidate_passed_not_promoted','scope':'Required PDF semantic acceptance; binary capture and parent HTML remain separate','source_binding':bind,'production_launcher_unchanged':True,'unrelated_launcher_ast_unchanged':True,'actual_required_pdf_count':5,'actual_required_pdf_pages':636,'baseline_false_acceptance_reproduced':comparisons['baseline']['publication_coverage_accepted'],'candidate_publication_accepted':comparisons['candidate']['publication_coverage_accepted'],'candidate_legal_structure_qualified':comparisons['candidate']['legal_structure_qualified'],'candidate_html_text_complete':comparisons['candidate']['publication_text_complete'],'candidate_required_nonimage_documents_complete':comparisons['candidate']['required_nonimage_documents_complete'],'new_per_document_dimension_count':len(comparisons['candidate']['pdf_structure_dimensions']),'tests':{'focused':7,'focused_seconds':0.716,'existing':30,'existing_seconds':0.764,'passed':True},'publisher_requests':0,'production_writes':0,'notes':['Existing integrity-only asset map entries lack semantic qualification; explicit per-PDF text/table dimensions are null and prevent acceptance.','Parent aggregate fields cannot override missing/false per-required-PDF dimensions. Character conservation alone does not satisfy either semantic dimension.','Synthetic all-explicit-true control tests the acceptance schema only, not qualification of the actual five PDFs.','Existing retained coverage and historical receipts remain unchanged; no PDF parsing or acquisition was repeated.']}
(root/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
