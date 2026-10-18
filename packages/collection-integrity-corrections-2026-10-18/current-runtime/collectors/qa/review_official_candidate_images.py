"""Run actual candidate collection and image parser tests, isolated from other imports."""
import argparse,hashlib,importlib,json,socket,sys,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--official-only',action='store_true');a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 sys.path.insert(0,str(a.candidate));collect=importlib.import_module('collect');verify=importlib.import_module('verify');sys.path.insert(0,str(HERE))
 import test_official_image_transport as transport
 import test_image_policy as policy
 import test_all_family_image_metadata as metadata
 policy.off=collect.model
 if a.official_only:
  original_policy=policy.Tests.rows;original_metadata=metadata.AllFamilyImageMetadata.rows
  policy.Tests.rows=lambda self,body:{'official':original_policy(self,body)['official']}
  metadata.AllFamilyImageMetadata.rows=lambda self,body:{'official':original_metadata(self,body)['official']}
 before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.candidate.glob('*') if p.suffix in ('.py','.cjs')}
 suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(transport),unittest.defaultTestLoader.loadTestsFromTestCase(policy.Tests),unittest.defaultTestLoader.loadTestsFromTestCase(metadata.AllFamilyImageMetadata)])
 def deny(*args,**kwargs):raise AssertionError('CANDIDATE_NETWORK_FORBIDDEN')
 with patch.object(socket.socket,'connect',deny),patch.object(socket,'create_connection',deny):result=unittest.TextTestRunner(verbosity=2).run(suite)
 after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.candidate.glob('*') if p.suffix in ('.py','.cjs')}
 report={'passed':result.wasSuccessful() and before==after,'tests':result.testsRun,'candidate_sources_before':before,'candidate_sources_after':after,'source_unchanged':before==after,'official_model_path':str(Path(collect.model.__file__).resolve()),'official_collect_path':str(Path(collect.__file__).resolve()),'official_only':a.official_only,'network_requests_sent':0,'claims':'Candidate exact model parser and real collector no-image-fetch regression; non-official parsers run unchanged current code. Actual source/byte audits remain separate.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
