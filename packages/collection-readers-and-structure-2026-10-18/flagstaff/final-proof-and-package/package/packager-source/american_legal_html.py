"""Source-owned AL whole native HTML, independent TOC and forward body order.

No collector/PDF/browser imports. Native PDF/page modes are deliberately refused.
"""
import html,json,re
from html.parser import HTMLParser
from urllib.parse import urlsplit
from common import *
from reader_utils import envelope,lines,literal_components,finish

IMAGE_POLICY='literal-[IMAGE]-no-image-fetch-v1'
READER='american-legal-native-html-publication-v1'

class NativeOrder(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.blocks=[];self.heads=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);key=a.get('id','')
        if key.startswith('rid-'):
            self.blocks.append(key[4:])
            if 'toc-destination' in a.get('class','').split():self.heads.append(key[4:])
    handle_startendtag=handle_starttag

def redux(data):
    match=re.search(r'window\._redux_state\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")',data.decode('utf-8'))
    require(match is not None,'AL raw overview metadata absent')
    return json.loads(json.loads(match[1]))['codes']

def independent(root,meta,requests,phase,overview_key):
    def response(key,url=None):
        require(key in requests,'Missing full independent source branch '+key)
        entry=requests[key];require(entry['response']['status']==200,'Unqualified source receipt')
        require(url is None or entry['requested_url']==url,'Wrong source request identity')
        data=safe(root,entry['file']).read_bytes();require(sha(data)==entry['sha256'],'Raw source hash drift')
        return data,entry
    data,opening=response(overview_key,meta['overview_url']);source=redux(data);identity=meta['identity']
    client,version=source['currClient'],source['selectedVersion']
    require(client['slug']==identity['client_slug'] and client['name']==identity['jurisdiction'] and client['region']['slug'].upper()==identity['state'],'Wrong source jurisdiction')
    require(version['uuid']==identity['version_uuid'] and version['client_slug']==identity['client_slug'] and version['name']==identity['version_name'] and version.get('currency_info')==identity['currency_info'],'Wrong source edition')
    books=[c for c in version['toc'] if c['uuid']==identity['code_uuid'] and c['slug']==identity['code_slug']]
    require(len(books)==1 and books[0]['title']==identity['code_title'] and books[0]['is_pdf'] is False,'Wrong HTML publication')
    nodes=[];seen=set();witness={};branch_ids=[]
    def visit(raw,parent,path,entry):
        did=raw['doc_id'];require(did not in seen,'Duplicate independent TOC ID');seen.add(did)
        n={'document_id':did,'internal_id':raw['id'],'heading':raw['title'],'parent_id':parent,'path':path+[raw['title']],
           'has_children':bool(raw.get('has_children')),'orig_doc_id':raw.get('orig_doc_id') or did,'orig_doc_idx':raw.get('orig_doc_idx') or 0,
           'passthru_doc_id':raw.get('passthru_doc_id'),'type':raw.get('type','section')}
        nodes.append(n);witness[did]=entry
        if n['has_children']:
            url='https://codelibrary.amlegal.com/api/section-toc/'+str(n['internal_id'])+'/'
            body,e=response(phase+':toc:'+did,url);payload=json.loads(body)
            require(payload['doc_id']==did and payload['id']==n['internal_id'] and payload['code_uuid']==identity['code_uuid'] and isinstance(payload.get('children'),list),'Wrong full branch identity')
            branch_ids.append(did)
            for child in payload['children']:
                require(child.get('parent_doc_id') in [None,did],'Wrong original child parent')
                visit(child,did,n['path'],e)
    for n in books[0]['sections']:visit(n,None,[],opening)
    return nodes,witness,branch_ids

def section_component(heading,chain):
    # Explicit source section sign is independent of chapter numbering (Charter).
    m=re.match(r'^(§{1,2})\s+(\d[\w.()/-]*(?:\s*[—–]\s*\d[\w.()/-]*)?)(?=\s|$)\s*(.*)$',heading)
    if m:return m[2],m[3],{'rule':'Literal source section-sign caption','marker':m[1],'literal':m[2]}
    parts,number,name,evidence,conflicts=literal_components(chain,heading,numbered_leaf=True)
    return number,name,{'rule':'Existing explicit section caption / exact named Chapter prefix only','evidence':evidence}

def read_projection(root,proof,family):
    root=envelope(root,proof,family,'american-legal');meta=load(root/'run.json');inventory=load(root/'inventory.json');ending=load(root/'inventory-end.json');requests=load(root/'requests.json');identity=meta['identity']
    require(meta['status']=='acquired' and meta['strategy']=='native' and identity['is_pdf'] is False and meta['max_items'] is None,'Only terminal whole native HTML source is qualified; PDF/page/limited modes refuse')
    require(meta['image_policy']==IMAGE_POLICY and family['publication_identity']==identity,'Image policy/publication identity mismatch')
    require(proof['selected_config']=={'source_url':meta['source_url'],'publication_selector':meta['publication_selector']},'Verification source configuration mismatch')
    require(inventory['complete'] and not inventory['pending'] and ending==inventory and meta['end_identity']==identity,'Incomplete or changed full independent inventory')
    require(sha(canonical(inventory))==meta['inventory_sha256']==meta['inventory_end_sha256'],'Inventory fingerprint mismatch')
    coverage=load(root/'coverage.json');require(coverage==family,'Standard recomputed coverage differs from stored report')
    require(family['inventory_complete'] and family['source_consistent_at_end'] and family['native_bulk_html_file_complete'] and not any(family[k] for k in ['missing_ids','extra_ids','duplicate_ids']),'Incomplete source/edition/ownership evidence')
    start,witness,branches=independent(root,meta,requests,'start','overview-start')
    end,_,endbranches=independent(root,meta,requests,'end:'+str(meta['resume_count']),'overview-end:'+str(meta['resume_count']))
    byid={n['document_id']:n for n in inventory['nodes']}
    require(len(byid)==len(inventory['nodes'])==len(start) and {n['document_id']:n for n in start}==byid and start==end and branches==endbranches,'Independent full TOC reconciliation failed')
    require(set(branches)==set(inventory['expanded']) and len(branches)==family['independently_recomputed_branch_count'],'Missing middle source branch')
    records=lines(root/'sections.jsonl');require([r['document_id'] for r in records]==[n['document_id'] for n in inventory['nodes']],'Stored IR order/IDs differ from declared inventory sequence')
    require(len(records)==family['acquired_count']==family['inventory_count'],'Source record coverage mismatch')
    ir={r['document_id']:r for r in records};irordinal={r['document_id']:i for i,r in enumerate(records)}
    require(len(ir)==len(records),'Duplicate source output')
    export=requests['native-export'];payload,job=export['response']['payload'],export['response']['job']
    require(export['response']['status']==200 and payload['version']==job['version']==identity['version_uuid'] and payload['output_format']=='html' and payload['for_print'] is False and job['for_print'] is False and json.loads(payload['scope'])==[{'code_slug':identity['code_slug']}],'Wrong whole-code native job scope')
    require(export['response']['url']=='https://export.amlegal.com/api/export-requests/'+job['uuid']+'/download/','Wrong native job download URL')
    original=safe(root,export['file']).read_bytes();require(sha(original)==export['sha256'],'Native bytes corrupt')
    scan=NativeOrder();scan.feed(original.decode('utf-8'));scan.close()
    require(len(scan.blocks)==len(set(scan.blocks)) and len(scan.heads)==len(set(scan.heads)),'Duplicate original native source IDs')
    physical={did:i for i,did in enumerate(scan.blocks)}
    order=[n['document_id'] for n in start]
    native_order=[did for did in order if ir[did]['kind']=='publisher-native-html-owned-range']
    # toc-destination marks only some native headers. Every independently owned
    # rich-block ID, including unmarked book/container headers, is authoritative.
    source_owner_order=[block for block in scan.blocks if block in ir]
    require(source_owner_order==native_order and set(scan.heads)<=set(source_owner_order),'Native source owner order differs from independently published TOC order')
    owned=[b for did in order for b in ir[did]['body_block_ids']]
    require(owned==scan.blocks and len(owned)==family['owned_source_block_count'],'Unowned/duplicate/reordered native source blocks')
    require(sum(len(r['tables']) for r in records)==family['table_count'] and sum(len(row) for r in records for table in r['tables'] for row in table)==family['table_cell_count'],'Table metadata missing')
    checkpoint=load(root/'checkpoint.json');require(checkpoint['acquired_ids']==[r['document_id'] for r in records] and checkpoint['inventory_sha256']==meta['inventory_sha256'],'Wrong source checkpoint')
    version={'snapshot_id':'sha256:'+sha(canonical(identity)),'publisher_version_uuid':identity['version_uuid'],'publisher_version_name':identity['version_name'],'currency_raw':identity['currency_info'],'acquisition_started_at':meta['started_at'],'acquisition_finished_at':meta['finished_at']}
    prefix='american-legal:'+identity['code_uuid']+':'
    nodes=[];dispositions=[];rows=[];provenance=[];exceptions=[];raw_hashes={}
    def source_path(e):
        if e['file'] not in raw_hashes:raw_hashes[e['file']]=sha(safe(root,e['file']).read_bytes())
        require(e['response']['status']==200 and raw_hashes[e['file']]==e['sha256'],'Missing raw source binding')
        return 'evidence/input/'+e['file']
    for ordinal,did in enumerate(order):
        r=ir[did];n=byid[did];nid=prefix+did;e=witness[did]
        require(r['publication_identity']==identity and r['heading']==n['heading'] and r['path']==n['path'] and r['parent_id']==n['parent_id'],'IR/source node identity or hierarchy drift')
        passthrough=r['kind']=='publisher-toc-passthrough-container'
        if passthrough:
            require(n['passthru_doc_id']==r.get('passthru_target_id') in byid and not r['body_block_ids'] and r['html'] is None and r['text']==r['heading'] and not r['tables'] and not r['assets'],'Unqualified structural passthrough body')
            target=byid[r['passthru_target_id']];ancestor=target['parent_id'];seen=set()
            while ancestor and ancestor!=did:
                require(ancestor not in seen,'Passthrough cycle');seen.add(ancestor);ancestor=byid[ancestor]['parent_id']
            require(ancestor==did,'Passthrough target is not a source descendant')
            source=requests['start:toc:'+did];text=html.escape(r['text'],quote=False);representation='Escaped exact source structural TOC heading; no descendant body synthesized'
        else:
            require(r['kind']=='publisher-native-html-owned-range' and isinstance(r['html'],str) and r['html'],'Unsupported source body/native page mode')
            source=export;text=r['html'];representation='Exact normalized source-owned HTML'
        require(r['source_sha256']==source['sha256'] and r['source_url']==source['requested_url'],'Body/raw request mismatch')
        require(r['image_policy']==IMAGE_POLICY and text.count('[IMAGE]')==len(r['image_placeholders']),'Image marker/source ownership differs')
        chain=[];current=did;seen=set()
        while current:
            require(current not in seen,'Source hierarchy cycle');seen.add(current);chain.append({'id':current,'heading':byid[current]['heading']});current=byid[current]['parent_id']
        chain.reverse();fields,_,_,evidence,conflicts=literal_components(chain,r['heading'])
        number,name,numberproof=section_component(r['heading'],chain)
        row={f:'' for f in FIELDS};row.update(fields);row.update(jurisdiction=identity['jurisdiction']+', '+identity['state'],code_name=identity['code_title'],section_number=number,section_name=name,citation=r['heading'],full_text=text,source_url=r['source_url'],scrape_date=source['retrieved_at'])
        check_html(text);rows.append(row)
        nodes.append({'node_id':nid,'publication_id':proof['publication_id'],'source_version':version['snapshot_id'],'parent_node_id':prefix+n['parent_id'] if n['parent_id'] else None,
                      'source_order':ordinal,'source_order_domain':'Publisher TOC forward preorder; native heading/block order independently agrees','node_kind':'publisher_structural_passthrough' if passthrough else 'publisher_TOC_owned_HTML',
                      'display_heading':n['heading'],'source_url':e['requested_url'],'publisher_descriptor':n,'raw_artifact_path':source_path(e),'raw_sha256':e['sha256']})
        cls=r['content_classification'];disposition='structural' if passthrough or cls=='structural-heading-only' else 'reserved_or_repealed' if cls in ['reserved-heading-only','source-explicit-status'] else 'unresolved' if cls=='unqualified-heading-only' else 'included'
        require(cls in ['structural-heading-only','reserved-heading-only','source-explicit-status','unqualified-heading-only','operative-or-front-matter-body','intentional-image-placeholder'],'Unknown source content classification')
        dispositions.append({'node_id':nid,'disposition':disposition,'record_ids':[nid],'evidence':{'source_kind':r['kind'],'content_classification':cls,'source_status_evidence':r.get('source_status_evidence')}})
        provenance.append({'record_id':nid,'node_ids':[nid],'source_version':version,'raw_artifact_path':source_path(source),'raw_sha256':source['sha256'],'source_document_id':did,
                           'source_chain':chain,'source_hierarchy_evidence':evidence,'source_hierarchy_conflicts':conflicts,'section_number_evidence':numberproof,
                           'rich_ir':{'path':'evidence/input/sections.jsonl','line_ordinal':irordinal[did],'record_sha256':sha(canonical(r))},'source_inventory_ordinal':irordinal[did],
                           'source_native_block_ordinals':[physical[b] for b in r['body_block_ids']],'body_block_ids':r['body_block_ids'],'full_text_representation':representation,
                           'source_tables':r['tables'],'source_table_parent_indices':r.get('table_parent_indices',[]),'source_links':r['links'],'source_notes':r['notes'],'source_native_auxiliary_fragments':r.get('native_auxiliary_fragments',[]),'source_image_placeholders':r['image_placeholders'],'source_asset_references':r['assets']})
        if conflicts:exceptions.append({'kind':'scalar_hierarchy_conflict','record_id':nid,'evidence':conflicts,'disposition':'Blank scalar field; exact full source ancestry retained'})
    # Required nonimage sources remain in the publication inventory. PDF pages are
    # retained diagnostics, never invented legal provisions. Image-only no-glyph
    # documents have explicit source policy N/A, not an image-caused failure.
    pages=lines(root/'pdf-pages.jsonl');assets=load(root/'assets.json')
    for a in assets:
        aid='american-legal-asset:'+sha(a['url'].encode());owners=[prefix+r['document_id'] for r in records if any(x['url']==a['url'] for x in r['assets'])]
        image=a['status']=='image-placeholder'
        if image:
            require(a['required'] is False and 'file' not in a and a.get('placeholder')=='[IMAGE]','Invalid image disposition')
            disposition='excluded_by_scope';reason='Intentional user image policy; exact source markers and locator retained, no image file'
        else:
            require(a['required'] is True,'Unknown nonimage asset scope')
            require(owners,'Required nonimage document has no independently owned HTML source reference')
            retained=a['status']=='retained'
            if retained:require(sha(safe(root,a['file']).read_bytes())==a['sha256'],'Required document bytes missing')
            related=[p for p in pages if p.get('source_url')==a['url']]
            validation=a.get('validation',{});count=validation.get('pages');owner='attachment:'+a.get('sha256','')
            expected_ids=[owner+':page:'+str(i) for i in range(1,count+1)] if type(count) is int and count>0 else []
            full_pdf_pages=retained and validation.get('kind')=='pdf' and validation.get('qualified') is True and bool(expected_ids) and a.get('normalized_pdf_document_pages')==count and a.get('normalized_pdf_owner_id')==owner and a.get('normalized_pdf_page_ids')==expected_ids and len(related)==count and [p.get('document_id') for p in related]==expected_ids and [p.get('page') for p in related]==list(range(1,count+1)) and all(p.get('owner_id')==owner and p.get('image_policy')==IMAGE_POLICY for p in related)
            no_glyph=full_pdf_pages and all(p.get('source_qualification',{}).get('policy_not_applicable_to_text_glyph_fidelity') is True and p['source_qualification'].get('source_text_glyph_count')==0 and p.get('native_source_evidence',{}).get('glyph_count')==0 and p.get('text','').replace('[IMAGE]','').strip()=='' for p in related)
            disposition='excluded_by_scope' if no_glyph else 'unresolved'
            reason='All source pages prove zero text glyphs; image policy N/A, existing [IMAGE] diagnostics preserved' if no_glyph else 'Required nonimage source retained/reported; no qualified canonical legal-unit grouping is asserted by this HTML-only reader'
            if disposition=='unresolved':exceptions.append({'kind':'required_nonimage_source_not_canonically_projected','asset_node_id':aid,'url':a['url'],'status':a['status'],'reason':reason})
        nodes.append({'node_id':aid,'publication_id':proof['publication_id'],'source_version':version['snapshot_id'],'parent_node_id':None,'source_order':None,'source_order_domain':'Referenced asset, not a printed section','node_kind':'intentional_image_reference' if image else 'required_nonimage_document','display_heading':a['url'],'source_url':a['url'],'source_owner_node_ids':owners,'asset_evidence':a})
        dispositions.append({'node_id':aid,'disposition':disposition,'record_ids':[],'evidence':{'reason':reason,'image_policy':IMAGE_POLICY if image else None,'normalized_native_pages':'evidence/input/pdf-pages.jsonl'}})
    pubs=[{'publication_id':proof['publication_id'],'official_title':identity['code_title'],'stable_identity':identity,'source_root':meta['source_url'],'scope_disposition':'Whole selected HTML code; separate required documents have explicit dispositions; not jurisdiction closure','source_version':version,'scope_evidence':'evidence/input/run.json'}]
    metadata={'jurisdiction':identity['jurisdiction']+', '+identity['state'],'source_config':proof['selected_config'],'source_version':version,
              'acquisition_interval':{'started_at':meta['started_at'],'finished_at':meta['finished_at']},'source_scope':'Whole independently inventoried native HTML publication; no PDF page grouping',
              'source_verification_report':'evidence/proofs/family-verification.json','source_coverage_path':'inherited-coverage.json','source_order':'Native-forward HTML header/block order equals independently reconstructed TOC preorder; original IR BFS ordinal retained separately',
              'canonical_HTML_records':len(records)-sum(r['kind']=='publisher-toc-passthrough-container' for r in records),'structural_TOC_passthrough_records':sum(r['kind']=='publisher-toc-passthrough-container' for r in records),
              'PDF_diagnostics_not_canonical_units':'evidence/input/pdf-pages.jsonl','inherited_coverage_unmodified':True,'source_native_sha256':export['sha256']}
    return finish(proof['publication_id'],rows,pubs,nodes,dispositions,provenance,exceptions,metadata,coverage)
