import json,collections
from pathlib import Path
b=Path(__file__).resolve().parent
r=json.loads((b/'attachment-2/records.jsonl').read_text());g=json.loads((b/'map2-native-glyph-geometry.json').read_text())['glyphs'];words=r['native_label_units']
missing_words=[];coverage=set()
for wi,w in enumerate(words):
 box=w['bbox'];chars=collections.Counter(c for c in w['text'] if not c.isspace());available=collections.Counter();ids=[]
 for i,x in enumerate(g):
  a=x['bbox'];cx=(a[0]+a[2])/2;cy=(a[1]+a[3])/2
  if box[0]-.5<=cx<=box[2]+.5 and box[1]-.5<=cy<=box[3]+.5 and x['qualified_text'] in chars:
   available[x['qualified_text']]+=1;ids.append(i)
 if chars-available:missing_words.append({'index':wi,'text':w['text'],'bbox':box,'missing':dict(chars-available)})
 coverage.update(ids)
res={'comparison':'Each retained independent source-word character capacity versus matching native glyphs centered inside same word bbox +/-0.5pt; support only, not bijection/reading-order proof','source_word_count':len(words),'source_words_without_sufficient_native_glyphs':missing_words,'native_glyphs':len(g),'native_glyphs_without_independent_source_word_support':[{k:x[k] for k in ('native_character_index','qualified_text','bbox')} for i,x in enumerate(g) if i not in coverage]}
(b/'map2-geometric-support.json').write_text(json.dumps(res,indent=2)+'\n');print({k:(len(v) if isinstance(v,list) else v) for k,v in res.items()})
