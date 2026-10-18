"""Exact-source full six-page logical native workflow; external closure remains false."""
import copy,csv,hashlib,importlib.metadata,io,json,pathlib,tempfile
from . import solid_waste_profile as profile
SOURCE_ID='82-4b983dc51ab6'
TITLE='Administrative Regulations - Collection & Storage of Solid Waste & Recyclables'
RUNTIME_PINS={'pypdf':'6.21.1','pdfminer.six':'20251107','PyMuPDF':'1.26.5'}

def matches(data,cfg):
    actual=hashlib.sha256(data).hexdigest()
    if actual!=profile.SOURCE_SHA256 and cfg.get('expected_sha256')!=profile.SOURCE_SHA256:return False
    assert actual==cfg.get('expected_sha256')==profile.SOURCE_SHA256,'SolidWaste configured/source SHA mismatch'
    assert cfg.get('id')==SOURCE_ID and cfg.get('title')==TITLE,'SolidWaste selected publication identity mismatch'
    assert cfg.get('url')==profile.SOURCE_URL,'SolidWaste source URL is not the observed selected route'
    assert cfg.get('state')=='KS' and cfg.get('jurisdiction')=='Overland Park, Kansas','SolidWaste jurisdiction/state mismatch'
    assert cfg.get('expected_pages')==6,'SolidWaste source physical-page pin mismatch'
    return True

def project(result,evidence,pages,cfg,raw_ref):
    """Pure canonical projection, independently testable with captured native evidence."""
    assert len(pages)==6 and [p['physical_page'] for p in pages]==list(range(1,7))
    assert all(p['document_id']==cfg['id'] and p['raw_sha256']==profile.SOURCE_SHA256 and p['raw_ref']==raw_ref for p in pages),'Original page diagnostic identity mismatch'
    assert len(result['units'])==88 and len(result['controls'])==26
    records=[]
    for u in result['units']:
        r=copy.deepcopy(u);r['logical_source_document_id']=r['document_id'];r['document_id']=cfg['id'];r['unit']='pdf_logical_unit';r['heading']=u['text'].splitlines()[0] if u['unit_type'] in ['document-title','section','subheading'] else (u['source_label'] or '')
        r['source_document_url']=cfg['url'];r['source_url']=cfg['url']+'#page='+str(min(u['source_pages']));r['physical_page_start']=min(u['source_pages']);r['physical_page_end']=max(u['source_pages']);r['page_count']=6;r['raw_ref']=raw_ref;r['raw_sha256']=profile.SOURCE_SHA256
        r['canonical_structure_selection']={'profile':'solid_waste_full6_logical','source_sha256':profile.SOURCE_SHA256,'source_url':cfg['url'],'physical_pages':u['source_pages'],'source_evidence_id':u['source_tag_id'],'canonical_record_id':u['id'],'authoritative_fields':['text','parent_id','unit_type','source_pages','source_glyph_ids','source_word_ids'],'scope':'Exact retained whole six-page native document logical text/order; incorporated dependencies and current adoption remain unresolved.'}
        records.append(r)
    records[0]['source_document_evidence']=copy.deepcopy(evidence)
    records[0]['superseded_detector_diagnostics']={'schema_version':1,'unit':'whole_native_document','reason':'Complete source-native logical units supersede page-oriented canonical text. All original six page records/fields retained exactly for diagnostic lineage.','raw_ref':raw_ref,'raw_sha256':profile.SOURCE_SHA256,'original_page_records':copy.deepcopy(pages)}
    validate_records(records,cfg)
    return records

def validate_records(records,cfg):
    assert len(records)==88 and len({r['id'] for r in records})==88,'SolidWaste logical record count/identity mismatch'
    assert all(r['unit']=='pdf_logical_unit' and r['document_id']==cfg['id'] and r['page_count']==6 and r['raw_sha256']==profile.SOURCE_SHA256 and r['source_document_url']==cfg['url'] and r['source_url']==cfg['url']+'#page='+str(min(r['source_pages'])) for r in records)
    assert [r['logical_key'] for r in records if r['unit_type']=='section']==['7.36-'+str(n) for n in range(1,6)]
    assert all(r['parent_id'] is None or r['parent_id'] in {u['id'] for u in records} for r in records)
    assert all(sorted(set(r['source_pages']))==r['source_pages'] and all(1<=p<=6 for p in r['source_pages']) for r in records)
    assert all('physical_page' not in r for r in records),'Logical unit must not be mislabeled as one physical page'
    evidence=records[0]['source_document_evidence'];assert all('source_document_evidence' not in r for r in records[1:])
    assert evidence['qualification']['source_glyph_ownership_complete'] and evidence['qualification']['source_logical_structure_qualified']
    assert evidence['qualification']['required_external_legal_dependencies_complete'] is False and evidence['qualification']['edition_currentness_qualified'] is False
    assert evidence['audit']['passed'] and evidence['audit']['canonical_csv_agrees']
    controls=evidence['source_controls'];glyphs=evidence['source_glyphs'];words=evidence['source_words'];original=evidence['original_logical_units']
    assert len(controls)==26 and len(glyphs)==15574 and len(words)==2425 and len(original)==88
    glyph_ids=[g for r in records for g in r['source_glyph_ids']]+[g for c in controls for g in c['source_glyph_ids']]
    assert len(glyph_ids)==len(set(glyph_ids))==15574 and set(glyph_ids)=={g['glyph_id'] for g in glyphs}
    for r,u in zip(records,original):
        for k in ['id','text','parent_id','unit_type','logical_key','source_glyph_ids','source_word_ids','source_pages','source_refs','source_tag_id','raw_glyph_text']:assert r[k]==u[k],'SolidWaste canonical source field changed: '+k
    old=records[0]['superseded_detector_diagnostics']['original_page_records'];assert len(old)==6 and [r['physical_page'] for r in old]==list(range(1,7))
    assert all(r['raw_sha256']==profile.SOURCE_SHA256 for r in old)

def build_records(data,cfg,raw_ref,page_parser):
    assert matches(data,cfg)
    runtime={k:importlib.metadata.version(k) for k in RUNTIME_PINS};assert runtime==RUNTIME_PINS,'SolidWaste native runtime differs from tested exact pins'
    from . import solid_waste_extract as extract,solid_waste_audit as audit
    # One fresh integration execution recomputes source logical extraction and
    # independent native audit; no retained normalized fixture is injected.
    with tempfile.TemporaryDirectory(prefix='solid-waste-native-') as td:
        out=pathlib.Path(td)/'source';result=extract.write(data,out);witness=audit.audit(data,out)
        evidence={'qualification':result['qualification'],'audit':witness,'original_logical_units':result['units'],'source_controls':result['controls'],'source_glyphs':[g for p in result['glyph_pages'] for g in p['glyphs']],'source_words':result['words'],'source_tags':result['tagged']['source_inventory'],'source_dependency_inventory':result['dependency_inventory'],'source_profile_bindings':result['profile_bindings']}
    # Preserve the original page-oriented collector's exact six diagnostics.
    pages,_=page_parser(data,{'id':cfg['id'],'heading':cfg['title'],'url':cfg['url'],'raw_ref':raw_ref},{'publication':cfg['title'],'jurisdiction':cfg['jurisdiction'],'state':cfg['state']})
    records=project(result,evidence,pages,cfg,raw_ref)
    details={'pages':6,'physical_page_count':6,'normalized_record_count':88,'canonical_record_unit':'pdf_logical_unit','parser_profile':'solid_waste_full6_logical','source_logical_structure_qualified':True,'source_native_text_coverage_complete':True,'source_native_reading_order_complete':True,'source_control_count':26,'source_tag_count':191,'source_MCID_reference_count':109,'source_glyph_count':15574,'source_word_count':2425,'source_section_count':5,'runtime_pins':runtime,'source_sha256':profile.SOURCE_SHA256,'pdf_extractable_text_reconciled':True,'detected_table_cells_qualified':True,'detected_table_count':0,'detected_table_cells':0,'source_table_applicability':'not-applicable-source-proven','pdf_table_semantics_complete':False,'reading_order_manual_review_required':True,'required_external_legal_dependencies_complete':False,'edition_currentness_qualified':False,'source_dependency_inventory':result['dependency_inventory'],'review_conditions':{'external_dependencies':'O.P.M.C. Chapter7.36 incorporated; CountySolidWasteRegulations referenced; both unresolved','currentness':'Printed2011, blankdeadline retained; currentadoption/edition equivalence unqualified','scope':'Own native text/logical source structure qualified; no fullpublication/dependency/edition/jurisdiction promotion'}}
    return records,details

def outputs(records):
    logical=[r for r in records if r.get('unit')=='pdf_logical_unit']
    assert logical
    cfg={'id':logical[0]['document_id'],'url':logical[0]['source_document_url']};validate_records(logical,cfg)
    columns=['id','document_id','unit','unit_type','heading','parent_id','source_label','source_pages','physical_page','physical_page_start','physical_page_end','page_count','text','source_url','raw_sha256'];stream=io.StringIO(newline='');writer=csv.DictWriter(stream,columns);writer.writeheader();writer.writerows({k:(json.dumps(r.get(k,[])) if k=='source_pages' else r.get(k)) for k in columns} for r in records)
    jsonl=lambda rs:''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rs).encode();result={'records.jsonl':jsonl(records),'records.csv':stream.getvalue().encode()};e=logical[0]['source_document_evidence']
    for name,key in [('source-logical-units.jsonl','original_logical_units'),('source-controls.jsonl','source_controls'),('source-glyphs.jsonl','source_glyphs'),('source-words.jsonl','source_words')]:result[name]=jsonl(e[key])
    result['source-page-diagnostics.jsonl']=jsonl(logical[0]['superseded_detector_diagnostics']['original_page_records'])
    if 'mixed_source_diagnostic_lineage' in logical[0]:result['source-asset-page-diagnostics.jsonl']=jsonl(logical[0]['mixed_source_diagnostic_lineage']['original_asset_page_records'])
    for name,key in [('source-tags.json','source_tags'),('source-dependency-inventory.json','source_dependency_inventory'),('source-logical-qualification.json','qualification'),('source-independent-audit.json','audit')]:result[name]=(json.dumps(e[key],ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    return result
