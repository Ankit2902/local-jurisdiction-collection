import ast,difflib,hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent;project=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');repo=project/'github/local-jurisdiction-collection'
v3=project/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/overland-five-required-v3';official=project/'outputs/collection-readiness-post1997ee1-2026-10-17/official/inline-image-identity-candidate'
family=root/'candidate/collectors/encodeplus';family.mkdir(parents=True);(family.parent/'__init__.py').write_text('')
for p in (repo/'collectors/encodeplus').iterdir():
 if p.is_file() and p.suffix in ('.py','.cjs','.txt','.json'):shutil.copyfile(p,family/p.name)
for folder in ('configs','fixtures'):shutil.copytree(repo/'collectors/encodeplus'/folder,family/folder)
shutil.copyfile(repo/'collectors/encodeplus/pdf_structure.py',root/'production-pdf_structure.py');shutil.copyfile(v3/'collectors/encodeplus/pdf_structure.py',root/'reviewed-v3-pdf_structure.py')
source=(official/'pdf_structure.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='image_source_name');helper='\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])+'\n\n'
base=(root/'reviewed-v3-pdf_structure.py').read_text();assert base.count('def pages(')==1;candidate=base.replace('def pages(',helper+'def pages(')
old="'source_name':str(im.get('name',''))";assert candidate.count(old)==1;candidate=candidate.replace(old,"'source_name':image_source_name(im)");(family/'pdf_structure.py').write_text(candidate)
(root/'inline-source-name-only.patch').write_text(''.join(difflib.unified_diff(base.splitlines(True),candidate.splitlines(True),fromfile='a/collectors/encodeplus/pdf_structure.py',tofile='b/collectors/encodeplus/pdf_structure.py')))
(root/'production-to-v3.patch').write_text(''.join(difflib.unified_diff((root/'production-pdf_structure.py').read_text().splitlines(True),base.splitlines(True),fromfile='a/collectors/encodeplus/pdf_structure.py',tofile='b/collectors/encodeplus/pdf_structure.py')))
test=(official/'test_inline_image_identity.py').read_text().replace('from pdf_structure import image_source_name','from .pdf_structure import image_source_name');(family/'test_inline_image_identity.py').write_text(test)
actual=root/'actual-charter';actual.mkdir();shutil.copyfile(official/'actual-charter/raw/a9c1009082d8cf915a93.bin',actual/'source.pdf')
for name in ('item.json','config.json'):shutil.copyfile(official/'actual-charter'/name,actual/name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(root/'source-binding.json').write_text(json.dumps({'production_parser_sha256':sha(root/'production-pdf_structure.py'),'v3_parser_sha256':sha(root/'reviewed-v3-pdf_structure.py'),'inline_candidate_parser_sha256':sha(family/'pdf_structure.py'),'official_parser_sha256':sha(official/'pdf_structure.py'),'actual_charter_source_sha256':sha(actual/'source.pdf'),'v3_input_directory':str(v3.relative_to(project)),'inline_helper_ast_exact_official':ast.dump(ast.parse(helper))==ast.dump(ast.Module(body=[node],type_ignores=[]))},indent=2)+'\n')
print((root/'source-binding.json').read_text())
