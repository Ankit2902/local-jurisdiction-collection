import subprocess,json,base64,os,sys
from pathlib import Path
b=Path(__file__).resolve().parent
p=subprocess.Popen([os.environ.get('NODE_BIN','node'),str(b/'browser.cjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
for name,op,url in [('overview','navigate','https://codelibrary.amlegal.com/codes/cleveland/latest/overview'),('main-js','fetch','https://codelibrary.amlegal.com/assets/main.f0cf9ff473f9b94fb761.js')]:
 p.stdin.write(json.dumps({'op':op,'url':url})+'\n');p.stdin.flush();r=json.loads(p.stdout.readline());print(name,r.get('ok'),flush=True);(out/(name+'.response.json')).write_text(json.dumps(r));
 if not r['ok']:break
 (out/(name+'.bin')).write_bytes(base64.b64decode(r['result']['body']))
p.stdin.write('{"op":"close"}\n');p.stdin.flush();print(p.stdout.readline());p.wait()
