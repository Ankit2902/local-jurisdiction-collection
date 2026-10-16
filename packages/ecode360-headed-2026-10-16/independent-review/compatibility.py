#!/usr/bin/env python3
"""Run existing offline test modules against a selected source copy; deny network."""
import argparse,importlib,sys,tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--package',required=True);p.add_argument('--tests',required=True);p.add_argument('--modules',nargs='+',default=['test_ecode360','test_e2e']);a=p.parse_args()
sys.path.insert(0,str(Path(a.package).resolve()))
e=importlib.import_module('ecode360');importlib.import_module('ingest_cua');importlib.import_module('ingest_standalone')
sys.path.insert(1,str(Path(a.tests).resolve()))
suite=unittest.TestSuite()
for name in a.modules:
 suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
with tempfile.TemporaryDirectory() as tmp,patch('requests.sessions.Session.request',side_effect=AssertionError('Independent offline review forbids network')),patch.object(e,'HOST_STOP_PATH',Path(tmp)/'host-stop.json'):
 result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'network_calls':0}))
sys.exit(not result.wasSuccessful())
