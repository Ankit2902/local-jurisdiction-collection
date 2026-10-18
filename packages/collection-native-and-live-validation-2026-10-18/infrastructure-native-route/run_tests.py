#!/usr/bin/env python3
import pathlib,sys,unittest
base=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(base/'candidate'))
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(base),pattern='test_*.py'))
raise SystemExit(0 if result.wasSuccessful()else 1)
