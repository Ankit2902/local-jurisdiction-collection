"""Independent stdlib structural/ownership review of frozen source-bound output."""
import hashlib,json,collections
from pathlib import Path
P=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/upoc-index-reconstruction-v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
M=json.loads((P/'MANIFEST.json').read_text())
assert sha(P/'MANIFEST.json')=='f8bf347a7315ad118a67c5b5823be27c1df95e85ac210bb5f2f43f9171c3ebe1'
for e in M['files']:
 assert sha(P/e['path'])==e['sha256'] and (P/e['path']).stat().st_size==e['bytes']
x=json.loads((P/'reconstructed.json').read_text());bs=[json.loads(l) for l in (P/'source/baseline-four-regions.jsonl').read_text().splitlines()];cfg=json.loads((P/'source.json').read_text());counts=collections.Counter();limitations=[]
assert not x['whole_book_semantic_or_table_completeness_qualified'] and x['forbidden_image_calls']==[] and x['network_requests']==0
for r in x['regions']:
 conf=next(v for v in cfg['items'] if v['item']['id']==r['document_id']);item=conf['item'];b=next(v for v in bs if v['document_id']==r['document_id'] and v['physical_page']==r['physical_page'])
 assert r['raw_sha256']==item['expected_sha256']==sha(P/item['raw_ref']) and r['source_url']==item['url']
 assert r['edition']==conf['edition'] and r['physical_page'] in [1,169]
 assert r['baseline_tables']==b['tables']
 old=[c for t in b['tables'] for c in t['cells'] if not c['independent_character_agreement']]
 assert old==[c['original_failed_cell'] for c in r['original_failed_cells_crosswalk']]
 assert all(c['original_failure_retained'] and not c['original_inferred_cell_semantics_qualified'] for c in r['original_failed_cells_crosswalk'])
 assert not r['whole_publication_table_semantics_complete'] and not r['legacy_40th_vs_primary_42nd_adoption_conflict_resolved'] and not r['cross_edition_substitution_performed']
 assert r['image_placeholders']==[] and not [z for z in b['ordered_blocks'] if z['kind']=='image_placeholder']
 words={w['id']:w for w in r['source_words']};glyphs={g['id']:g for g in r['source_glyphs']};segments={s['id']:s for s in r['native_query_segments']}
 ownedwords=[];ownedglyphs=[]
 for ordinal,u in enumerate(r['units'],1):
  assert u['reading_order']==ordinal and u['reading_column']==1 and not u['automatic_cross_reference_target_resolution']
  ownedwords+=u['source_word_ids']
  for f in u['fields']:
   ownedglyphs+=f['source_glyph_ids'];ss=[segments[k] for k in f['native_query_segments']]
   assert [g for s in ss for g in s['source_glyph_ids']]==f['source_glyph_ids']
   assert all(g in glyphs for g in f['source_glyph_ids'])
   assert f['text']=='\n'.join(s['text'] for s in ss)
   assert set(f['source_word_references_nonowning'])=={glyphs[g]['word_id'] for g in f['source_glyph_ids']}
   for s in ss:
    assert s['native_character_indices']==[glyphs[g]['native_char_index'] for g in s['source_glyph_ids']]
    assert s['native_index_text']==''.join(glyphs[g]['native_unicode'] for g in s['source_glyph_ids'])
    if s['unicode_qualified']: assert s['independent_native_index_characters_agree']
  if u['unicode_qualified']:assert u['independent_whole_entry_characters_agree']
  else:
   assert u['kind']=='group_heading' and u['group_unicode_not_inferred']
 assert collections.Counter(ownedwords)==collections.Counter(words.keys())
 assert collections.Counter(ownedglyphs)==collections.Counter(glyphs.keys())
 assert len({g['native_char_index'] for g in glyphs.values()})==len(glyphs)
 for s in segments.values():
  if not s['independent_ordered_characters_agree']:
   limitations.append({'document_id':r['document_id'],'page':r['physical_page'],'segment':s['id'],'text':s['text'],'native':s['independent_native_text'],'unicode_qualified':s['unicode_qualified'],'rectangle_qualified':s['rectangular_field_boundary_qualified']})
 counts.update(regions=1,words=len(words),glyphs=len(glyphs),old_failed_cells=len(old),entries=sum(u['kind']=='index_entry' for u in r['units']),units=len(r['units']),fields=sum(len(u['fields']) for u in r['units']),image_markers=len(r['image_placeholders']))
assert dict(counts)==dict(regions=4,words=859,glyphs=7112,old_failed_cells=417,entries=112,units=123,fields=444,image_markers=0)
assert sum(s['unicode_qualified'] for s in limitations)==2 and sum(not s['unicode_qualified'] for s in limitations)==2
print(json.dumps({'passed':True,'manifest_sha256':sha(P/'MANIFEST.json'),'counts':dict(counts),'preserved_unqualified_segments':limitations,'whole_book_semantics':False,'source_writes':0,'network_or_image_operations':0},indent=2))
