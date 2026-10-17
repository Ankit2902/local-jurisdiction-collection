import sys;sys.dont_write_bytecode=True
import json,hashlib,collections
from pathlib import Path
import pypdfium2
from native_labels import native_label_runs
base=Path(__file__).resolve().parent;project=base.parents[3]
r=json.loads((base/'attachment-2/records.jsonl').read_text());data=(project/r['raw_ref']).read_bytes();assert hashlib.sha256(data).hexdigest()==r['raw_sha256']
doc=pypdfium2.PdfDocument(data);p=doc[0];t=p.get_textpage();runs,g=native_label_runs(t,r['pdfium_qualified_comparison_text'],r['pdfium_stream_text'],r['height'],r['id']);t.close();p.close();doc.close()
# Group exact/near-identical overprints only; retain every source index.
groups=[]
for glyph in g:
 matches=[x for x in groups if x['text']==glyph['qualified_text'] and max(abs(a-b) for a,b in zip(x['bbox'],glyph['bbox']))<=.5]
 if len(matches)==1:matches[0]['native_glyph_ids'].append(glyph['id'])
 else:groups.append({'text':glyph['qualified_text'],'bbox':glyph['bbox'],'native_glyph_ids':[glyph['id']]})
words=r['native_label_units'];wc=collections.Counter(c for w in words for c in w['text'] if not c.isspace());gc=collections.Counter(x['text'] for x in groups);nc=collections.Counter(x['qualified_text'] for x in g)
res={'native_glyphs':len(g),'geometry_unique_glyphs':len(groups),'source_word_nonspace_chars':sum(wc.values()),'dedup_counter_equal':gc==wc,'native_minus_words':dict(nc-wc),'words_minus_native':dict(wc-nc),'unique_minus_words':dict(gc-wc),'words_minus_unique':dict(wc-gc),'duplicate_groups':sum(len(x['native_glyph_ids'])>1 for x in groups),'source_sha256':r['raw_sha256'],'native_stream_sha256':hashlib.sha256(r['pdfium_stream_text'].encode()).hexdigest()}
(base/'map2-overprint-inspection.json').write_text(json.dumps(res,indent=2)+'\n');(base/'map2-native-glyph-geometry.json').write_text(json.dumps({'runs':runs,'glyphs':g,'geometry_groups':groups})+'\n');print(json.dumps(res))
