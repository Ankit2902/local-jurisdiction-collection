"""Read-only verifier of a compact retained live fixture; extraction is temporary, never network."""
import argparse,json,tarfile,tempfile
from pathlib import Path
from collectors.ecode.engine import verify

def main():
 p=argparse.ArgumentParser();p.add_argument('--fixture',required=True);p.add_argument('--expect-complete',action='store_true');a=p.parse_args()
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp)
  with tarfile.open(a.fixture,'r:gz') as archive:
   for member in archive.getmembers():
    target=(root/member.name).resolve()
    if not target.is_relative_to(root.resolve()) or member.issym() or member.islnk():raise ValueError('Unsafe fixture member')
    if member.isdir():target.mkdir(parents=True,exist_ok=True)
    elif member.isfile():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.extractfile(member).read())
    else:raise ValueError('Unsupported fixture member')
  r=verify(root/'proof');passed=r['verified'] and r['complete']==a.expect_complete
  print(json.dumps({'fixture_check_passed':passed,'expected_complete':a.expect_complete,'actual':r},ensure_ascii=False,indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
