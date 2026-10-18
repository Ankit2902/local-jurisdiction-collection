"""Explicit readers for qualified Flagstaff, Municode and enCodePlus HTML IR.

Each reader preserves its verified source inventory, ownership, order and limits.
Native/page/unknown modes fail closed; no hierarchy or sections are invented.
"""
from flagstaff import read_projection
from municode_html import read_projection as municode
from encodeplus_html import read_projection as encodeplus
READERS={'originals-flagstaff-html-v1':read_projection,'municode-html-publication-v1':municode,'encodeplus-html-publication-v1':encodeplus}
def reader(name):
    if name not in READERS:raise ValueError('Unsupported reader; no speculative family mapping: '+name)
    return READERS[name]

from ecode_html import read_projection as ecode
READERS['ecode-html-retained-incomplete-v1']=ecode
