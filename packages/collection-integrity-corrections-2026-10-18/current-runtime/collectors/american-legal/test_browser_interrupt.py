#!/usr/bin/env python3
"""Optional headed-browser integration: delayed localhost response, interruption, bounded owned cleanup."""
import argparse,datetime,json,os,signal,subprocess,threading,time
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from transport import Browser,save

def processes():
 rows=[]
 for line in subprocess.check_output(['ps','-axo','pid=,ppid=,stat=,command='],text=True).splitlines():
  try:pid,parent,stat,command=line.strip().split(None,3);rows.append((int(pid),int(parent),stat,command))
  except ValueError:pass
 return rows
def tree(root):
 rows=processes();owned={root}
 for _ in range(12):owned|={pid for pid,parent,stat,command in rows if parent in owned}
 return [{'pid':pid,'parent':parent,'state':stat,'command':command} for pid,parent,stat,command in rows if pid in owned]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--receipt',type=Path);a=parser.parse_args();started=threading.Event();owned=[]
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   started.set();time.sleep(5)
   try:self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<html><body>Local delayed text only</body></html>')
   except BrokenPipeError:pass
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;threading.Thread(target=server.serve_forever,daemon=True).start();browser=Browser()
 def interrupt():
  started.wait(25);owned.extend(tree(browser.p.pid));os.kill(os.getpid(),signal.SIGINT)
 worker=threading.Thread(target=interrupt,daemon=True);worker.start();interrupted=False
 try:browser.call('navigate','http://127.0.0.1:'+str(server.server_port)+'/delayed')
 except KeyboardInterrupt:interrupted=True
 finally:
  t=time.monotonic();browser.close();elapsed=time.monotonic()-t;server.shutdown()
 assert interrupted and started.is_set(),'Browser never reached controlled in-flight request';assert browser.p.poll() is not None and elapsed<25,'Interrupted close remained blocked'
 remaining=[]
 for _ in range(20):
  live={pid:{'state':stat,'command':command} for pid,parent,stat,command in processes()};remaining=[r for r in owned if r['pid'] in live and live[r['pid']]['command']==r['command'] and not live[r['pid']]['state'].startswith('Z')]
  if not remaining:break
  time.sleep(.25)
 assert not remaining,'Owned browser processes still running after interruption'
 result={'schema_version':1,'test':'real ordinary headed browser interruption during delayed localhost navigation; no publisher request','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'interrupted':interrupted,'close_seconds':round(elapsed,3),'owned_node_pid':browser.p.pid,'owned_process_count':len(owned),'owned_processes_remaining':0,'image_requests':0,'passed':True}
 if a.receipt:save(a.receipt,result)
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
