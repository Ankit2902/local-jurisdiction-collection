from pathlib import Path
import hashlib,json,shutil
P=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');repo=P/'github/local-jurisdiction-collection';src=P/'outputs/collection-readiness-post-1997ee1-2026-10-17/american-legal/overland-solid-waste-logical-v1';r=P/'outputs/collection-readiness-post1997ee1-2026-10-17/solid-waste-production-integration-candidate-v1';r.mkdir(exist_ok=True);ep=r/'candidate/collectors/encodeplus';assert not ep.exists();ep.mkdir(parents=True)
for x in (repo/'collectors/encodeplus').iterdir():
 if x.is_file() and x.suffix in ['.py','.json','.txt','.cjs']:shutil.copy2(x,ep/x.name)
for n in ['fixtures','configs']:shutil.copytree(repo/'collectors/encodeplus'/n,ep/n)
for n in ['native_document.py','requirements.txt']:shutil.copy2(ep/n,r/('baseline-'+n))
mods={'extract_logical':'solid_waste_extract','profile':'solid_waste_profile','pdf_tags':'solid_waste_tags','pdf_glyphs':'solid_waste_glyphs','source_inventory':'solid_waste_inventory','pdf_native':'solid_waste_native','independent_audit':'solid_waste_audit'}
for old,new in mods.items():
 s=(src/'source'/(old+'.py')).read_text()
 if old=='extract_logical':s=s.replace('import pdf_glyphs,pdf_tags,profile,source_inventory','from . import solid_waste_glyphs as pdf_glyphs,solid_waste_tags as pdf_tags,solid_waste_profile as profile,solid_waste_inventory as source_inventory')
 if old=='independent_audit':s=s.replace('import pdf_native','from . import solid_waste_native as pdf_native')
 (ep/(new+'.py')).write_text(s)
f=ep/'fixtures/solid-waste-logical';f.mkdir();shutil.copy2(src/'source.pdf',f/'source.pdf');shutil.copy2(src/'SUMMARY.json',f/'reviewed-source-summary.json');shutil.copy2(src/'final-execution-v2.json',f/'reviewed-execution.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();bindings={'production_parser_sha256':sha(repo/'collectors/encodeplus/pdf_structure.py'),'production_native_sha256':sha(ep/'native_document.py'),'reviewed_source_manifest_sha256':sha(src/'MANIFEST.json'),'source_sha256':sha(src/'source.pdf'),'modules':{old:{'source_sha256':sha(src/'source'/(old+'.py')),'adapted_module':new+'.py','candidate_sha256':sha(ep/(new+'.py'))} for old,new in mods.items()}}
(r/'source-binding.json').write_text(json.dumps(bindings,indent=2)+'\n')
# Compact reviewed canonical fixtures are JSON text only.
import gzip
for name in ['logical-units.jsonl','source-controls.jsonl']:(f/(name+'.gz')).write_bytes(gzip.compress((src/'canonical-final-v2'/name).read_bytes(),mtime=0))
shutil.copy2('/tmp/prepare_solidwaste_integration.py',r/'prepare.py');print(r)
