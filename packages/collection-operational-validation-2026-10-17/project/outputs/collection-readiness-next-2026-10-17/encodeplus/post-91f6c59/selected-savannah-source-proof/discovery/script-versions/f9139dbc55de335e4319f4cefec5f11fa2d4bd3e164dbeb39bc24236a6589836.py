from pathlib import Path
import sys,json,hashlib,subprocess,tempfile,io,re,email.parser,urllib.request,urllib.error,datetime,shutil
from unittest.mock import patch
here=Path(__file__).resolve().parent;project=here.parents[3];repo=project/'github/local-jurisdiction-collection';sys.path.insert(0,str(repo));from collectors.encodeplus.transport import fetch
out=here/'savannah-alternative-discovery';out.mkdir(exist_ok=True);scripts=out/'script-versions';scripts.mkdir(exist_ok=True)
for p in [Path(__file__),repo/'collectors/encodeplus/transport.py',repo/'collectors/encodeplus/util.py']:
 h=hashlib.sha256(p.read_bytes()).hexdigest();shutil.copy2(p,scripts/(h+'.py'))
class Response(io.BytesIO):
 def __init__(self,data,status,headers):super().__init__(data);self.status=status;self.headers=headers
class OSVerified:
 def open(self,request,timeout=120):
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);body=td/'body';headers=td/'headers';args=['/usr/bin/curl','--silent','--show-error','--proto','=https','--connect-timeout','30','--max-time',str(timeout),'--dump-header',str(headers),'--output',str(body),'--write-out','%{http_code}','--user-agent','CompliSolv public publication collection/1.0','--url',request.full_url];result=subprocess.run(args,capture_output=True)
   if result.returncode:raise urllib.error.URLError('Ordinary system curl TLS/HTTP failed: '+result.stderr.decode(errors='replace'))
   blocks=re.split(rb'\r?\n\r?\n',headers.read_bytes().strip());block=blocks[-1];lines=block.splitlines();parsed=email.parser.BytesParser().parsebytes(b'\n'.join(lines[1:]));h=dict(parsed.items());status=int(result.stdout.decode());data=b'' if parsed.get('Content-Type','').lower().startswith('image/') else body.read_bytes();return Response(data,status,h)
if __name__=='__main__':
 url=sys.argv[1];name=sys.argv[2];target=out/name;assert not target.exists();backend={'scope':'Research-only ordinary verified systemTLS acquisition, using existing sharedgate/stops/redirectloop; no insecure overrides or productiontransportchange','url':url,'output':name,'curl_path':'/usr/bin/curl','curl_binary_sha256':hashlib.sha256(Path('/usr/bin/curl').read_bytes()).hexdigest(),'curl_version':subprocess.run(['/usr/bin/curl','--version'],capture_output=True,text=True).stdout,'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()};(out/(name+'.backend.json')).write_text(json.dumps(backend,indent=2)+'\n')
 with patch('urllib.request.build_opener',return_value=OSVerified()):data,meta=fetch(url,target)
 print({'status':meta['http_status'],'bytes':len(data),'sha256':meta['sha256']})
