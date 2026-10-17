"""Read-only package hash/retained-proof verification; no acquisition or parsing."""
import sys;sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((B/'MANIFEST.json').read_text());assert m['schema_version']==1
for f in m['files']:assert sha(B/f['path'])==f['sha256'],f['path']
a=json.loads((B/'full-native-replay-summary.json').read_text());assert a['network_requests']==a['image_operations']==0
assert a['source_proven_alias_cases']==2 and a['unqualified_inferred_boundary_cases']==44
assert len(a['historical_46_case_assessment'])==46
for d,counts in zip(a['documents'],[(46,799,799),(62,616,572),(1,18,18)]):
 assert (d['pages'],d['cells'],d['current_cells_agree'])==counts
 assert d['detector_cell_text_geometry_ownership_raw_pdfium_preserved'] and d['source_files_unchanged']
 assert not d['semantic_complete']
sp=B/'spokane-native-attachments';s=json.loads((sp/'native-label-derivative-v3/summary.json').read_text());assert(s['total_pages'],s['native_label_pages'],s['source_proven_no_glyph_pages'])==(101,2,99)
for i,item in enumerate(s['attachments'],1):
 rows=[json.loads(x) for x in (sp/f'native-label-derivative-v3/attachment-{i}/records.jsonl').read_text().splitlines()]
 assert len(rows)==item['pages'] and item['original_files_unchanged']
 for r in rows:
  q=r['requested_scope_qualification'];assert q['native_label_projection_complete'] and q['pixel_operations']==0
  assert r['native_label_text']==r['pdfium_qualified_comparison_text']
  assert ''.join(x['qualified_text'] for x in r['native_label_glyph_geometry'])==''.join(c for c in r['native_label_text'] if not c.isspace())
  assert r['raw_sha256']==item['native_sha256'] and r['required_by']
  assert 'data:image/' not in json.dumps(r).lower()
  assert not r['text_serialization']['inferred_map_reading_order']
  if i==2:assert not q['attachment_text_normalization_qualified'] and q['remaining_native_text_qualification_gap']
  else:assert q['attachment_text_normalization_qualified']
  if i in (3,4):assert q['source_proven_no_glyph_text_NA'] and r['text']=='[IMAGE]'
geo=json.loads((sp/'map2-geometric-support.json').read_text());assert not geo['source_words_without_sufficient_native_glyphs'] and not geo['native_glyphs_without_independent_source_word_support']
print(json.dumps({'passed':True,'files_verified':len(m['files']),'historical_cell_cases':46,'qualified_hyphen_aliases':2,'remaining_inferred_cell_boundary_gaps':44,'spokane_pages':101,'exact_native_label_projection_pages':2,'source_proven_no_native_glyph_pages':99,'map2_independent_multiplicity_gap_preserved':True,'readonly':True}))
