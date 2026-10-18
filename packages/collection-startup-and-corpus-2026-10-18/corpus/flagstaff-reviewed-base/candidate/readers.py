"""Explicit family reader registry; unsupported formats fail closed.

Only Flagstaff's verified operational HTML IR is currently implemented. A new
reader must produce Projection without inferring hierarchy or native sections.
"""
from flagstaff import read_projection
READERS={'originals-flagstaff-html-v1':read_projection}
def reader(name):
    if name not in READERS:raise ValueError('Unsupported reader; no speculative family mapping: '+name)
    return READERS[name]
