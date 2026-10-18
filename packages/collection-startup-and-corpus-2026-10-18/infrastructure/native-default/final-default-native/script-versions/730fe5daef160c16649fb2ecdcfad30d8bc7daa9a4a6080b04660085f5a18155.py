"""Exact native Infrastructure printed units; legal/list/dependency gates stay incomplete."""
import copy,csv,hashlib,importlib.metadata,io,json
from . import infrastructure_printed_projection as source
TITLE='Manual of Infrastructure Standards'
UNIT='pdf_source_printed_unit'
SOURCE_METADATA={'/CreationDate':"D:20240307110856-06'00'",'/ModDate':"D:20240307110856-06'00'",'/Producer':'Skia/PDF m124 Google Docs Renderer','/Title':'manual-of-infrastructure-standards-for-right-of-way draft final 11-06-2023'}
RUNTIME_PINS={'pypdf':'6.21.1','pdfplumber':'0.11.8','pdfminer.six':'20251107','pypdfium2':'5.14.0'}

def validate_selected_config(cfg):
 if cfg.get('id')!=source.ID and cfg.get('expected_sha256')!=source.SHA:return
 assert cfg.get('expected_sha256')==source.SHA,'Infrastructure configured edition SHA mismatch'
 assert cfg.get('id')==source.ID and cfg.get('title')==TITLE,'Infrastructure selected native identity mismatch'
 assert cfg.get('url')==source.URL,'Infrastructure selected source URL is not the observed registered route'
 assert cfg.get('jurisdiction')=='Overland Park, Kansas' and cfg.get('state')=='KS','Infrastructure jurisdiction/state mismatch'
 assert cfg.get('expected_pages')==62,'Infrastructure physical-page pin mismatch'

def matches(data,cfg):
 actual=hashlib.sha256(data).hexdigest()
 if actual!=source.SHA and cfg.get('expected_sha256')!=source.SHA:return False
 validate_selected_config(cfg)
 assert actual==cfg.get('expected_sha256')==source.SHA,'Infrastructure native source/edition SHA mismatch'
 return True

def project_records(pages,inventory,cfg,raw_ref,metadata=None):
 metadata=copy.deepcopy(SOURCE_METADATA if metadata is None else metadata)
 assert metadata==SOURCE_METADATA,'Infrastructure original native metadata differs from exact source'
 assert cfg['id']==source.ID and cfg['url']==source.URL and cfg['expected_sha256']==source.SHA and cfg['expected_pages']==62
 assert all(p['raw_ref']==raw_ref for p in pages),'Infrastructure original raw-reference mismatch'
 units,dimensions=source.project(pages,inventory)
 records=[]
 for u in units:
  r=copy.deepcopy(u);r['source_unit_kind']=r['unit'];r['unit']=UNIT;r['unit_type']=('frontmatter' if r['source_outline'] is None else ('table-of-contents' if r['source_outline']['ordinal']==0 else 'printed-heading-unit'));r['publication']=cfg['title'];r['jurisdiction']=cfg['jurisdiction'];r['state']=cfg['state'];r['page_count']=62;r['physical_page_start']=min(r['source_pages']);r['physical_page_end']=max(r['source_pages']);r['source_url']=cfg['url']+'#page='+str(r['physical_page_start']);r['raw_ref']=raw_ref
  r['canonical_structure_selection']={'profile':source.PROFILE,'source_sha256':source.SHA,'source_url':cfg['url'],'physical_pages':r['source_pages'],'canonical_record_id':r['id'],'source_outline_ordinal':r['source_outline']['ordinal'] if r['source_outline'] else None,'authoritative_fields':['heading','text','ordered_blocks','tables','source_fragments','source_outline','source_pages','parent_id'],'scope':'Flat source-bookmark/printed-heading and physical source-fragment ownership. No invented parent/list/paragraph or external legal/adoption qualification.'}
  records.append(r)
 records[0]['source_document_evidence']={'profile':source.PROFILE,'native_metadata':metadata,'native_inventory':copy.deepcopy(inventory),'source_control_count':142,'source_word_count':18662,'cross_page_units':40,'required_external_legal_dependencies_complete':False,'edition_complete':False,'nested_list_hierarchy_qualified':False,'paragraph_continuation_semantics_qualified':False}
 records[0]['superseded_detector_diagnostics']={'schema_version':1,'unit':'whole_native_document','reason':'Source printed units supersede generic physical-page records; every original page/TOC/cover/table diagnostic remains exact.','raw_ref':raw_ref,'raw_sha256':source.SHA,'original_page_records':copy.deepcopy(pages)}
 validate_records(records,cfg)
 return records,dimensions

def validate_records(records,cfg):
 assert cfg['id']==source.ID and cfg['url']==source.URL,'Wrong Infrastructure record configuration'
 assert len(records)==172 and len({r['id'] for r in records})==172,'Infrastructure source-unit identity/count mismatch'
 assert all(r.get('unit')==UNIT and r.get('document_id')==source.ID and r.get('raw_sha256')==source.SHA and r.get('page_count')==62 and 'physical_page' not in r for r in records),'Infrastructure logical/page/source dimensions conflated'
 evidence=records[0]['source_document_evidence'];old=records[0]['superseded_detector_diagnostics']['original_page_records']
 assert evidence['native_metadata']==SOURCE_METADATA,'Infrastructure native metadata lineage changed'
 assert evidence['profile']==source.PROFILE and all('source_document_evidence' not in r for r in records[1:])
 assert evidence['source_control_count']==142 and evidence['source_word_count']==18662 and evidence['cross_page_units']==40
 assert evidence['required_external_legal_dependencies_complete'] is False and evidence['edition_complete'] is False and evidence['nested_list_hierarchy_qualified'] is False and evidence['paragraph_continuation_semantics_qualified'] is False
 expected,_=source.project(old,evidence['native_inventory'])
 for r,u in zip(records,expected):
  for k in ['id','document_id','heading','parent_id','source_outline','source_outline_parent_ordinal','source_pages','raw_sha256','source_document_url','source_fragments','ordered_blocks','text','tables','qualification']:assert r[k]==u[k],'Infrastructure canonical source field changed: '+k
  assert r['unit_type']==('frontmatter' if u['source_outline'] is None else ('table-of-contents' if u['source_outline']['ordinal']==0 else 'printed-heading-unit'))
  assert r['source_unit_kind']==u['unit'] and r['physical_page_start']==min(u['source_pages']) and r['physical_page_end']==max(u['source_pages']) and r['source_url']==source.URL+'#page='+str(min(u['source_pages']))
  s=r['canonical_structure_selection'];assert s['profile']==source.PROFILE and s['source_sha256']==source.SHA and s['source_url']==source.URL and s['physical_pages']==r['source_pages'] and s['canonical_record_id']==r['id']
 assert all(r['raw_ref']==old[0]['raw_ref'] and r['publication']==TITLE and r['jurisdiction']=='Overland Park, Kansas' and r['state']=='KS' for r in records),'Infrastructure record raw/context ownership differs'
 assert all(r['canonical_structure_selection']['source_outline_ordinal']==(r['source_outline']['ordinal'] if r['source_outline'] else None) for r in records),'Infrastructure selection outline binding differs'

def build_records(data,cfg,raw_ref,page_parser):
 assert matches(data,cfg)
 pins={k:importlib.metadata.version(k) for k in RUNTIME_PINS};assert pins==RUNTIME_PINS,'Infrastructure source parser runtime differs from tested pins'
 pages,_=page_parser(data,{'id':cfg['id'],'heading':cfg['title'],'url':cfg['url'],'raw_ref':raw_ref},{'publication':cfg['title'],'jurisdiction':cfg['jurisdiction'],'state':cfg['state']})
 inventory=source.native_inventory(data,pages)
 from pypdf import PdfReader
 metadata={str(k):str(v) for k,v in (PdfReader(io.BytesIO(data),strict=True).metadata or {}).items()}
 records,dimensions=project_records(pages,inventory,cfg,raw_ref,metadata)
 from .infrastructure_contents import summary
 # Own extractable characters/flat printed units are measured. Full text semantics,
 # list/paragraph intent and required document closure deliberately remain false.
 details={'metadata':metadata,'pages':62,'physical_page_count':62,'normalized_record_count':172,'canonical_record_unit':UNIT,'parser_profile':source.PROFILE,'source_sha256':source.SHA,'runtime_pins':pins,'source_native_text_coverage_complete':False,'source_extractable_characters_conserved':True,'source_flat_printed_units_qualified':True,'source_cover_units':1,'source_table_of_contents_units':1,'source_other_printed_heading_units':170,'source_flat_fragment_order_qualified':True,'source_logical_structure_qualified':False,'source_native_reading_order_complete':False,'nested_list_hierarchy_qualified':False,'paragraph_continuation_semantics_qualified':False,'required_external_legal_dependencies_complete':False,'edition_currentness_qualified':False,'pdf_extractable_text_reconciled':True,'detected_table_cells_qualified':True,'detected_table_count':5,'detected_table_cells':79,'pdf_table_semantics_complete':False,'reading_order_manual_review_required':True,'source_infrastructure_dimensions':summary(pages),'source_printed_unit_dimensions':{k:v for k,v in dimensions.items() if k not in ['original_page_records','canonical_pages']},'review_conditions':{'reading_order':'Untagged flat source outline and preserved source fragments do not establish nested list/paragraph intent','spacing':'Three previously qualified TOC leader/folio full-line spacing disagreements remain explicit','table_note':'Physical53 prints height marker2, printed note begins1; no reassociation','external_dependencies':'Current Construction Specifications/StandardDetails/ApprovedMaterials/KCMMB/KDOT/TrafficControlHandbook/StreetlightDesignManual remain unresolved','edition':'CoverMarch1,2024 and metadata draft title/creation date remain distinct; no adoption/currentness qualification'}}
 return records,details

def outputs(records):
 selected=[r for r in records if r.get('unit')==UNIT];assert selected
 cfg={'id':source.ID,'url':source.URL};validate_records(selected,cfg)
 if any(r.get('unit')=='pdf_logical_unit' for r in records):
  from .solid_waste_logical import outputs as other_outputs
  result=other_outputs(records)
 else:
  fields=['id','document_id','unit','unit_type','heading','parent_id','source_pages','physical_page','physical_page_start','physical_page_end','page_count','text','source_url','raw_sha256'];buf=io.StringIO(newline='');w=csv.DictWriter(buf,fields);w.writeheader();w.writerows({k:json.dumps(r.get(k,[])) if k=='source_pages' else r.get(k) for k in fields} for r in records)
  result={'records.jsonl':''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records).encode(),'records.csv':buf.getvalue().encode()}
 first=selected[0];e=first['source_document_evidence'];old=first['superseded_detector_diagnostics']['original_page_records']
 result['infrastructure-source-page-diagnostics.jsonl']=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in old).encode()
 for name,obj in [('infrastructure-source-inventory.json',e['native_inventory']),('infrastructure-source-qualification.json',{k:v for k,v in e.items() if k!='native_inventory'})]:result[name]=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
 return result
