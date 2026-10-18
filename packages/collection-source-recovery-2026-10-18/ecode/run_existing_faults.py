import sys
sys.dont_write_bytecode=True
import argparse,importlib.util,types,unittest,socket,base64
from pathlib import Path
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--collector-root',required=True,type=Path);p.add_argument('--test-source',required=True,type=Path);a=p.parse_args()
parent=types.ModuleType('collectors');parent.__path__=[];sys.modules['collectors']=parent
family=types.ModuleType('collectors.ecode');family.__path__=[str(a.collector_root.resolve())];sys.modules['collectors.ecode']=family
spec=importlib.util.spec_from_file_location('_existing_faults',a.test_source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def no(*args,**kwargs):raise AssertionError('Publisher network/image decode forbidden')
with patch.object(socket.socket,'connect',no),patch.object(socket,'create_connection',no),patch.object(base64,'b64decode',no):
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(m))
sys.exit(0 if result.wasSuccessful() else 1)
