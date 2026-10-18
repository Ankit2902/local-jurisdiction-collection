import sys;sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent
m=json.loads((B/'MANIFEST.json').read_text())
for f in m['files']:assert hashlib.sha256((B/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
d=json.loads((B/'source-diff.json').read_text());assert all(d['all_other_existing_functions_AST_identical'].values());assert d['helper_exactly_identical_to_full_replay'] and not d['acquisition_changed']
s=json.loads((B/'spokane-native-label-rebase/summary.json').read_text());assert(s['total_pages'],s['total_runs'],s['total_glyphs'])==(101,724,7619);assert s['network_requests']==s['pixel_operations']==s['PDFminer_or_vector_reparses']==0;assert not s['publication_complete']
for n,a in enumerate(s['attachments'],1):
 assert a['same_native_labels_order_geometry_text_image_placeholders_as_proven_v3'] and a['sources_unchanged'];q=json.loads((B/f'spokane-native-label-rebase/attachment-{n}/qualification.json').read_text());assert q['native_label_projection_complete'] and not q['semantic_complete'];assert q['attachment_text_normalization_qualified']==(n!=2)
 rows=[json.loads(x) for x in (B/f'spokane-native-label-rebase/attachment-{n}/records.jsonl').read_text().splitlines()];assert len(rows)==a['pages']
 for r in rows:assert r['native_label_text']==r['pdfium_qualified_comparison_text'] and r['required_by'] and 'data:image/' not in json.dumps(r).lower()
print(json.dumps({'passed':True,'files':len(m['files']),'spokane_pages':101,'native_projection_glyphs':7619,'map2_engine_gap_preserved':True,'readonly':True}))
