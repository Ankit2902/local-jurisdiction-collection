"""Source-owned enCodePlus HTML records; native document/page modes refuse."""
from reader_utils import *

def read_projection(root,proof,family):
    root=envelope(root,proof,family,'encodeplus');s=load(root/'checkpoint.json');cfg=s['config'];cov=load(root/'coverage.json');pubid=proof['publication_id']
    require(s.get('phase')=='finished' and cfg==proof['selected_config'] and cfg.get('base','').startswith('https://') and '/regs/' in cfg.get('base','') and 'mode' not in cfg,'Unsupported/unbound enCodePlus HTML mode')
    require(family.get('publication_identity')==cfg['identity'] and family.get('inventory_sha256')==s['inventory_sha256'],'Wrong reconstructed source identity/version')
    for k in ['publication_text_complete','attachments_complete','edition_complete','jurisdiction_complete']:require(family.get(k)==cov.get(k),'Retained/reconstructed coverage differs '+k)
    require(family.get('status')==cov.get('status') and family.get('errors')==cov.get('errors'),'Reconstructed/retained verification status or errors differ')
    require(family.get('duplicate_output_ids')==0 and not family.get('duplicate_source_dispositions'),'Source duplication unqualified')
    for n,h in s['code_hashes'].items():
        require(proof['collector_sources_before'].get('collectors/encodeplus/'+n)==h,'Historical parser revision mismatch '+n)
        raw(root,'script-versions/'+h+Path(n).suffix,h)
    inv=load(root/'inventory.json');require(inv['sha256']==s['inventory_sha256']==cov['inventory_sha256'] and inv['base']==cfg['base'] and inv['identity']==cfg['identity'],'Inventory/source binding differs')
    def checked_entry(entry):
        p=raw(root,entry['path'],entry['sha256']);receipt=load(p.with_name(p.name+'.receipt.json'))
        require(receipt['url']==entry['url'] and receipt['http_status']==200 and receipt['sha256']==entry['sha256'] and not receipt.get('challenge'),'Wrong body receipt/source status')
        require(receipt.get('final_url',entry['url']).startswith(cfg['base']) and not receipt.get('headers',{}).get('content-type','').lower().startswith('image/'),'Escaped publication/image body')
        return receipt
    inventory_receipt=checked_entry(s['inventory_raw']);rows_ir=lines(root/'records.jsonl');byid={str(r['id']):r for r in rows_ir};require(len(byid)==len(rows_ir)==family['body_nodes'],'Duplicate/missing normalized body')
    node_by={str(n['id']):n for n in inv['nodes']};require(len(node_by)==len(inv['nodes'])==family['inventory_nodes'],'Duplicate/missing native TOC node')
    missing=set(family['missing_ids']);require(set(node_by)-set(byid)==missing and not missing,'Missing source body cannot be silently dropped')
    embedded=set(family['embedded_ids']);require(set(byid)-set(node_by)==embedded,'Foreign/unaccounted embedded body')
    blocks={};owners={}
    for block in s['blocks']:
        require(block['path'] not in blocks,'Duplicate acquired source block');blocks[block['path']]=(block,checked_entry(block))
        for ident in block['record_ids']:
            ident=str(ident);require(ident not in owners,'Duplicate acquired own-body disposition');owners[ident]=block['path']
    require(set(owners)==set(byid),'Source block/body identity inventory differs')
    require(s['end_inventory_sha256']==s['inventory_sha256'] and family['start_end_consistent'] is True,'Unreconciled source closing/version')
    source_version={'snapshot_id':'sha256:'+file_hash(root/'checkpoint.json'),'inventory_sha256':s['inventory_sha256'],'source_identity':cfg['identity'],'publisher_edition_id':None,'original_runtime':s['runtime'],'legal_currency_interpretation':None}
    nodes=[];dispositions=[];rows=[];provenance=[];exceptions=[];source_order=list(owners)
    # Acquisition blocks retain observed own-body DOM order; IR export is ID-sorted.
    # TOC is an independent inventory, never numeric ordering/hierarchy authority.
    require([i for i in source_order if i in node_by]==list(node_by),'Source block order differs from observed TOC inventory; profile qualification required')
    for ordinal,ident in enumerate(source_order):
        r=byid[ident];require(r['kind'] in ['operative_or_descriptive_body','structural_container','source_empty_unresolved','confirmed_source_empty'],'Unsupported native/page/unknown body kind')
        require(r['raw_path']==owners[ident] and r['raw_path'] in blocks,'Wrong body raw owner')
        block,receipt=blocks[r['raw_path']];require(r['raw_sha256']==block['sha256'] and r['body_sha256']==sha(r['html'].encode()),'Body canonical/raw hash mismatch')
        require(r['canonical_body_key'] and r['ownership'].startswith('exclusive'),'No exclusive own-body interpretation')
        path=r['path'];require(all(isinstance(n,dict) and str(n['id']) in byid for n in path),'Unbound hierarchy ancestry')
        require(r['parent_id']==(str(path[-1]['id']) if path else None),'Parent/path disagreement')
        require(len({str(n['id']) for n in path} | {ident})==len(path)+1,'Hierarchy cycle/duplicate ancestor')
        for i,n in enumerate(path):
            ancestor=byid[str(n['id'])];require(ancestor['heading']==n['heading'] and ancestor['parent_id']==(str(path[i-1]['id']) if i else None),'Inconsistent canonical source ancestry')
        if ident in node_by:require(r['toc_heading']==node_by[ident]['heading'],'TOC/body source identity mismatch')
        nid='toc:'+ident if ident in node_by else 'body:'+ident;parent='toc:'+str(r['parent_id']) if r['parent_id'] in node_by else 'body:'+str(r['parent_id']) if r['parent_id'] else None
        descriptor=node_by.get(ident);witness=s['inventory_raw'] if descriptor else block
        nodes.append({'node_id':nid,'publication_id':pubid,'parent_node_id':parent,'source_order':ordinal,'node_kind':'publisher_toc_node' if descriptor else 'embedded_source_owned_body','display_heading':descriptor['heading'] if descriptor else r['heading'],'source_url':r['source_url'],'source_version':source_version['snapshot_id'],'raw_artifact_path':'evidence/input/'+witness['path'],'raw_sha256':witness['sha256'],'locator':{'kind':'source-secID','id':ident,'declared_depth':descriptor.get('declared_depth') if descriptor else None,'hierarchy_method':r['hierarchy_method']}})
        chain=[{'id':str(n['id']),'heading':n['heading']} for n in path]+[{'id':ident,'heading':r['heading']}]
        row,component_proof,conflicts=corpus_row(cfg['jurisdiction'],cfg['identity'],chain,r['heading'],r['body_html'],r['source_url'],receipt['started_at'])
        rid=pubid+':'+ident;rows.append(row);disposition='structural' if r['kind']=='structural_container' else 'unresolved' if r['kind']=='source_empty_unresolved' else 'included'
        dispositions.append({'node_id':nid,'disposition':disposition,'record_ids':[rid],'evidence':{'source_body_kind':r['kind'],'source_disposition':r['disposition'],'ir_record_sha256':sha(canonical(r))}})
        provenance.append({'record_id':rid,'node_ids':[nid],'source_version':source_version,'source_kind':r['kind'],'parent_source_id':r['parent_id'],'source_order':ordinal,'raw_artifact_path':'evidence/input/'+r['raw_path'],'raw_sha256':r['raw_sha256'],'locator':{'kind':'exclusive-source-section','secid':ident,'canonical_body_key':r['canonical_body_key'],'ownership':r['ownership']},'rich_ir':{'path':'evidence/input/records.jsonl','line_ordinal':rows_ir.index(r),'source_export_order':'Original IR is ID-sorted; corpus follows observed acquisition-block/TOC source order','record_sha256':sha(canonical(r))},'canonical_html_field':'body_html','canonical_html_sha256':sha(r['body_html'].encode()),'source_owned_html_field':'html','source_owned_html_sha256':r['body_sha256'],'hierarchy_chain':chain,'field_source_components':component_proof,'hierarchy_conflicts':conflicts,'extraction_versions':s['code_hashes'],'table_count':len(r['tables']),'notes':r['notes'],'list_count':r['list_count']})
        exceptions.extend({'kind':'hierarchy_scalar_conflict','record_id':rid,**x} for x in conflicts)
    exceptions.extend({'kind':'inherited_source_error','message':x} for x in cov['errors'])
    pubs=[{'publication_id':pubid,'official_title':cfg['identity'],'root':cfg['base'],'stable_identity':cfg,'source_version':source_version,'scope_disposition':cfg['scope'],'scope_evidence':'evidence/input/checkpoint.json','native_or_other_publication_not_transcribed':True}]
    receipt_ends=[load(p).get('finished_at') for p in root.rglob('*.receipt.json')];receipt_ends=[t for t in receipt_ends if t]
    meta={'jurisdiction':cfg['jurisdiction'],'source_config':cfg,'source_version':source_version,'acquisition_interval':{'started_at':s['started_at'],'finished_at':max(receipt_ends) if receipt_ends else None,'role':'Original run start through last retained source receipt; exact body receipt started_at exported per row, never replay time'},'reader_scope':'Source-owned HTML inventory plus embedded source units; native_document/pdf_page inputs refuse. Required attachment binary capture does not become a text corpus.'}
    return finish(pubid,rows,pubs,nodes,dispositions,provenance,exceptions,meta,cov)
