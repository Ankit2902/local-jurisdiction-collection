import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
project=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00')
repo=project/'github/local-jurisdiction-collection'
previous=project/'outputs/collection-readiness-post-91f6c59-2026-10-17/ep-named-config-binding-candidate-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rels=['collectors/ops/launcher.py','collectors/qa/readiness_binding.py','collectors/registry/dispatch.py']
inputs=['collectors/encodeplus/targets.json','collectors/registry/publications.json','collectors/registry/targets.json']
stage=root/'promotion-test-layout'
for rel in rels+inputs:
 dest=stage/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile((previous/'candidate'/rel) if rel in rels else repo/rel,dest)
# The focused test is self-contained after installation at this normal repo path.
dest=stage/'collectors/qa/test_named_encodeplus_binding.py';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/dest.name,dest)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',COLLECTION_TEST_REPO=str(repo))
with (root/'current-prepromotion.stdout').open('w') as out,(root/'current-prepromotion.stderr').open('w') as err:
 negative=subprocess.run([sys.executable,'-B',str(root/dest.name)],env=env,stdout=out,stderr=err)
assert negative.returncode!=0,'Regression must detect current prepromotion omission'
env.pop('COLLECTION_TEST_REPO')
with (root/'postpromotion-layout.stdout').open('w') as out,(root/'postpromotion-layout.stderr').open('w') as err:
 positive=subprocess.run([sys.executable,'-B',str(dest)],env=env,stdout=out,stderr=err)
assert positive.returncode==0,'Candidate failed normal installed-layout tests'
# Existing suite imports readiness_binding from its normal neighboring directory.
shutil.copyfile(repo/'collectors/qa/test_readiness_binding.py',stage/'collectors/qa/test_readiness_binding.py')
with (root/'existing-suite.stdout').open('w') as out,(root/'existing-suite.stderr').open('w') as err:
 existing=subprocess.run([sys.executable,'-B',str(stage/'collectors/qa/test_readiness_binding.py')],env=env,stdout=out,stderr=err)
assert existing.returncode==0
baseline=json.loads((previous/'source-baseline.json').read_text())
assert all(sha(repo/rel)==expected for rel,expected in baseline.items()),'Production changed'
report={'status':'repository_ready_regression_prepared_not_promoted','production_modified':False,'publisher_requests':0,'regression_file':'test_named_encodeplus_binding.py','regression_sha256':sha(root/dest.name),'prepromotion_production_test_exit':negative.returncode,'postpromotion_normal_layout_test_exit':positive.returncode,'focused_tests':7,'existing_tests':16,'existing_exit':existing.returncode,'source_modules':{rel:sha(stage/rel) for rel in rels},'current_inputs':{rel:sha(repo/rel) for rel in inputs},'production_baselines_unchanged':baseline,'exact_postpromotion_command':".collection-runtime/venv/bin/python -B -m unittest discover -s collectors/qa -p 'test_named_encodeplus_binding.py' -v",'exact_existing_test_command':".collection-runtime/venv/bin/python -B -m unittest discover -s collectors/qa -p 'test_readiness_binding.py' -v"}
(root/'validation-summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
