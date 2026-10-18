#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess,sys,datetime
root=pathlib.Path(__file__).resolve().parent;cases=[]
for label,runtime in [('baseline-a',root/'baseline-runtime'),('baseline-b',root/'baseline-runtime'),('candidate-a',root),('candidate-b',root)]:
 with(root/(label+'.log')).open('wb')as log:
  result=subprocess.run([sys.executable,'-B',str(root/'probe_actual_charter.py'),'--runtime',str(runtime),'--source',str(root/'actual-charter'),'--out',str(root/label)],stdout=log,stderr=subprocess.STDOUT)
 cases.append({'label':label,'returncode':result.returncode});(root/'process-progress.json').write_text(json.dumps(cases,indent=2)+'\n')
 if result.returncode:raise SystemExit(result.returncode)
print(json.dumps(cases,indent=2))
