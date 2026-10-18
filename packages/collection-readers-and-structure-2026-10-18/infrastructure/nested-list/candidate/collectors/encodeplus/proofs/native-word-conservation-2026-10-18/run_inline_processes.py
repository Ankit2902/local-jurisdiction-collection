import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent;results=[]
for label,parser in [('baseline-a',root/'reviewed-v3-pdf_structure.py'),('baseline-b',root/'reviewed-v3-pdf_structure.py'),('candidate-a',root/'candidate/collectors/encodeplus/pdf_structure.py'),('candidate-b',root/'candidate/collectors/encodeplus/pdf_structure.py')]:
 argv=[sys.executable,'-B',str(root/'probe_selected_inline.py'),'--parser',str(parser),'--out',str(root/label)]
 with (root/(label+'.log')).open('w') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
 results.append({'label':label,'exit':r.returncode});(root/'inline-processes.json').write_text(json.dumps(results,indent=2)+'\n');assert r.returncode==0,label
