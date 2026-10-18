#!/usr/bin/env python3
"""Test the exact reviewed runtime without modifying that runtime or repo."""
import argparse,hashlib,json,pathlib,sys,unittest
base=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--runtime',type=pathlib.Path,required=True);a=p.parse_args()
family=a.runtime/'collectors/encodeplus'
expected=json.loads((base/'PROVENANCE.json').read_text())['expected_runtime_sha256']
assert all(hashlib.sha256((family/n).read_bytes()).hexdigest()==h for n,h in expected.items()),'Different runtime from qualified proof'
sys.path.insert(0,str(a.runtime));result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(base),pattern='test_infrastructure_contents.py'))
raise SystemExit(0 if result.wasSuccessful()else 1)
