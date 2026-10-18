"""Explicit source-bound HTML readers; incomplete scopes stay incomplete.

Each reader preserves its verified source inventory, ownership, order and limits.
Native/page/unknown modes fail closed; no hierarchy or sections are invented.
"""
from flagstaff import read_projection
from municode_html import read_projection as municode
from encodeplus_html import read_projection as encodeplus
from ecode_html import read_projection as ecode
from american_legal_html import read_projection as american_legal
READERS={'originals-flagstaff-html-v1':read_projection,'municode-html-publication-v1':municode,'encodeplus-html-publication-v1':encodeplus,'ecode-html-retained-incomplete-v1':ecode,'american-legal-native-html-publication-v1':american_legal}
def reader(name):
    if name not in READERS:raise ValueError('Unsupported reader; no speculative family mapping: '+name)
    return READERS[name]
