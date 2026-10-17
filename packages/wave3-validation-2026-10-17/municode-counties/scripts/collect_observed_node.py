"""One bounded observed legal node, exact primary publication/job/TOC binding."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('primary',type=Path);p.add_argument('node');p.add_argument('out',type=Path);a=p.parse_args();r=json.loads((a.primary/'receipt.json').read_text());assert r['status']=='acquired';assert not a.out.exists(),'Fresh output required'
found=[]
def walk(n):
 if n['Id']==a.node:found.append(n)
 for c in n.get('Children',[]):walk(c)
walk(json.loads((a.primary/'toc-full.json').read_text()));assert len(found)==1
api='https://library.municode.com/api/CodesContent?'+urlencode({'productId':r['product']['ProductID'],'jobId':r['job']['Id'],'nodeId':a.node,'groupChunks':'false'})
subprocess.run([os.environ.get('NODE','node'),str(ROOT/'scripts/acquire_node.cjs'),r['url'],api,str(a.out)],check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/normalize_supplemental.py'),str(a.primary),str(a.out)],check=True)
