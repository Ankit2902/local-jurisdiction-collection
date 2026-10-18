import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent;repo=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rels=['collectors/ops/launcher.py','collectors/qa/readiness_binding.py','collectors/registry/dispatch.py']
before={rel:sha(repo/rel) for rel in rels}
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',COLLECTION_TEST_REPO=str(repo),PYTHONPATH=str(repo/'collectors/qa')+os.pathsep+str(repo))
commands=[('production-focused',[sys.executable,'-B',str(root/'test_named_encodeplus_binding.py')]),('production-existing',[sys.executable,'-B','-m','unittest','collectors.qa.test_ops_acceptance','collectors.qa.test_ops_dependencies','collectors.qa.test_readiness_binding','collectors.qa.test_native_dispatch_upgrade','collectors.qa.test_originals_dispatch','collectors.qa.test_readiness_catalog','-v'])]
results=[]
for name,argv in commands:
 with (root/(name+'.stdout')).open('w') as out,(root/(name+'.stderr')).open('w') as err:
  run=subprocess.run(argv,cwd=repo,env=env,stdout=out,stderr=err)
 results.append({'name':name,'argv':argv,'exit':run.returncode,'stdout':name+'.stdout','stderr':name+'.stderr'})
 assert run.returncode==0,(name,run.returncode)
after={rel:sha(repo/rel) for rel in rels};assert before==after
(root/'current-production-validation.json').write_text(json.dumps({'passed':True,'production_modified':False,'no_live_collection':True,'python':sys.version,'source_before':before,'source_after':after,'commands':results},indent=2)+'\n')
print(json.dumps({'passed':True,'source_unchanged':True,'commands':results},indent=2))
