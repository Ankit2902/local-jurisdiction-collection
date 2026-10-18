"""Typed publisher ancestry and printed heading components; no ID-number guessing."""
import re
from html.parser import HTMLParser
from urllib.parse import urldefrag
from common import require,sha,canonical

class FinishedHeading(Exception):pass
class Heading(HTMLParser):
    def __init__(self,level):
        super().__init__(convert_charrefs=True);self.level=level;self.depth=0;self.text=[];self.attrs={};self.anchors=[];self.current=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if not self.depth:
            if tag!=self.level:return
            self.depth=1;self.attrs=attrs;return
        if tag=='br':self.text.append(' ');return
        if tag not in ['hr','img','input','meta','link','wbr']:self.depth+=1
        if tag=='a':self.current={'attributes':attrs,'text':[]};self.anchors.append(self.current)
    def handle_startendtag(self,tag,attrs):
        if tag=='br' and self.depth:self.text.append(' ')
    def handle_data(self,text):
        if self.depth:
            self.text.append(text)
            if self.current is not None:self.current['text'].append(text)
    def handle_endtag(self,tag):
        if self.depth:
            if tag=='a':self.current=None
            self.depth-=1
            if not self.depth:raise FinishedHeading()
def clean(s):return re.sub(r'\s+',' ',s).strip()
def heading(record):
    if not record['source_heading_level']:return None
    p=Heading(record['source_heading_level'])
    try:p.feed(record['semantic_html'])
    except FinishedHeading:pass
    text=clean(''.join(p.text).replace('[IMAGE]',''))
    if not text or text!=record['heading'] or p.attrs.get('class','').split()!=record.get('source_heading_classes',[]):return None
    return {'text':text,'tag':record['source_heading_level'],'classes':record.get('source_heading_classes',[]),'attributes':p.attrs,'anchors':[{'attributes':a['attributes'],'text':clean(''.join(a['text']))} for a in p.anchors]}

def typed_role(record,h):
    if h is None:return 'unheaded_body' if record['source_heading_level'] is None else 'unqualified_heading'
    classes=h['classes'];tag=h['tag'];text=h['text']
    if classes==['Title'] and tag=='h1':return 'title'
    if classes==['Cite'] and tag=='h3':return 'section'
    if classes==['Division'] and tag=='p':return 'division'
    if classes==['CH'] and tag=='h2':
        for literal,role in [('CHAPTER','chapter'),('ARTICLE','article'),('SECTION','source_section_group')]:
            if re.match('^'+literal+r'\b',text,re.I):return role
    if classes==['CH'] and tag=='h2' and text=='APPENDICES':return 'source_appendices_group'
    if classes==['CHTitle'] and tag=='h2':return 'chapter_title_continuation'
    return 'unqualified_heading'

def section_number(h):
    """Use a visible heading locator only if its own published name/id agrees."""
    if not h:return '',{'status':'unqualified_no_canonical_heading'}
    match=re.match(r'^(?:SECTION\s+|SEC\.\s+|§\s*)?(Amendment No\. \d+|[A-Z]+-\d+(?:[-.][A-Za-z0-9]+)*|\d+(?:[-.][A-Za-z0-9]+)*)(?=\s|$)',h['text'],re.I)
    if not match:return '',{'status':'source_unnumbered_heading','heading_text':h['text']}
    printed=match[1];same=lambda v:clean(v).replace('-','.')==printed.replace('-','.')
    witnesses=[]
    for a in [{'attributes':h['attributes'],'text':''}]+h['anchors']:
        attrs=a['attributes']
        for key in ['id','name']:
            if attrs.get(key) and same(attrs[key]) and (not a['text'] or a['text']==printed):witnesses.append({'attribute':key,'value':attrs[key],'visible_anchor_text':a['text']})
    if not witnesses:return '',{'status':'unqualified_displayed_locator_has_no_agreeing_source_anchor','displayed_candidate':printed}
    return printed,{'status':'qualified_displayed_heading_and_own_anchor','printed':printed,'heading_text':h['text'],'anchor_witnesses':witnesses,'normalization':'Comparison only: published dash/dot locator separators compared equivalently; emitted number is original displayed text, never an ID conversion'}

def derive(records,inventory,mapping):
    """Returns per-node parent and per-record fields with explicit evidence.

    Full ancestry paths, not bare source_id or printed numbers, disambiguate IDs.
    Body-only units use the common published parent ancestry of that document.
    """
    byrid={r['record_id']:r for r in records};edges={e['edge_id']:e for e in inventory};paths={};by_path={};issues=[]
    for e in inventory:
        path=tuple(e.get('ancestor_classes') or e['source_id'].split());key=(e['root_index'],path)
        own=tuple(e['source_id'].split())
        require(bool(own) and path[-len(own):]==own,'Publisher source ID is not exact ancestry suffix')
        paths[e['edge_id']]=key;by_path.setdefault(key,[]).append(e['edge_id'])
    parents={};parent_evidence={}
    for eid,e in edges.items():
        root,path=paths[eid]
        own=tuple(e['source_id'].split());parent_path=path[:-len(own)]
        if not parent_path:
            parents['toc:'+eid]=None;parent_evidence['toc:'+eid]={'status':'publisher_component_root','root_index':root,'source_path':list(path)};continue
        candidates=by_path.get((root,parent_path),[])
        if len(candidates)==1:
            parents['toc:'+eid]='toc:'+candidates[0];status='qualified_full_publisher_ancestor_path'
        else:
            parents['toc:'+eid]=None;status='unqualified_missing_or_ambiguous_publisher_parent';issues.append({'edge_id':eid,'issue':status,'candidate_edge_ids':candidates})
        parent_evidence['toc:'+eid]={'status':status,'root_index':root,'source_path':list(path),'parent_candidates':candidates}
    rnodes={rid:[] for rid in byrid}
    for eid,rid in mapping.items():rnodes[rid].append('toc:'+eid)
    for r in records:
        rid=r['record_id']
        if rnodes[rid]:continue
        nid='body:'+rid;rnodes[rid]=[nid];doc=urldefrag(r['source_url'])[0]
        relevant=[eid for eid in edges if urldefrag(edges[eid]['source_url'])[0]==doc]
        roots={paths[eid][0] for eid in relevant};candidate=None
        # An unheaded book introduction is contextual to its explicit document root.
        exactroots=[eid for eid in relevant if not paths[eid][1][:-len(edges[eid]['source_id'].split())]]
        if r['source_heading_level'] is None and len(exactroots)==1:candidate=exactroots[0]
        elif len(roots)==1 and relevant:
            sequences=[paths[eid][1][:-len(edges[eid]['source_id'].split())] for eid in relevant];prefix=[]
            for components in zip(*sequences):
                if len(set(components))!=1:break
                prefix.append(components[0])
            candidates=by_path.get((next(iter(roots)),tuple(prefix)),[])
            if len(candidates)==1:candidate=candidates[0]
        parents[nid]='toc:'+candidate if candidate else None
        parent_evidence[nid]={'status':'qualified_document_root_or_shared_published_parent_ancestry' if candidate else 'unqualified_body_only_parent','document_source_url':doc,'source_context_edge_ids':relevant,'qualified_parent_edge_id':candidate}
        if candidate is None:issues.append({'record_id':rid,'issue':'unqualified_body_only_parent'})
    heads={rid:heading(r) for rid,r in byrid.items()};roles={rid:typed_role(r,heads[rid]) for rid,r in byrid.items()};labels={rid:r['heading'] for rid,r in byrid.items()};roleproof={}
    for i,r in enumerate(records):
        rid=r['record_id'];roleproof[rid]={'typed_source_heading':heads[rid],'role':roles[rid],'source_record_id':rid,'raw_sha256':r['source_sha256']}
        if roles[rid]=='chapter_title_continuation':
            prev=records[i-1] if i else None
            qualified=bool(prev and roles[prev['record_id']]=='chapter' and prev['source_sha256']==r['source_sha256'] and urldefrag(prev['source_url'])[0]==urldefrag(r['source_url'])[0] and prev['full_text']==prev['heading'] and max(prev['block_indices'])+1==min(r['block_indices']))
            if qualified:
                roles[rid]='chapter';labels[rid]=prev['heading']+'\n'+r['heading'];roleproof[rid].update(role='chapter',qualification='Explicit adjacent h2.CH + h2.CHTitle printed continuation, same raw source and consecutive source blocks; records/bodies remain separate',ordered_heading_record_ids=[prev['record_id'],rid],ordered_displayed_components=[prev['heading'],r['heading']])
            else:roles[rid]='unqualified_heading';issues.append({'record_id':rid,'issue':'Unqualified chapter title continuation'})
        if roles[rid]=='unqualified_heading':issues.append({'record_id':rid,'issue':'Unknown/conflicting typed source heading'})
    node_owner={'toc:'+eid:rid for eid,rid in mapping.items()};node_owner.update({'body:'+rid:rid for rid in byrid if rnodes[rid][0].startswith('body:')})
    result={}
    for rid,r in byrid.items():
        alternatives=[];chains=[]
        for nid in rnodes[rid]:
            chain=[];seen=set();current=nid
            while current:
                require(current not in seen,'Publisher ancestry cycle');seen.add(current);chain.append(current);current=parents[current]
            chain.reverse();fields={k:'' for k in ['division','title','subtitle','chapter','subchapter','article','part','subpart']};proofs={}
            for n in chain:
                owner=node_owner[n];role=roles[owner]
                if role in fields:fields[role]=labels[owner];proofs[role]=dict(roleproof[owner],source_node_id=n)
            alternatives.append((fields,proofs));chains.append(chain)
        fields,proofs=alternatives[0]
        if any(x[0]!=fields for x in alternatives):
            fields={k:'' for k in fields};proofs={};issues.append({'record_id':rid,'issue':'Conflicting multiple source hierarchy paths; fields deliberately blank'})
        number,numberproof=section_number(heads[rid]) if roles[rid] in ['section','source_section_group'] else ('',{'status':'not_a_source_section_or_section_group'})
        name=r['heading'] if r['source_heading_level'] else ''
        if roles[rid]=='section' and number and name.startswith(number):name=name[len(number):].lstrip()
        if roles[rid]=='section' and not number and numberproof['status']!='source_unnumbered_heading':issues.append({'record_id':rid,'issue':'No unambiguous displayed own section locator','evidence':numberproof})
        result[rid]={'fields':dict(fields,section_number=number,section_name=name),'source_chains':chains,'field_evidence':proofs,'section_number_evidence':numberproof,'source_role':roles[rid]}
    return {'parents':parents,'parent_evidence':parent_evidence,'records':result,'issues':issues,'roles':roles}
