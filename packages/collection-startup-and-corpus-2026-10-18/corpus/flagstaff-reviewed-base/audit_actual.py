"""Independent consumer audit of package versus hash-bound rich IR, not raw reparse."""
import collections,csv,hashlib,io,json,re,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag

FIELDS='jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()
def h(data):return hashlib.sha256(data).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').split('\n') if l]
def tree(root):return {p.relative_to(root).as_posix():h(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}
class Structure(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.tags=collections.Counter();self.cells=[];self.events=[];self.image_positions=[];self.characters=0
    def handle_starttag(self,tag,attrs):
        self.tags[tag]+=1;self.events.append(('start',tag,attrs))
        if tag in ['td','th']:self.cells.append((tag,dict(attrs).get('rowspan','1'),dict(attrs).get('colspan','1')))
        assert tag not in {'img','svg','picture','image'},'active image'
    handle_startendtag=handle_starttag
    def handle_endtag(self,tag):self.events.append(('end',tag))
    def handle_data(self,data):
        start=0
        while '[IMAGE]' in data[start:]:
            n=data.index('[IMAGE]',start);self.image_positions.append(self.characters+n);start=n+7
        self.characters+=len(data);self.events.append(('text',data))
def audit(root):
    root=Path(root).resolve();before=tree(root);manifest=load(root/'run-manifest.json');pid=manifest['publication_id'];evidence=root/'evidence/input';ir=lines(evidence/'normalized/records.jsonl');corpus=load(root/'aggregate-fulltext.json')['provisions'];toc=load(root/'aggregate-toc.json')['provisions'];nodes=lines(root/'source-nodes.jsonl');disp=lines(root/'node-dispositions.jsonl');prov=lines(root/'record-provenance.jsonl');source=load(evidence/'source/checkpoint.json');cov=load(evidence/'coverage.json')
    assert len(ir)==len(corpus)==len(toc)==len(prov)==2661
    assert load(root/'inherited-coverage.json')==cov and not manifest['complete'] and not manifest['serialization_complete'] is False
    assert not cov['source_consistency_complete'] and not cov['publication_accepted'] and not cov['whole_jurisdiction_complete']
    edges={e['edge_id'] for e in source['inventory']};assert {n['node_id'][4:] for n in nodes if n['node_kind']=='publisher_toc_edge'}==edges and len(edges)==2658
    assert {n['node_id'] for n in nodes}=={d['node_id'] for d in disp} and len(disp)==len({d['node_id'] for d in disp})==len(nodes)
    assert {rid for d in disp for rid in d['record_ids']}=={r['record_id'] for r in ir}
    art={a['source_url']:a for a in source['artifacts'] if a['role']=='content'}
    byrecord={r['record_id']:r for r in ir};by_node={n['node_id']:n for n in nodes};node_owner={nid:p['record_id'] for p in prov for nid in p['node_ids']}
    inventory={e['edge_id']:e for e in source['inventory']};path_index=collections.defaultdict(list)
    for e in inventory.values():path_index[(e['root_index'],tuple(e.get('ancestor_classes') or e['source_id'].split()))].append(e['edge_id'])
    parent_count=0
    for eid,e in inventory.items():
        path=tuple(e.get('ancestor_classes') or e['source_id'].split());own=tuple(e['source_id'].split());assert path[-len(own):]==own;parent=path[:-len(own)]
        choices=path_index[(e['root_index'],parent)] if parent else []
        expected='toc:'+choices[0] if parent else None;assert not parent or len(choices)==1
        assert by_node['toc:'+eid]['parent_node_id']==expected;parent_count+=expected is not None
    assert parent_count==2640
    def typed(r):
        c=r['source_heading_classes'];level=r['source_heading_level'];text=r['heading']
        if level=='h1' and c==['Title']:return 'title'
        if level=='p' and c==['Division']:return 'division'
        if level=='h2' and c==['CH']:
            for prefix,role in [('CHAPTER','chapter'),('ARTICLE','article')]:
                if text.upper().startswith(prefix+' '):return role
        if level=='h2' and c==['CHTitle']:return 'chapter'
        return None
    totals=collections.Counter();fieldcounts=collections.Counter();tableattrs=[]
    for ordinal,(r,row,t,p) in enumerate(zip(ir,corpus,toc,prov)):
        assert list(row)==FIELDS and all(isinstance(x,str) for x in row.values());assert dict(row,full_text='')==t
        assert row['full_text']==r['semantic_html'] and row['source_url']==r['source_url'] and row['citation']==(r['heading'] if r['source_heading_level'] else '')
        expected_fields={f:'' for f in ['division','title','subtitle','chapter','subchapter','article','part','subpart']}
        chains=[]
        for nid in p['node_ids']:
            chain=[];seen=set()
            while nid:
                assert nid not in seen;seen.add(nid);chain.append(nid);nid=by_node[nid]['parent_node_id']
            chain.reverse();chains.append(chain)
        for nid in chains[0]:
            ancestor=byrecord[node_owner[nid]];role=typed(ancestor)
            if role:
                label=ancestor['heading']
                if ancestor['source_heading_classes']==['CHTitle']:
                    j=ir.index(ancestor);prev=ir[j-1];assert prev['source_heading_classes']==['CH'] and prev['heading'].startswith('CHAPTER ') and prev['source_sha256']==ancestor['source_sha256'];assert max(prev['block_indices'])+1==min(ancestor['block_indices']);label=prev['heading']+'\n'+label
                expected_fields[role]=label
        assert {f:row[f] for f in expected_fields}==expected_fields
        assert p['hierarchy_evidence']['source_chains']==chains
        if row['section_number']:
            number=row['section_number'];assert r['heading'].startswith(number) or r['heading'].startswith('SECTION '+number)
            proof=p['hierarchy_evidence']['section_number_evidence'];assert proof['printed']==number and proof['anchor_witnesses']
            parsed=Structure();parsed.feed(r['semantic_html']);own_heading=[]
            for event in parsed.events:
                if event[0]=='end' and event[1]==r['source_heading_level']:break
                if event[0]=='start':own_heading.extend((k,v) for k,v in event[2] if k in ['id','name'])
            assert all((w['attribute'],w['value']) in own_heading and w['value'].strip().replace('-','.')==number.replace('-','.') for w in proof['anchor_witnesses'])
        section=r['heading'] if r['source_heading_level'] else ''
        if r['source_heading_classes']==['Cite'] and row['section_number']:section=section[len(row['section_number']):].lstrip()
        assert row['section_name']==section
        fieldcounts.update(k for k,v in row.items() if v)
        a=art[urldefrag(r['source_url'])[0]];assert row['scrape_date']==a['started_at'];assert p['record_id']==r['record_id'] and p['row_ordinal']==ordinal
        assert h((root/p['raw_artifact_path']).read_bytes())==p['raw_sha256']==r['source_sha256']==a['sha256']
        assert p['locator']['block_indices']==r['block_indices'];assert p['rich_ir']['record_sha256']==h(json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
        expected=Structure();expected.feed(r['semantic_html']);actual=Structure();actual.feed(row['full_text']);assert (expected.events,expected.cells,expected.image_positions)==(actual.events,actual.cells,actual.image_positions)
        totals.update(actual.tags);totals['image_markers']+=len(actual.image_positions);totals['source_list_groups']+=len(r.get('source_list_groups',[]));totals['notes_metadata']+=len(r['notes']);tableattrs.extend(actual.cells)
    for folder,stem,expected in [('', 'aggregate-fulltext',corpus),('', 'aggregate-toc',toc),('publications/'+pid+'/', 'fulltext',corpus),('publications/'+pid+'/', 'toc',toc)]:
        b=(root/(folder+stem+'.csv')).read_bytes();assert b[:3]==b'\xef\xbb\xbf';csv.field_size_limit(64*1024*1024);reader=csv.DictReader(io.StringIO(b.decode('utf-8-sig'),newline=''));assert reader.fieldnames==FIELDS and list(reader)==expected
        assert load(root/(folder+stem+'.json'))['provisions']==expected
    proof=load(root/'evidence/proofs/read-only-proof.json');assert tree(evidence)==proof['evidence_sha256_before']==proof['evidence_sha256_after'];assert before==tree(root)
    assert totals['table']==377 and totals['image_markers']==882 and totals['source_list_groups']==11
    return {'passed':True,'scope':'All2661 exported rows versus exact verified rich IR; independent consumer/CSV/source-evidence joins, no raw source normalizer rerun or new semantic claim','record_count':len(corpus),'toc_source_nodes':len(edges),'body_only_source_nodes':len(nodes)-len(edges),'source_disposition_count':len(disp),'copied_original_files':len(proof['evidence_sha256_before']),'preserved_tags':dict(totals),'preserved_cells':len(tableattrs),'populated_corpus_fields':dict(fieldcounts),'source_backed_toc_parents':parent_count,'source_consistency_complete':cov['source_consistency_complete'],'publication_accepted':cov['publication_accepted'],'package_complete':manifest['complete'],'package_unchanged':True,'network_requests':0,'image_decode_render_extraction_calls':0}
if __name__=='__main__':print(json.dumps(audit(sys.argv[1]),indent=2))
