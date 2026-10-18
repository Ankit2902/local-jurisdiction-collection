import ast,copy,hashlib,json,shutil
from pathlib import Path
P=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');O=P/'outputs/collection-readiness-post1997ee1-2026-10-17';base=O/'sto-parser-integration-candidate-v1';src=P/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/upoc-index-reconstruction-v1';r=O/'upoc-parser-integration-candidate-v1';r.mkdir(exist_ok=True)
assert not (r/'candidate').exists();shutil.copytree(base/'candidate',r/'candidate',ignore=shutil.ignore_patterns('__pycache__'))
ep=r/'candidate/collectors/encodeplus';f=ep/'fixtures/upoc-index';f.mkdir()
for n in ['source.json','reconstructed.json'] :shutil.copy2(src/n,f/n)
shutil.copy2(src/'source/baseline-four-regions.jsonl',f/'baseline-four-regions.jsonl')
cfg=json.loads((src/'source.json').read_text());expected=json.loads((src/'reconstructed.json').read_text())
for c in cfg['items']:
 it=c['item'];shutil.copy2(src/it['raw_ref'],f/(it['expected_sha256']+'.pdf'))
# Record exact candidate baseline and source provenance, no production writes.
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['pdf_structure.py','native_document.py']:shutil.copy2(ep/n,r/('baseline-'+n))
(r/'source-binding.json').write_text(json.dumps({'sto_candidate_manifest_sha256':sha(base/'MANIFEST.json'),'upoc_packet_manifest_sha256':sha(src/'MANIFEST.json'),'upoc_program_sha256':sha(src/'reconstruct.py'),'upoc_normalized_sha256':sha(src/'reconstructed.json'),'baseline_parser_sha256':sha(ep/'pdf_structure.py'),'baseline_native_sha256':sha(ep/'native_document.py')},indent=2)+'\n')
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def neutral(v,prefix,doc):
 if isinstance(v,str):return v.replace(prefix,'{PAGE}').replace(doc,'{DOCUMENT}')
 if isinstance(v,list):return [neutral(x,prefix,doc) for x in v]
 if isinstance(v,dict):return {k:neutral(x,prefix,doc) for k,x in v.items()}
 return v
def fingerprint(v,prefix,doc):
 v=copy.deepcopy(v);v['source_url']='{SOURCE}';return canonical(neutral(v,prefix,doc))
profiles={}
for c in cfg['items']:
 it=c['item'];pins={}
 for x in expected['regions']:
  if x['document_id']!=it['id']:continue
  b=next(json.loads(l) for l in (src/'source/baseline-four-regions.jsonl').read_text().splitlines() if json.loads(l)['id']==x['id'].split('::printed-index-reconstruction')[0]);prefix=b['id']
  pins[x['physical_page']]={'page_size':x['page_size'],'native_text_sha256':hashlib.sha256(b['pdfium_stream_text'].encode()).hexdigest(),'baseline_tables_sha256':canonical(neutral(b['tables'],prefix,it['id'])),'region_sha256':fingerprint(x,prefix,it['id']),'old_failed_cells':len(x['original_failed_cells_crosswalk']),'words':len(x['source_words']),'glyphs':len(x['source_glyphs'])}
 profiles[it['expected_sha256']]={'edition':c['edition'],'expected_group_CID_placeholders':c['expected_group_CID_placeholders'],'urls':[it['url']],'pins':pins}
text=(src/'reconstruct.py').read_text();tree=ast.parse(text);funcs=[]
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name in ['compact','bbox','intersects','center_inside','lines','joined','canonical','reconstruct_page']:
  funcs.append(ast.get_source_segment(text,n).replace('def reconstruct_page(','def _reconstruct_page('))
head='''"""Exact source-native UPOC index reconstruction; no edition/wholebook promotion.

Recomputes native words, glyphs, field ownership and queries. Source profiles are
bound by runtime module hash; no stored normalized output is injected.
"""
import copy,hashlib,json,re,unicodedata
from collections import Counter,defaultdict
import pypdfium2.raw as pdfium_raw
'''
head+='\nPROFILES='+repr(profiles)+'\n\n'
wrapper='''
def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def _neutral(value,prefix,document):
    if isinstance(value,str):return value.replace(prefix,'{PAGE}').replace(document,'{DOCUMENT}')
    if isinstance(value,list):return [_neutral(v,prefix,document) for v in value]
    if isinstance(value,dict):return {k:_neutral(v,prefix,document) for k,v in value.items()}
    return value

def _region_digest(region,prefix,document):
    region=copy.deepcopy(region);region['source_url']='{SOURCE}'
    return _digest(_neutral(region,prefix,document))

def attach_record(record,page,textpage,item,source_sha256):
    """Add finite index evidence. Unknown profile is no-op; selected drift refuses."""
    profile=PROFILES.get(source_sha256)
    physical=record.get('physical_page')
    if not profile or item.get('url') not in profile['urls'] or physical not in profile['pins']:return False
    pin=profile['pins'][physical]
    assert record['raw_sha256']==source_sha256,'UPOC source-record hash mismatch'
    assert record['document_id']==item['id'] and record['source_url']==item['url']+'#page='+str(physical),'UPOC record ownership/source URL mismatch'
    assert [float(page.width),float(page.height)]==pin['page_size'],'UPOC source page geometry changed'
    assert hashlib.sha256(textpage.get_text_range().encode()).hexdigest()==pin['native_text_sha256'],'UPOC native text fingerprint changed'
    assert _digest(_neutral(record['tables'],record['id'],item['id']))==pin['baseline_tables_sha256'],'UPOC detector diagnostics changed'
    source_item=dict(item,expected_sha256=source_sha256)
    index=_reconstruct_page(page,textpage,source_item,profile,record)
    assert _region_digest(index,record['id'],item['id'])==pin['region_sha256'],'UPOC full source word/glyph/style/field/geometry/diagnostic fingerprint changed'
    assert len(index['original_failed_cells_crosswalk'])==pin['old_failed_cells'],'UPOC old failed-cell evidence missing'
    index['source_binding']={'raw_sha256':source_sha256,'source_url':item['url'],'physical_page':physical,'native_text_sha256':pin['native_text_sha256'],'region_sha256':pin['region_sha256'],'qualification':'Exact source-native printed units, word/glyph/style geometry and independent native queries; CID and rectangle gaps retained.'}
    index['detector_evidence_disposition']='Original inferred detector cells and false flags remain unchanged diagnostics; index fields do not relabel detector results.'
    record['source_printed_indexes']=[index]
    record['pdf_qualification']['source_index_glyph_capture_complete']=True
    record['pdf_qualification']['source_index_unicode_complete']=index['all_region_unicode_qualified']
    record['pdf_qualification']['source_index_rectangle_boundaries_complete']=all(s['rectangular_field_boundary_qualified'] for s in index['native_query_segments'])
    return True

def summary(records):
    """Per-source index dimensions; never satisfy whole-PDF or edition semantics."""
    regions=[x for r in records for x in r.get('source_printed_indexes',[])]
    if not regions:return None
    groups=[]
    for digest in sorted({x['raw_sha256'] for x in regions}):
        assert digest in PROFILES,'Unknown UPOC region profile'
        xs=[x for x in regions if x['raw_sha256']==digest];pages=[x['physical_page'] for x in xs]
        assert len(pages)==len(set(pages)),'Duplicate UPOC source index page'
        assert all(x['source_binding']['raw_sha256']==digest for x in xs),'Mixed UPOC source binding'
        groups.append({'source_sha256':digest,'edition':PROFILES[digest]['edition'],'expected_physical_pages':[1,169],'observed_physical_pages':sorted(pages),'source_regions':len(xs),'source_index_glyph_capture_complete':set(pages)=={1,169} and all(x['source_word_ownership_complete'] and x['source_glyph_ownership_complete'] for x in xs),'all_region_unicode_qualified':all(x['all_region_unicode_qualified'] for x in xs),'known_unicode_field_content_reconciled':all(x['all_known_unicode_fields_independently_reconciled'] for x in xs),'rectangle_boundaries_complete':all(s['rectangular_field_boundary_qualified'] for x in xs for s in x['native_query_segments']),'index_entries':sum(u['kind']=='index_entry' for x in xs for u in x['units']),'printed_units':sum(len(x['units']) for x in xs),'source_words':sum(len(x['source_words']) for x in xs),'source_glyphs':sum(len(x['source_glyphs']) for x in xs),'fields':sum(len(u['fields']) for x in xs for u in x['units']),'unqualified_CID_headings':sum(len(x['unresolved_encoded_glyphs']) for x in xs),'known_unicode_rectangle_overlap_diagnostics':sum(not s['rectangular_field_boundary_qualified'] and s['unicode_qualified'] for x in xs for s in x['native_query_segments']),'original_failed_detector_cells_retained':sum(len(x['original_failed_cells_crosswalk']) for x in xs),'whole_book_semantic_or_edition_complete':False})
    return {'scope':'Only source-pinned UPOC physical1+169 printed indexes; not entire books or edition/adoption qualification','sources':groups,'whole_book_semantic_or_table_completeness_qualified':False,'legacy_40th_vs_primary_42nd_adoption_conflict_resolved':False,'image_policy':'[IMAGE]; original image placeholders/ownership unchanged, no separate image fetch/decode/extract/render/OCR'}
'''
(ep/'upoc_printed_index.py').write_text(head+'\n\n'.join(funcs)+'\n'+wrapper)
p=ep/'pdf_structure.py';s=p.read_text();s=s.replace('from .sto_physical_schedule import attach_record as attach_source_physical_schedule','from .sto_physical_schedule import attach_record as attach_source_physical_schedule\nfrom .upoc_printed_index import attach_record as attach_source_printed_index');s=s.replace('attach_source_physical_schedule(output[-1], original, tp, item, digest)','attach_source_physical_schedule(output[-1], original, tp, item, digest)\n                attach_source_printed_index(output[-1], original, tp, item, digest)');p.write_text(s)
p=ep/'native_document.py';s=p.read_text();needle="if scoped is not None: details['source_physical_schedule_dimensions']=scoped";assert needle in s;s=s.replace(needle,needle+"\n    from .upoc_printed_index import summary as printed_index_summary\n    indexes=printed_index_summary(records)\n    if indexes is not None: details['source_printed_index_dimensions']=indexes");p.write_text(s)
shutil.copy2('/tmp/prepare_upoc_integration.py',r/'prepare.py')
print(r)
