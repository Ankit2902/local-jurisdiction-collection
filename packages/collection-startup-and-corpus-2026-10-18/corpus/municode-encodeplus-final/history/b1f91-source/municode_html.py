"""One exact Municode HTML publication. All native/page/unknown variants refuse."""
from reader_utils import *

def read_projection(root,proof,family):
    root=envelope(root,proof,family,'municode');cp=load(root/'checkpoint.json');cfg=cp['binding'];cov=load(root/'coverage.json');pubid=proof['publication_id']
    require(cp.get('schema_version')==1 and cp.get('phase')=='finished' and cfg==proof['selected_config'],'Unqualified Municode HTML checkpoint/config')
    require(family.get('passed') is True and family.get('network_requests')==0 and family.get('package_writes') is False,'No successful actual offline family reconstruction')
    require(len(cp['publications'])==1 and len(cov['selected_product_ids'])==1,'Reader selects one publication, never guesses multi-book scope')
    pid=next(iter(cp['publications']));publication=cp['publications'][pid];report=load(root/'publications'/pid/'coverage.json')
    require(cov['selected_product_ids']==[pid] and family['record_count']==cov['record_count'],'Publication/count proof mismatch')
    for key in ['publication_complete','publication_text_complete','publication_attachments_complete']:require(family.get(key)==cov.get(key),'Family/retained coverage mismatch '+key)
    for name,h in cfg['implementation'].items():
        if Path(name).suffix=='.py':require(proof['collector_sources_before'].get(name)==h,'Historical parser revision mismatch '+name)
        raw(root,'executed-sources/'+h+'/'+name,h)
    def unit(name):
        u=cp['units'][name];rp=safe(root,u['receipt']);r=load(rp)
        require(r['status']==200 and not r.get('access_stop') and not r.get('image_omitted'),'Failed or image source unit')
        require(r['request']==u['request'] and r['sha256']==u['sha256'],'Raw unit receipt binding differs')
        body=raw(root,r['body_file'],u['sha256']);return json.loads(body.read_text()),r,body.relative_to(root).as_posix()
    tree,toc_receipt,tocpath=unit(publication['toc_unit']);product,_,_=unit(publication['product_unit']);product=product['Model'];job,_,_=unit(publication['job_unit'])
    require(str(product['ProductID'])==pid and job['Id']==publication['job_id'] and str(job['ProductId'])==pid,'Wrong source product/job')
    require(product['Client']['ClientName'] in cp['expected_identity']['client_names'] and product['Client']['State']['StateAbbreviation']==cp['expected_identity']['state'],'Wrong jurisdiction')
    require(publication['start_signature']==publication['end_signature'] and report['start_end_consistent'] is True,'Source version changed')
    source_nodes=[];byid={}
    def walk(n,parent,ancestors):
        ident=str(n['Id']);require(ident and ident not in byid,'Duplicate source inventory ID');require(str(n.get('ParentId'))==str(parent) or n.get('ParentId') is None and parent is None,'Source parent mismatch')
        record={'id':ident,'heading':n.get('Heading') or '', 'parent':parent,'ancestors':ancestors,'source':n};byid[ident]=record;source_nodes.append(record)
        for child in n.get('Children',[]):walk(child,ident,ancestors+[ident])
    walk(tree,None,[]);require(len(source_nodes)==report['inventory_node_count'],'Source inventory count differs')
    records=lines(root/'publications'/pid/'sections.jsonl');rmap={str(r['node_id']):r for r in records};require(len(rmap)==len(records)==report['parsed_record_count'],'Duplicate/missing rich records')
    exclusions={str(x['id']):x for x in report['justified_exclusions']};require(len(exclusions)==len(report['justified_exclusions']),'Duplicate disposition')
    require(set(rmap).isdisjoint(exclusions) and set(rmap)|set(exclusions)==set(byid),'Missing/foreign source inventory disposition')
    docs={}
    for name in publication['content_units']:
        payload,receipt,path=unit(name);require(isinstance(payload,list),'Unsupported native/content format')
        for ordinal,d in enumerate(payload):
            ident=str(d['Id']);require(ident not in docs,'Duplicate source document body');docs[ident]=(d,receipt,path,ordinal,name)
    version={'snapshot_id':'sha256:'+file_hash(root/'checkpoint.json'),'publisher_job':job,'product_id':pid,'start_signature':publication['start_signature'],'end_signature':publication['end_signature'],'legal_currency_interpretation':None}
    rows=[];nodes=[];dispositions=[];provenance=[];exceptions=[];scope_observations=[]
    for order,n in enumerate(source_nodes):
        ident=n['id'];nid='toc:'+pid+':'+ident;parent='toc:'+pid+':'+n['parent'] if n['parent'] else None
        nodes.append({'node_id':nid,'publication_id':pubid,'source_order':order,'parent_node_id':parent,'node_kind':'publisher_fullTree_node','display_heading':n['heading'],'source_url':cfg['source_url'].split('?')[0]+'?nodeId='+ident,'source_version':version['snapshot_id'],'raw_artifact_path':'evidence/input/'+tocpath,'raw_sha256':toc_receipt['sha256'],'locator':{'kind':'publisher-fullTree-ID','id':ident,'child_ids':[str(x['Id']) for x in n['source'].get('Children',[])]}})
        if ident in exclusions:
            ex=exclusions[ident];d,_,expath=unit(ex['evidence_unit']);ds=d if isinstance(d,list) else d.get('Docs',[]);require(isinstance(ds,list),'Unknown landing response wrapper');matching=[x for x in ds if str(x.get('Id'))==ident]
            require(len(matching)==1 and matching[0].get('DocType')==4 and not matching[0].get('Content'),'Unproved structural exclusion')
            
            if isinstance(d,dict) and d.get('NewOrds'):
                scope_observations.append({'kind':'uncollected_landing_NewOrds','source_unit':ex['evidence_unit'],'raw_artifact_path':'evidence/input/'+expath,'raw_sha256':cp['units'][ex['evidence_unit']]['sha256'],'source_field':'NewOrds','source_count':len(d['NewOrds']),'source_field_sha256':sha(canonical(d['NewOrds'])),'disposition':'Retained original landing metadata; outside selected codified-book transcription. No uncodified-ordinance or jurisdiction closure added.'})
            dispositions.append({'node_id':nid,'disposition':'structural','record_ids':[],'evidence':ex});continue
        r=rmap[ident];require(ident in docs and r['source_unit']==docs[ident][4],'Missing/foreign own body source')
        d,receipt,path,ordinal,unitname=docs[ident]
        require(r['product_id']==int(pid) and r['job_id']==job['Id'] and r['doc_type'] in [1,2] and d.get('DocType')==r['doc_type'],'Unsupported source body type/version')
        require(r['parent_id']==n['parent'] and r['path']==[byid[x]['heading'] for x in n['ancestors']]+[n['heading']] and r['toc_heading']==n['heading'],'Rich/source hierarchy mismatch')
        require(r['body_sha256']==sha((d.get('Content') or '').encode()) and r['normalized_html_sha256']==sha(r['html'].encode()),'Body raw/canonical hash mismatch')
        require(not any(value for key,value in d.items() if key.lower() in {'notes','footnotes'}) and not r.get('notes') and not r.get('footnotes_html'),'Unsupported separate Notes/Footnotes presentation order in raw or normalized body; source schema qualification required before export')
        chain=[{'id':x,'heading':byid[x]['heading']} for x in n['ancestors']]+[{'id':ident,'heading':n['heading']}]
        row,component_proof,conflicts=corpus_row(cfg['jurisdiction'],product['ProductName'],chain,r['heading'],r['html'],r['source_url'],receipt['retrieved_at'],not r['is_container'])
        rid=pid+':'+ident;rows.append(row);kind='source_parent_with_owned_body' if r['is_container'] and r['text'].strip() else 'source_structural_parent' if r['is_container'] else 'source_leaf_body'
        disposition='structural' if r['is_container'] and not r['text'].strip() else 'included'
        dispositions.append({'node_id':nid,'disposition':disposition,'record_ids':[rid],'evidence':{'rich_ir_kind':kind,'doc_type':r['doc_type'],'record_sha256':sha(canonical(r))}})
        provenance.append({'record_id':rid,'node_ids':[nid],'source_version':version,'source_kind':kind,'parent_source_id':n['parent'],'source_order':order,'raw_artifact_path':'evidence/input/'+path,'raw_sha256':receipt['sha256'],'locator':{'kind':'publisher-JSON-doc-ID','id':ident,'array_ordinal':ordinal,'source_unit':unitname},'rich_ir':{'path':'evidence/input/publications/'+pid+'/sections.jsonl','line_ordinal':records.index(r),'record_sha256':sha(canonical(r))},'scrape_date_source_value':receipt['retrieved_at'],'scrape_date_conversion':'Source provider UTC epoch rendered ISO8601; original numeric value retained','canonical_html_field':'html','canonical_html_sha256':sha(r['html'].encode()),'hierarchy_chain':chain,'field_source_components':component_proof,'hierarchy_conflicts':conflicts,'extraction_versions':cfg['implementation']})
        exceptions.extend({'kind':'hierarchy_scalar_conflict','record_id':rid,**x} for x in conflicts)
    require(len(rows)==len(records),'Emitted row/body ownership differs')
    pubs=[{'publication_id':pubid,'official_title':product['ProductName'],'root':cfg['source_url'],'stable_identity':{'product_id':pid,'client_id':cp['client_id'],'job_id':job['Id']},'source_version':version,'scope_disposition':'selected exact HTML book including owned parent bodies; not jurisdiction closure','scope_evidence':'evidence/input/checkpoint.json','additional_source_scope_observations':scope_observations}]
    exceptions.extend(scope_observations)
    exceptions.extend({'kind':'inherited_source_error','message':x} for x in report['errors'])
    receipt_times=[load(safe(root,u['receipt']))['retrieved_at'] for u in cp['units'].values()]
    meta={'jurisdiction':cfg['jurisdiction'],'source_config':cfg,'source_version':version,'acquisition_interval':{'started_at':acquired_date(min(receipt_times)),'finished_at':acquired_date(max(receipt_times)),'source_epoch_range':[min(receipt_times),max(receipt_times)],'role':'Earliest/latest retained acquisition receipt UTC times; exact own-body retrieved_at exported per row'},'reader_scope':'One source-pinned HTML publication only; no native PDF pages. Separate Notes/Footnotes schema not supported when populated.'}
    return finish(pubid,rows,pubs,nodes,dispositions,provenance,exceptions,meta,cov)
