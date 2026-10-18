from pathlib import Path
import collections,hashlib,json,sys
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];sys.path.insert(0,str(OUT/'source'));import pdf_glyphs
source=ROOT/'github/local-jurisdiction-collection/collectors/encodeplus/fixtures/overland-solid-waste-native.pdf';raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='1af70bb8170cf2701cfb9e7ede2b274bf848309ca6fcaa3b7a7eeba9cd426c39';(OUT/'source.pdf').write_bytes(raw);pages=pdf_glyphs.extract(raw);(OUT/'glyph-ledger.json').write_text(json.dumps(pages,indent=2,ensure_ascii=False)+'\n');tagged=json.loads((OUT/'initial-tagged-document.json').read_text());byref={(b['page'],b['mcid']):b for p in tagged['pages'] for b in p['blocks']};rows=[]
for page in pages:
 groups=collections.defaultdict(list)
 for c in page['glyphs']:
  if not c['source_artifact']:groups[c['source_mcid']].append(c)
 for mcid,chars in groups.items():
  b=byref[(page['page'],mcid)];assert ''.join(c['text'] for c in chars)==b['glyph_text'];rows.append({'page':page['page'],'mcid':mcid,'source_tag_id':b['owner_id'],'text':b['text'],'glyph_count':len(chars),'first_x':chars[0]['bbox'][0],'first_y':chars[0]['bbox'][1],'font_sizes':sorted(set(c['font_size'] for c in chars)),'fonts':sorted(set(c['font'] for c in chars))})
(OUT/'content-ref-inventory.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n');print('pages',len(pages),'glyphs',sum(len(p['glyphs']) for p in pages),'refs',len(rows));print('fonts',collections.Counter(c['font'] for p in pages for c in p['glyphs']))
for r in rows:
 if r['text'].strip():print(r['source_tag_id'],r['page'],r['mcid'],round(r['first_x'],2),r['font_sizes'],repr(r['text'][:85]))
