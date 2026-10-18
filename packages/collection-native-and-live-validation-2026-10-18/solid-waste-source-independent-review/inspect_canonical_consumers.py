"""Separate stdlib-only canonical exports/control/ownership/source-gap inspection."""
import collections,csv,hashlib,io,json
from pathlib import Path
P=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/collection-readiness-post-1997ee1-2026-10-17/american-legal/overland-solid-waste-logical-v1');D=P/'canonical-final-v2'
read=lambda n:json.loads((D/n).read_text());rows=lambda n:[json.loads(l) for l in (D/n).read_text().splitlines()];sha=lambda b:hashlib.sha256(b).hexdigest()
u=rows('logical-units.jsonl');c=rows('source-controls.jsonl');g=rows('source-glyphs.jsonl');w=rows('source-words.jsonl');q=read('qualification.json');i=read('source-dependency-inventory.json');tags=read('source-tags.json');by={x['id']:x for x in u};gg={x['glyph_id']:x for x in g}
assert len(u)==88 and len(c)==26 and len(g)==15574 and len(w)==2425 and len(gg)==15574
owned=[v for x in u+c for v in x['source_glyph_ids']];assert len(owned)==len(set(owned))==len(g) and set(owned)==set(gg)
assert sum(not x['text'].isspace() for x in g)==13104
assert [(x['logical_key'],x['parent_id']) for x in u if x['unit_type']=='section']==[(f'7.36-{n}','native-82-4b983dc51ab6::document') for n in range(1,6)]
for x in u:
 assert x['parent_id'] is None or x['parent_id'] in by
 assert x['source_sha256']==q['source_sha256'] and x['text_sha256']==sha(x['text'].encode())
 assert x['raw_glyph_text']==''.join(gg[k]['text'] for k in x['source_glyph_ids'])
 assert x['source_pages']==list(dict.fromkeys(gg[k]['page'] for k in x['source_glyph_ids']))
 assert x['tables']==[] and x['image_placeholders']==[]
 assert [k for line in x['source_lines'] for k in line['source_glyph_ids']]==x['source_glyph_ids']
 assert x['source_word_ids']==[z['word_id'] for z in w if z['logical_owner_id']==x['id']]
 for line in x['source_lines']:assert line['raw_text']==''.join(gg[k]['text'] for k in line['source_glyph_ids'])
for x in c:
 assert x['raw_glyph_text']==''.join(gg[k]['text'] for k in x['source_glyph_ids'])
 if x['unit_type']=='native-Artifact-footer':assert all(gg[k]['source_artifact'] for k in x['source_glyph_ids'])
 else:assert x['unit_type']=='blank-source-paragraph' and x['raw_glyph_text'].strip()==''
assert sum(x['unit_type']=='native-Artifact-footer' for x in c)==6
assert sum(x['unit_type']=='blank-source-paragraph' for x in c)==20
# Every nonspace glyph belongs to exactly one whole word, including explicit controls.
nonwhite=[k for x in w for k in x['source_glyph_ids']];assert len(nonwhite)==len(set(nonwhite))==13104 and set(nonwhite)=={x['glyph_id'] for x in g if not x['text'].isspace()}
for x in w:
 assert x['text']==''.join(gg[k]['text'] for k in x['source_glyph_ids']) and x['logical_owner_id'] in {z['id'] for z in u+c}
for n,source in [('logical-units.csv',u),('source-controls.csv',c)]:
 exported=list(csv.DictReader(io.StringIO((D/n).read_text())));assert len(exported)==len(source)
 for a,b in zip(exported,source):
  for k in ['id','unit_type','text','source_tag_id','source_sha256']:assert a[k]==(b.get(k) or '')
  assert json.loads(a['source_pages'])==b['source_pages']
bykey={x['logical_key']:x for x in u};assert bykey['7.36-5.D']['source_pages']==[5,6] and len(bykey['7.36-5.D']['source_refs'])==2
assert bykey['7.36-1.B.2.a']['parent_id']==bykey['7.36-1.B.2']['id']
assert bykey['7.36-3.B.Commercial.1']['parent_id']==bykey['7.36-3.B.Commercial']['id']
assert bykey['7.36-3.B.Residential.1']['parent_id']==bykey['7.36-3.B.Residential']['id']
assert 'rights-of-\nway.' in bykey['7.36-5.G']['text']
assert all(q[k] is False for k in ['jurisdiction_complete','required_external_legal_dependencies_complete','edition_currentness_qualified'])
assert len(i['textual_dependencies'])==2 and i['required_external_legal_dependencies_complete'] is False
for dep in i['textual_dependencies']:
 assert dep['resolved_in_this_packet'] is False and dep['edition_equivalence_qualified'] is False
 for witness in dep['witnesses']:
  owner=by[witness['logical_owner_id']];assert witness['text']==owner['text'] and witness['text_sha256']==sha(owner['text'].encode())
assert len(tags['nodes'])==191 and len(tags['references'])==109 and tags['unsupported']==[] and tags['duplicate_references']==[] and tags['unbound_references']==[]
assert all(i[k]==0 for k in ['embedded_files','annotations','hyperlinks','inline_images','image_xobjects'])
print(json.dumps({'passed':True,'canonical_units':88,'source_controls':26,'glyphs':15574,'nonwhite_glyphs':13104,'whole_words':2425,'source_nodes':191,'MCIDrefs':109,'sections':5,'canonical_JSON_CSV_text_raw_lines_and_ownership_exact':True,'crosspage_D_refs':bykey['7.36-5.D']['source_refs'],'printed_hyphen_preserved':True,'source_footer_artifacts':6,'source_blank_controls':20,'no_source_images_or_tables':True,'dependencies':[{'label':x['label'],'resolved':x['resolved_in_this_packet']} for x in i['textual_dependencies']],'edition_currentness_qualified':False,'wholepublication_acceptance':False,'image_or_network_calls':0},indent=2))
