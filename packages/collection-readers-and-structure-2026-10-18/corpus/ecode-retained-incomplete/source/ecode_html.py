"""Exact retained eCode360 HTML IR only. No acquisition or completeness promotion."""
import re
from html.parser import HTMLParser
from reader_utils import *

class _TOCPositions(HTMLParser):
    """Only literal attributes in #toc, without DOM repair or legal-text parsing."""
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self):super().__init__(convert_charrefs=True);self.stack=[];self.entries=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);inside=bool(self.stack and self.stack[-1][1]) or a.get('id')=='toc'
        if inside and 'contentTitle' in (a.get('class') or '').split() and a.get('data-guid') is not None and a.get('data-position') is not None:self.entries.append((a['data-guid'],a['data-position']))
        if tag not in self.VOID:self.stack.append((tag,inside))
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:del self.stack[i:];break
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
def toc_positions(raw):
    parser=_TOCPositions();parser.feed(raw.decode('utf-8',errors='strict'));parser.close();return parser.entries

def read_projection(root,proof,family):
    root=envelope(root,proof,family,'ecode');cp=load(root/'checkpoint.json');cfg=cp['config'];cov=load(root/'coverage.json');pubid=proof['publication_id']
    require(cp.get('schema_version')=='icc-full-1.0' and cfg==proof['selected_config'] and cfg.get('family')=='ecode360' and not cfg.get('subtree') and not cfg.get('max_items'),'Only explicitly verified whole-publication eCode HTML acquisition scope supported')
    require(family.get('verified') is True,'Standard retained-source reconstruction did not verify')
    require({k:v for k,v in family.items() if k!='verified'}==cov,'Family report differs from inherited source coverage')
    require(cp.get('network_prohibited') is True and cov.get('complete') is False,'This reader deliberately supports retained incomplete source only; other modes require qualification')
    identity=cp['identity'];require(identity['family']=='ecode360' and cp['publication_url']=='https://ecode360.com/'+identity['customer_id'] and cfg['url']==cp['publication_url'],'Wrong customer/publication root')
    require(cov['identity']==identity and not cov['missing_ids'] and not cov['extra_ids'] and not cov['unresolved_ids'] and not cov['conflicting_duplicate_bodies'],'Acquired HTML node ownership unresolved')
    require(not cov['limits_applied'] and cov['scope']=='whole_publication','Bounded source is not this reader profile')
    for n,h in cp['code_fingerprint'].items():
        require(proof['collector_sources_before'].get(n)==h,'Wrong explicitly selected standard verifier revision')
        raw(root,'executed-source/'+n,h)
    inv=load(root/'inventory.json');ds=load(root/'dispositions.json');records=lines(root/'records.jsonl');by={n['id']:n for n in inv};disps={d['id']:d for d in ds};rmap={r['id']:r for r in records}
    require(len(by)==len(inv)==len(disps)==len(ds)==cov['inventory_nodes'] and set(by)==set(disps),'Missing/duplicate source descriptor/disposition')
    require(len(rmap)==len(records)==cov['normalized_records']==cov['owned_content_nodes'],'Missing/duplicate acquired body')
    require(set(rmap)=={n for n,d in disps.items() if d['classification']=='owned_content'},'Omitted/foreign owned-body projection')
    require(all(d['classification'] in ['owned_content','structural_empty','reserved_or_repealed_empty'] for d in ds),'Unsupported source disposition')
    arts={a['path']:a for a in cp['artifacts']};require(len(arts)==len(cp['artifacts']),'Duplicate raw artifact')
    for a in arts.values():
        raw(root,a['path'],a['sha256']);require(safe(root,a['path']).stat().st_size==a['bytes'],'Raw byte count differs')
        require(not a.get('headers',{}).get('content-type','').strip().lower().startswith('image/'),'Separate image artifact forbidden')
    valid=[a for a in arts.values() if a['role'] in ['root-start','content'] and a['status']==200]
    positions={};position_witness={};ordered_tocs=0
    for a in valid:
        local=[]
        for ident,value in toc_positions(safe(root,a['path']).read_bytes()):
            require(value.isdigit(),'Noninteger publisher position')
            require(ident in by,'Unknown positioned source node');position=int(value);local.append(position)
            require(ident not in positions or positions[ident]==position,'Conflicting source positions')
            positions[ident]=position;position_witness.setdefault(ident,{'raw_artifact_path':'evidence/input/'+a['path'],'raw_sha256':a['sha256'],'selector':'#toc .contentTitle[data-guid="'+ident+'"][data-position="'+value+'"]','literal_data_position':value})
        require(local==sorted(local) and len(local)==len(set(local)),'Source TOC sibling order conflicts with publisher positions');ordered_tocs+=1
    rootid=identity['customer_id']
    require(set(positions)==set(by)-{rootid} and len(set(positions.values()))==len(positions),'Missing/duplicate publisher source order')
    ordered_inv=[by[rootid]]+[by[k] for k in sorted(positions,key=positions.get)]
    def witness(url):
        hits=[a for a in valid if a['url']==url];require(hits,'Source descriptor has no observed raw witness');return hits[0]
    def ancestry(ident):
        out=[];seen=set();current=ident
        while current:
            require(current in by and current not in seen,'Unknown/cyclic retained ancestry');seen.add(current);n=by[current];out.insert(0,n)
            current=rmap.get(current,{}).get('parent_id') or n.get('parent_id')
        return out
    version={'snapshot_id':'sha256:'+file_hash(root/'checkpoint.json'),'publisher_identity':identity,'publisher_currency_raw':identity['currency_raw'],'closing_currency_raw':None,'edition_complete':False,'interpretation':'Literal opening identity only; no retained closing sweep'}
    nodes=[];dispositions=[];rows=[];provenance=[];exceptions=[]
    for order,n in enumerate(ordered_inv):
        ident=n['id'];a=witness(n['observed_on']);r=rmap.get(ident);parent=(r or {}).get('parent_id') or n.get('parent_id')
        nodes.append({'node_id':'source:'+ident,'publication_id':pubid,'parent_node_id':'source:'+parent if parent else None,'source_order':order,'source_order_domain':'Publisher literal global data-position, corroborated by every acquired source TOC DOM sequence; bodyless publication root precedes descendants','source_order_witness':position_witness.get(ident,{'root_wrapper':True,'body_emitted':False}),'node_kind':n['kind'],'display_heading':n['heading'],'source_url':n['url'],'publisher_descriptor':n,'source_version':version['snapshot_id'],'raw_artifact_path':'evidence/input/'+a['path'],'raw_sha256':a['sha256'],'locator':{'kind':'eCode360-source-GUID','guid':ident,'observed_on':n['observed_on']},'parent_policy':'Exact rich own-body parent when available, otherwise retained descriptor parent; missing source parent is not guessed'})
        classification=disps[ident]['classification'];disposition={'owned_content':'included','structural_empty':'structural','reserved_or_repealed_empty':'reserved_or_repealed'}[classification]
        dispositions.append({'node_id':'source:'+ident,'disposition':disposition,'record_ids':[pubid+':'+ident] if r else [],'evidence':disps[ident]})
    original_ordinals={r['id']:i for i,r in enumerate(records)}
    require(rootid not in rmap,'Publication root unexpectedly owns a body')
    for i,r in enumerate(sorted(records,key=lambda r:positions[r['id']])):
        ident=r['id'];chain=ancestry(ident);require(r['path']==[n['heading'] for n in chain],'Retained path differs from source-owned ancestry')
        require(r['source_url']=='https://ecode360.com/'+ident and r['edition']=={k:v for k,v in identity.items() if k not in ['name','state']},'Wrong body source/edition')
        require(r['raw_witnesses'] and all(x in arts and arts[x] in valid for x in r['raw_witnesses']),'Unqualified own-body raw witness')
        a=arts[r['raw_witnesses'][0]];html=r['semantic_html'];check_html(html)
        require(r['body_sha256']==sha(canonical({'heading':r['heading'],'html':html})),'Canonical body digest mismatch')
        require(html.count('[IMAGE]')==r['image_placeholder_count'],'Image placeholder ownership differs')
        row,evidence,conflicts=corpus_row(cfg['jurisdiction'],identity['name'],chain,r['heading'],html,r['source_url'],a['retrieved_at'])
        if r['kind']=='section':
            m=re.fullmatch(r'(?:§|SECTION)\s*(\S+)\s*(.*)',r['heading'],re.S)
            require(m,'Section has no literal publisher section marker')
            row['section_number']=m[1].rstrip(':');row['section_name']=m[2]
            evidence.append({'field':'section_number','source_heading':r['heading'],'value':row['section_number'],'rule':'Exact printed § token; no GUID/numeric-depth inference'})
        rows.append(row);rid=pubid+':'+ident
        provenance.append({'record_id':rid,'node_ids':['source:'+ident],'source_version':version,'source_order':i,'source_order_domain':'Publisher data-position; original rich IR ordinal retained separately','source_order_witness':position_witness[ident],'source_kind':r['kind'],'parent_source_id':r['parent_id'],'raw_artifact_path':'evidence/input/'+a['path'],'raw_sha256':a['sha256'],'raw_witnesses':[{'path':'evidence/input/'+x,'sha256':arts[x]['sha256'],'retrieved_at':arts[x]['retrieved_at']} for x in r['raw_witnesses']],'locator':{'kind':'exclusive-owned-eCode-content-GUID','id':ident,'source_body_id':ident+'_content'},'rich_ir':{'path':'evidence/input/records.jsonl','line_ordinal':original_ordinals[ident],'record_sha256':sha(canonical(r))},'canonical_html_field':'semantic_html','canonical_html_sha256':sha(html.encode()),'canonical_body_sha256':r['body_sha256'],'notes_html':r['notes_html'],'tables_html':r['tables_html'],'note_policy':'Notes/history already inline in canonical own body; source typed note arrays retained, never appended again','image_placeholder_count':r['image_placeholder_count'],'image_references':r['image_references'],'links':r['links'],'assets':r['assets'],'hierarchy_chain':chain,'field_source_components':evidence,'hierarchy_conflicts':conflicts,'extraction_versions':cp['code_fingerprint'],'scrape_date_role':'Exact selected own-body raw retrieved_at; not replay/export time'})
        exceptions.extend({'kind':'hierarchy_scalar_conflict','record_id':rid,**x} for x in conflicts)
    exceptions.extend({'kind':'inherited_source_error','evidence':x} for x in cov['errors'])
    exceptions.extend({'kind':'unqualified_required_nonimage_document','source_url':u,'qualification':False} for u in cov['missing_assets'])
    exceptions.append({'kind':'missing_source_closing_sweep','start_end_inventory_consistent':cov['start_end_inventory_consistent'],'publication_complete':False})
    pubs=[{'publication_id':pubid,'official_title':identity['name'],'title_role':'Exact publisher root title, no inferred publication name','root':cp['publication_url'],'stable_identity':identity,'source_version':version,'scope_disposition':'All acquired own-body HTML and every retained source disposition; incomplete publication acquisition','publication_accepted':False,'complete':False,'scope_evidence':'evidence/input/coverage.json','jurisdiction_discovery_complete':False}]
    times=[a['retrieved_at'] for a in arts.values()]
    meta={'jurisdiction':cfg['jurisdiction'],'source_config':cfg,'source_version':version,'acquisition_interval':{'started_at':min(times),'finished_at':max(times),'role':'Original raw receipt interval; replay/export not fresh acquisition'},'reader_scope':'Actual whole acquired HTML scope, not a complete publication. Missing closing+required documents and access stop retained.','publication_accepted':False,'complete':False,'source_order_qualified':True,'source_order_nodes':len(positions),'source_TOC_DOM_sequences_checked':ordered_tocs,'source_coverage_path':'inherited-coverage.json','notes_policy':'Inline canonical semantic HTML once; separately typed source notes retained in provenance','source_verification_mode':'Actual standard exact explicitly selected retained engine.verify; verified reconstruction can pass while publication completeness remains false'}
    return finish(pubid,rows,pubs,nodes,dispositions,provenance,exceptions,meta,cov)
