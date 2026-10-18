#!/usr/bin/env python3
"""One strict standard offline verifier with no-network/image tripwires and byte-stability audit."""
import sys,pathlib,json,os,time,datetime,hashlib,traceback,socket
from unittest.mock import patch
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(P/'runtime'))
import verify,collect
from no_image import guard
from source_inventory import validate

def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(root.rglob('*'))if p.is_file()}

def main():
 run=P/'run';before=hashes(run);calls=[];net=[];started=time.monotonic()
 s={'pid':os.getpid(),'stage':'strict-readonly-active','started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 collect.save(P/'verify-status.json',s)
 def denied(*a,**kw):net.append('network_forbidden');raise AssertionError('Read-only verification never requests network')
 try:
  with guard(calls),patch.object(socket,'socket',denied),patch.object(socket,'create_connection',denied):
   r=verify.verify(run)
   cp=collect.load(run/'checkpoint.json');expected=collect.load(P/'clark-uncodified-inventory.json')
   validate((run/cp['identity']['source_ref']).read_bytes(),collect.load(run/'config.json')['source_url'],expected)
  after=hashes(run);assert before==after,'Read-only verifier changed producer evidence'
  code=0 if r['requested_coverage_complete'] else 3
  s.update(coverage=collect.brief(r),pdf_text_table_qa=r.get('pdf_text_table_qa'),read_only=True,source_files_unchanged=True,source_file_count=len(before),source_hashes=before)
 except BaseException as e:
  code=3;s['exception']=str(e);traceback.print_exc()
 s.update(stage='strict-readonly-terminal',exit_code=code,elapsed_seconds=time.monotonic()-started,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),image_api_calls=calls,network_calls=net)
 collect.save(P/'verify-status.json',s)
 print(json.dumps({k:v for k,v in s.items()if k not in ['source_hashes','pdf_text_table_qa']},indent=2));return code
if __name__=='__main__':sys.exit(main())
