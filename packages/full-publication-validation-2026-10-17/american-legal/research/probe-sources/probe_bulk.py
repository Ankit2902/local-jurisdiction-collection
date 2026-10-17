import subprocess,json,base64,os,sys,re,hashlib
from pathlib import Path
base=Path(__file__).resolve().parent;out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
for name in ['browser.cjs','gate.py','probe_bulk.py']:
 q=base/name;(out/(hashlib.sha256(q.read_bytes()).hexdigest()+q.suffix)).write_bytes(q.read_bytes())
p=subprocess.Popen([os.environ.get('NODE_BIN','node'),str(base/'browser.cjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
def call(name,cmd):
 p.stdin.write(json.dumps(cmd)+'\n');p.stdin.flush();r=json.loads(p.stdout.readline());print(name,r.get('ok'),r.get('error'),flush=True);(out/(name+'.json')).write_text(json.dumps(r));assert r['ok'],r
 b=base64.b64decode(r['result']['body']);(out/(name+'.bin')).write_bytes(b);return b
try:
 data=call('overview',{'op':'navigate','url':'https://codelibrary.amlegal.com/codes/cleveland/latest/overview'});state=json.loads(json.loads(re.search(r'window\._redux_state = JSON\.parse\(("(?:[^"\\]|\\.)*")',data.decode()).group(1)));v=state['codes']['selectedVersion'];c=v['toc'][0];call('native-bulk',{'op':'export','url':f"https://codelibrary.amlegal.com/codes/cleveland/{v['uuid']}/{c['slug']}/{c['sections'][0]['doc_id']}",'code_uuid':c['uuid'],'code_slug':c['slug'],'version':v['uuid']})
finally:
 p.stdin.write('{"op":"close"}\n');p.stdin.flush();print(p.stdout.readline(),flush=True);p.wait()
