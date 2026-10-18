"""Projection only: no source HTML parsing, collection or normalizer imports."""
import json
from urllib.parse import urlsplit,urlunsplit
from common import *
from flagstaff_hierarchy import derive

ROOT='https://www.codepublishing.com/AZ/Flagstaff/'
def document(url):
    p=urlsplit(url);return urlunsplit((p.scheme,p.netloc,p.path,p.query,''))
def read_projection(root,proof,verified):
    root=Path(root)
    cp=load(root/'checkpoint.json');cfg=cp['config'];cov=load(root/'coverage.json')
    require(cfg==proof['selected_config']==verified['publication_config'],'Wrong proof/publication config')
    require(cfg.get('profile')=='flagstaff_html' and cfg.get('source_url')==ROOT and cfg.get('target_id')=='original-flagstaff-az' and cfg.get('required_formats')==['html'],'Unsupported source profile')
    require(proof.get('publication_id')=='original-flagstaff-az-primary','Wrong publication stable identity')
    require(verified.get('full_raw_replay_equal') is True and verified.get('input_files_modified') is False and verified.get('source_route_ledger_verified') is True and verified.get('opening_body_closing_chronology_verified') is True,'No qualified retained-source replay proof')
    source=load(root/'source/checkpoint.json');summary=load(root/'normalized/summary.json');audits=load(root/'normalized/document-audits.json')
    require(source.get('schema')=='flagstaff-full-html-1' and source['source_url']==ROOT and source.get('images_downloaded') is False,'Source profile/image acquisition invalid')
    require(cov['config']==cfg and cov['formats']['html']['summary']==summary,'Coverage and normalization summary disagree')
    require(verified['formats']['html']['summary']['source_checkpoint_sha256']==file_hash(root/'source/checkpoint.json'),'Verification source checkpoint mismatch')
    for gate in ['publication_text_complete','attachments_complete','source_consistency_complete','publication_accepted','complete','whole_jurisdiction_complete']:
        require(verified.get(gate)==cov.get(gate),'Verified coverage differs: '+gate)
    code=load(root/'normalized/executed-normalization.json')
    require(code==summary['code_fingerprint'],'Normalized source revision mismatch')
    for name,h in code.items():require(file_hash(safe(root,'normalized/executed-normalization/'+name))==h,'Normalization code snapshot corrupt')
    raw={}
    for a in source['artifacts']:
        require(a['status']==200 and a['source_url']==a['final_url'],'Unqualified source transport')
        require(not a.get('headers',{}).get('content-type','').lower().startswith('image/'),'Separate image source forbidden')
        require(file_hash(safe(root,'source/'+a['path']))==a['sha256'],'Source receipt hash mismatch')
        if a['role']=='content':
            require(a['source_url'] not in raw,'Duplicate raw document');raw[a['source_url']]=a
    rows_ir=[json.loads(l) for l in (root/'normalized/records.jsonl').read_text(encoding='utf-8').split('\n') if l]
    require(len(rows_ir)==summary['records'] and len({r['record_id'] for r in rows_ir})==len(rows_ir),'Duplicate/missing rich records')
    require(load(root/'normalized/source-inventory.json')==source['inventory'],'Source inventory mismatch')
    version={'snapshot_id':'sha256:'+file_hash(root/'source/checkpoint.json'),'publisher_currency_raw':summary['opening_currency'],'normalized_currency_date':None,'date_precision':'Not interpreted by packaging','closing_currency_raw':summary['closing_currency']}
    audit_by={a['url']:a for a in audits};mapping={};edge_by={e['edge_id']:e for e in source['inventory']}
    require(len(edge_by)==len(source['inventory']),'Duplicate TOC source identities')
    for a in audits:
        require(not a['missing_toc_edges'] and not a['extra_body_headings'] and not a['heading_only_unresolved'],'Unreconciled source headings')
        for m in a['mapping']:
            require(m['edge_id'] in edge_by and m['edge_id'] not in mapping,'Duplicate/foreign TOC mapping');mapping[m['edge_id']]=m['record_id']
    require(set(mapping)==set(edge_by),'Missing source TOC dispositions')
    byid={r['record_id']:r for r in rows_ir};require(set(mapping.values())<=set(byid),'TOC maps absent body')
    hierarchy=derive(rows_ir,source['inventory'],mapping)
    # Whole-block ownership reconciles without reparsing the original HTML.
    for url,a in audit_by.items():
        owned=[i for r in rows_ir if document(r['source_url'])==url for i in r['block_indices']]
        require(len(owned)==len(set(owned)) and sorted(owned)==list(range(a['source_blocks'])),'Unowned/duplicate source blocks')
    require(set(raw)==set(audit_by)=={document(r['source_url']) for r in rows_ir},'Missing/foreign raw ownership document')
    nodes=[];dispositions=[];node_ids_by_record={rid:[] for rid in byid}
    for i,e in enumerate(source['inventory']):
        rid=mapping[e['edge_id']];r=byid[rid];a=raw[document(r['source_url'])];nid='toc:'+e['edge_id'];node_ids_by_record[rid].append(nid)
        witness=[x for x in source['artifacts'] if x['role']=='toc-start' and x['source_url']==source['observed_readers'][e['root_index']]['url']]
        require(len(witness)==1,'No unique independent TOC source witness')
        t=witness[0]
        nodes.append({'node_id':nid,'publication_id':proof['publication_id'],'source_version':version['snapshot_id'],'parent_node_id':hierarchy['parents'][nid],'parentage_evidence':hierarchy['parent_evidence'][nid],'source_order':i,'source_order_domain':'retained publisher TOC inventory sequence','node_kind':'publisher_toc_edge','display_heading':e['label'],'source_url':e['source_url'],'publisher_descriptor':e,'raw_artifact_path':'evidence/input/source/'+t['path'],'raw_sha256':t['sha256'],'locator':{'kind':'verified-toc-edge','edge_id':e['edge_id']},'owned_body_evidence':{'raw_artifact_path':'evidence/input/source/'+a['path'],'raw_sha256':a['sha256'],'block_indices':r['block_indices']}})
    for r in rows_ir:
        if not node_ids_by_record[r['record_id']]:
            a=raw[document(r['source_url'])];nid='body:'+r['record_id'];node_ids_by_record[r['record_id']]=[nid]
            nodes.append({'node_id':nid,'publication_id':proof['publication_id'],'source_version':version['snapshot_id'],'parent_node_id':hierarchy['parents'][nid],'parentage_evidence':hierarchy['parent_evidence'][nid],'source_order':rows_ir.index(r),'source_order_domain':'verified owned-body record sequence (not TOC enumeration)','node_kind':'source_body_only_unit','display_heading':r['heading'] if r['source_heading_level'] else '', 'source_url':r['source_url'],'raw_artifact_path':'evidence/input/source/'+a['path'],'raw_sha256':a['sha256'],'locator':{'kind':'verified-owned-block-indices','block_indices':r['block_indices'],'source_heading_ids':r['source_heading_ids']}})
    rows=[];provenance=[]
    for i,r in enumerate(rows_ir):
        a=raw[document(r['source_url'])];require(r['source_sha256']==a['sha256'],'IR/raw body binding mismatch')
        html=r['semantic_html'];check_html(html)
        require(html.count('[IMAGE]')==r['image_placeholder_count'],'Image placeholder ownership differs')
        heading=r['heading'] if r['source_heading_level'] else ''
        row={f:'' for f in FIELDS};row.update(jurisdiction=r['jurisdiction'],code_name=cfg['publication'],section_name=heading,citation=heading,full_text=html,source_url=r['source_url'],scrape_date=a['started_at'])
        row.update(hierarchy['records'][r['record_id']]['fields'])
        rows.append(row);qualification=r.get('body_qualification')
        disposition='structural' if qualification=='source_structural_parent_with_published_children' else 'reserved_or_repealed' if qualification=='explicit_reserved_or_repealed' else 'unresolved' if qualification=='unresolved_heading_only' else 'included'
        for nid in node_ids_by_record[r['record_id']]:dispositions.append({'node_id':nid,'disposition':disposition,'record_ids':[r['record_id']],'evidence':{'rich_ir_kind':r['kind'],'body_qualification':qualification,'ir_record_sha256':sha(canonical(r))}})
        provenance.append({'record_id':r['record_id'],'publication_id':proof['publication_id'],'row_ordinal':i,'corpus_row_sha256':sha(canonical(row)),'node_ids':node_ids_by_record[r['record_id']],'source_version':version,'raw_artifact_path':'evidence/input/source/'+a['path'],'raw_sha256':a['sha256'],'locator':{'kind':'verified-owned-block-indices','block_indices':r['block_indices'],'source_heading_ids':r['source_heading_ids'],'source_child_section_ids':r.get('source_child_section_ids',[])},'rich_ir':{'path':'evidence/input/normalized/records.jsonl','line_ordinal':i,'record_id':r['record_id'],'record_sha256':sha(canonical(r))},'extraction_versions':code,'source_semantic_html_sha256':sha(html.encode()),'hierarchy_policy':'Explicit publisher full ancestor paths plus typed canonical headings and agreeing printed anchors; unknown/conflicting fields remain blank','hierarchy_evidence':hierarchy['records'][r['record_id']],'heading_policy':'Literal citation; source-qualified displayed locator separated into section_number/section_name; local Source introduction label is not a citation','scrape_date_role':'Exact raw acquisition started_at, not replay time or legal edition','canonical_selection':'semantic_html only; superseded_detector_diagnostics not merged','rich_ir_kind':r['kind']})
    exceptions=[{'kind':'inherited_coverage_error','message':x} for x in cov.get('errors',[])];exceptions += [{'kind':'source_reference_defect','evidence':x} for x in load(root/'normalized/source-link-defects.json')]
    pubs=[{'publication_id':proof['publication_id'],'official_title':cfg['publication'],'root':cfg['source_url'],'stable_identity':cfg,'scope_disposition':'selected_primary_publication_including_published_Charter_component','scope_evidence':'evidence/input/collection-start.json','source_version':version,'observed_source_components':source['observed_readers'],'jurisdiction_discovery_complete':False,'scope_limitation':'One selected primary. No assertion all separate publications/adopted legal layers are closed. Original scope qualification retained.'}]
    meta={'jurisdiction':cfg['jurisdiction'],'source_version':version,'source_config':cfg,'acquisition_interval':{'started_at':source['started_at'],'finished_at':source['finished_at'],'role':'Original source acquisition interval; exact per-body timestamps preserved in scrape_date'},'source_coverage_path':'inherited-coverage.json','source_scope':'Same original verified source units; no new legal section grouping','source_verification_report':'evidence/proofs/read-only-proof.json','family_verification_report':'evidence/proofs/family-verification.json','hierarchy_mapping':'Unverified hierarchy/section-number fields deliberately blank; source ancestry and IDs retained in sidecars'}
    meta['hierarchy_mapping']='Root-scoped complete publisher ancestry paths, source heading classes/types, and displayed locators corroborated by own canonical name/id anchors. Unknown/conflicting mappings qualified explicitly.'
    meta['hierarchy_qualifications']=hierarchy['issues']
    return Projection(proof['publication_id'],rows,pubs,nodes,dispositions,provenance,exceptions,meta,cov)
