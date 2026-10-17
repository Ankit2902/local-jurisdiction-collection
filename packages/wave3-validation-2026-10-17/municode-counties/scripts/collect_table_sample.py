"""Acquire one observed table candidate, pinned to current primary TOC and job."""
import json,os,subprocess,sys
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'browser/richmond';r=json.loads((p/'receipt.json').read_text());nid='CH30ZO_ARTVIIOREPALORE_DIV2OREPARE_S30-710.3_1DIPASP';found=[]
def walk(n):
 if n['Id']==nid:found.append(n)
 for c in n.get('Children',[]):walk(c)
walk(json.loads((p/'toc-full.json').read_text()));assert len(found)==1,'Observed node not present'
out=ROOT/'supplemental/richmond-parking-dimensions';assert not out.exists(),'Use a new output path'
api='https://library.municode.com/api/CodesContent?'+urlencode({'productId':r['product']['ProductID'],'jobId':r['job']['Id'],'nodeId':nid,'groupChunks':'false'})
subprocess.run([os.environ.get('NODE','node'),str(ROOT/'scripts/acquire_node.cjs'),r['url'],api,str(out)],check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/normalize_supplemental.py'),str(p),str(out)],check=True)
subprocess.run([os.environ.get('NODE','node'),str(ROOT/'scripts/verify_tables.cjs'),str(out),str(ROOT/'evidence/table-dom-richmond')],check=True)
