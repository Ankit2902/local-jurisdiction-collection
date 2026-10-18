import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent;repo=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(repo/'collectors/ops/launcher.py')
env=dict(os.environ,COLLECTION_TEST_REPO=str(repo),PYTHONPATH=str(repo/'collectors/qa')+os.pathsep+str(repo),PYTHONDONTWRITEBYTECODE='1')
commands=[('focused',[sys.executable,'-B',str(root/'test_required_pdf_acceptance.py')]),('existing',[sys.executable,'-B','-m','unittest','collectors.qa.test_ops_acceptance','collectors.qa.test_ops_dependencies','collectors.qa.test_native_dispatch_upgrade','-v'])]
results=[]
for label,argv in commands:
 with (root/(label+'.stdout')).open('w') as out,(root/(label+'.stderr')).open('w') as err:
  result=subprocess.run(argv,cwd=repo,env=env,stdout=out,stderr=err)
 results.append({'label':label,'argv':argv,'exit':result.returncode});assert result.returncode==0,label
after=sha(repo/'collectors/ops/launcher.py');assert before==after
(root/'validation-summary.json').write_text(json.dumps({'passed':True,'production_writes':0,'publisher_requests':0,'launcher_before':before,'launcher_after':after,'test_sha256':sha(root/'test_required_pdf_acceptance.py'),'fixture_sha256':sha(root/'fixtures/overland-required-pdf-coverage.json'),'commands':results,'nonpdf_inspection':{'source':'collectors/encodeplus/documents.py','source_sha256':sha(repo/'collectors/encodeplus/documents.py'),'behavior':'Any non-PDF required binary receives only nonempty-byte integrity, explicitly semantics unqualified. DOCX/ZIP are not parsed semantically.','retained_coverage_scan_root':'outputs/collection-readiness-next-2026-10-17/encodeplus','retained_coverage_scan_matches':0,'qualification':'No actual retained non-PDF asset integrity entry found in this bounded coverage scan; source-supported limitation, not a claimed observed DOCX/ZIP semantic loss.','recommendation':'Treat non-PDF required documents separately from PDF dimensions and do not equate nonempty-byte capture with legal semantic qualification.'}},indent=2)+'\n')
print(json.dumps({'passed':True,'launcher_sha256':before,'test_sha256':sha(root/'test_required_pdf_acceptance.py'),'commands':results},indent=2))
