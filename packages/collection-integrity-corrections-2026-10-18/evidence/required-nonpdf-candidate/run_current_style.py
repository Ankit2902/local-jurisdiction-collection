import json,os,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
stage=root/'test-repository'
for source,rel in [('launcher-candidate.py','collectors/ops/launcher.py'),('encodeplus-documents.py','collectors/encodeplus/documents.py')]:
 p=stage/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/source,p)
# Exercise the current-import durable tests against a normal source tree.
pdf=root.parent/'required-pdf-acceptance-regression-v1'
dest=stage/'collectors/qa';(dest/'fixtures').mkdir(parents=True,exist_ok=True)
shutil.copyfile(pdf/'test_required_pdf_acceptance.py',dest/'test_required_pdf_acceptance.py')
shutil.copyfile(pdf/'fixtures/overland-required-pdf-coverage.json',dest/'fixtures/overland-required-pdf-coverage.json')
shutil.copyfile(root/'test_required_nonpdf_acceptance_current.py',dest/'test_required_nonpdf_acceptance.py')
results=[]
for label,name in [('durable-nonpdf','test_required_nonpdf_acceptance.py'),('durable-actual-pdf','test_required_pdf_acceptance.py')]:
 with (root/(label+'.stdout')).open('w') as out,(root/(label+'.stderr')).open('w') as err:
  result=subprocess.run([sys.executable,'-B',str(dest/name)],env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=err)
 results.append({'label':label,'exit':result.returncode});assert result.returncode==0,label
(root/'durable-tests.json').write_text(json.dumps(results,indent=2)+'\n')
