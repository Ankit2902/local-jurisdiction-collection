import subprocess,json,base64,os,sys,re,hashlib
from pathlib import Path
b=Path(__file__).resolve().parent;out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
for n in ['browser.cjs','gate.py','probe_routes.py']:
 q=b/n;(out/(hashlib.sha256(q.read_bytes()).hexdigest()+q.suffix)).write_bytes(q.read_bytes())
p=subprocess.Popen([os.environ.get('NODE_BIN','node'),str(b/'browser.cjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
def call(name,op,url):
 p.stdin.write(json.dumps({'op':op,'url':url})+'\n');p.stdin.flush();r=json.loads(p.stdout.readline());print(name,r.get('ok'),flush=True);(out/(name+'.response.json')).write_text(json.dumps(r));assert r['ok'],r
 data=base64.b64decode(r['result']['body']);(out/(name+'.bin')).write_bytes(data);return data
try:
 data=call('overview','navigate','https://codelibrary.amlegal.com/codes/cleveland/latest/overview');state=json.loads(json.loads(re.search(r'window\._redux_state = JSON\.parse\(("(?:[^"\\]|\\.)*")',data.decode()).group(1)));v=state['codes']['selectedVersion'];code=v['toc'][0];root=next(n for n in code['sections'] if n['has_children']);call('section-toc','fetch','https://codelibrary.amlegal.com/api/section-toc/'+str(root['id'])+'/');call('render-section','fetch',f"https://codelibrary.amlegal.com/api/render-section/cleveland/{v['uuid']}/{code['slug']}/{code['sections'][0]['doc_id']}/0/");pdf=next(c for c in v['toc'] if c['is_pdf']);call('pdf-root','navigate',f"https://codelibrary.amlegal.com/codes/cleveland/{v['uuid']}/{pdf['slug']}/{pdf['sections'][0]['doc_id']}")
finally:
 p.stdin.write('{"op":"close"}\n');p.stdin.flush();print(p.stdout.readline());p.wait()
