#!/usr/bin/env python3
"""Standard unbounded producer, authentic captured-opening import, fresh closing; no images."""
import sys,pathlib,json,os,datetime,time,traceback
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(P/'runtime'))
import collect
from no_image import guard
from source_inventory import validate
calls=[];started=time.monotonic()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
s={'pid':os.getpid(),'started_at':now(),'stage':'full198-active','driver':str(pathlib.Path(__file__).resolve()),'image_api_calls':calls}
collect.save(P/'full-status.json',s)
expected=json.loads((P/'clark-uncodified-inventory.json').read_text());original=collect.discover

def checked(run,c,resume=False):
 items,identity=original(run,c,resume)
 validate((run/identity['source_ref']).read_bytes(),c['source_url'],expected)
 return items,identity
collect.discover=checked
code=3
try:
 with guard(calls):code=collect.collect(P/'ordinance-config.json',P/'run',from_cache=P/'capture')
except BaseException as e:
 s['exception']=str(e);traceback.print_exc()
finally:
 s.update(stage='full198-terminal',exit_code=code,finished_at=now(),elapsed_seconds=time.monotonic()-started,image_api_calls=calls)
 collect.save(P/'full-status.json',s)
sys.exit(code)
