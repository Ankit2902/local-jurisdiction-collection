#!/usr/bin/env python3
"""Standalone entry point for setup, planning, acquisition and verification."""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from collectors.winboot import boot, ensure_fcntl
if __name__ == '__main__':
    boot()
else:
    ensure_fcntl()
sys.dont_write_bytecode = True
sys.path.insert(0, str(_root / "collectors" / "ops"))
from launcher import main

if __name__ == "__main__":
    raise SystemExit(main())
