"""San Mateo publisher-designated repository acquisition and namespace-aware XML replay."""
from __future__ import annotations
import argparse, html, json, re, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import date
from collections import Counter,defaultdict
from common import acquire, clean, dump, sha, record, readable, package
REPO='cityofsanmateo/law-xml'
BASE='us/ca/cities/san-mateo/'
STRUCT={'container','section'}
META={'prefix','num','heading','meta'}
def local(n):return n.tag.rsplit('}',1)[-1]
def child(n,name):return next((x for x in n if local(x)==name),None)
def value(n,name):
    c=child(n,name);return clean(''.join(c.itertext())) if c is not None else ''
def label(n):return ' '.join(x for x in [value(n,'prefix'),value(n,'num'),value(n,'heading')] if x)
def markup(n):
    """XML vocabulary to semantic HTML; original XML remains authoritative sidecar."""
    name=local(n)
    if name in ('image','img'):return '<span data-image-src="'+html.escape(n.get('src',n.get('href','')),quote=True)+'">[IMAGE]</span>'
    if name=='include':return '<p>[UNRESOLVED INCLUDE: '+html.escape(n.get('href',''))+']</p>'
    tag={'text':'p','para':'div','num':'span','heading':'strong','annotations':'div','annotation':'p','cite':'a','note':'aside','footnote':'aside','italic':'em','bold':'strong'}.get(name,name if name in {'table','thead','tbody','tfoot','tr','td','th','sup','sub','ol','ul','li','p','span','br'} else 'div')
    attrs=''.join(' '+k+'="'+html.escape(v,quote=True)+'"' for k,v in n.attrib.items() if k in {'rowspan','colspan','start','value','type','href','src','id'})
    content=html.escape(n.text or '')
    for c in n:
        # Formatting indentation must not join list labels to their text.
        content+=markup(c)+(' ' if local(c)=='num' else '')+html.escape(c.tail or '')
    if name=='annotation' and not clean(''.join(n.itertext())):
        content=html.escape(' '.join(x for x in [n.get('type',''),n.get('doc',''),n.get('path','')] if x))
    return '<'+tag+attrs+'>'+content+'</'+tag+'>'

def parse_xml(data, source_url, publication='municipal-code', version='', raw_path='', scrape_date=None):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():raise ValueError('external/entity XML unsupported')
    root=ET.fromstring(data);nodes=[];rows=[];dispositions=[];provenance=[]
    def visit(n,indices,trail,parent):
        kind=local(n);locator={'kind':'xml-child-indices','value':indices,'expanded_tag':n.tag}
        node_id=source_url+'::'+('/'.join(map(str,indices)) or 'root')
        owned=[c for c in n if local(c) not in STRUCT|META]
        structured=''.join(markup(c) for c in owned)
        text=readable(structured)
        includes=[x.get('href','') for c in owned for x in c.iter() if local(x)=='include']
        node={'node_id':node_id,'parent_node_id':parent,'publication_id':publication,'source_order':len(nodes),'node_kind':kind,'display_number':value(n,'num'),'display_heading':value(n,'heading'),'source_url':source_url,'raw_artifact_path':raw_path,'raw_sha256':sha(data),'locator':locator,'source_attributes':dict(n.attrib),'hierarchy':trail,'source_version':version}
        nodes.append(node)
        # Headers alone are structural; operative container bodies and notes survive.
        emit=bool(text) or kind=='section'
        disposition='unresolved' if includes else ('included' if emit and text else ('reserved_or_repealed' if re.search(r'reserved|repealed',label(n),re.I) else 'structural'))
        record_ids=[]
        if emit:
            rid=sha(node_id.encode());record_ids=[rid]
            hierarchy={}
            for t in trail:
                prefix=t['prefix'].lower()
                if prefix in {'division','title','subtitle','chapter','subchapter','article','part','subpart'}:hierarchy[prefix]=t['label']
            rows.append(record(jurisdiction='San Mateo, CA',code_name='Charter' if publication=='charter' else 'Municipal Code',section_number=value(n,'num') if kind=='section' else '',section_name=value(n,'heading'),citation=label(n),full_text=text,source_url=source_url,scrape_date=scrape_date or date.today().isoformat(),**hierarchy))
            provenance.append({'record_id':rid,'node_id':node_id,'publication_id':publication,'source_version':version,'raw_sha256':sha(data),'locator':locator,'semantic_html':structured,'owned_xml':'\n'.join(ET.tostring(c,encoding='unicode') for c in owned),'parser_version':'bulk-official-html-1','includes_unresolved':includes})
        dispositions.append({'node_id':node_id,'disposition':disposition,'record_ids':record_ids,'reason':'Includes need explicit resolution' if includes else 'Own body only; child structural nodes visited independently'})
        next_trail=trail+[{'prefix':value(n,'prefix'),'number':value(n,'num'),'label':label(n)}]
        for index,c in enumerate(n):
            if local(c) in STRUCT:visit(c,indices+[index],next_trail,node_id)
    visit(root,[],[],None)
    return {'rows':rows,'nodes':nodes,'dispositions':dispositions,'provenance':provenance,'tag_counts':dict(Counter(local(x) for x in root.iter()))}

def publication_inventory(tree,commit):
    if tree.get('truncated'):raise ValueError('Git tree truncated; cannot claim repository inventory')
    families=defaultdict(list)
    for item in tree.get('tree',[]):
        if item['type']=='blob' and item['path'].startswith(BASE):families[item['path'][len(BASE):].split('/')[0]].append(item)
    return [{'publication_id':'municipal-code' if name=='code' else name,'repository_family':name,'root':BASE+name,'commit':commit,'file_count':len(items),'scope_decision':('in_scope_code' if name=='code' else 'in_scope_charter' if name=='charter' else 'editorial_reference' if name in ('editorial-actions','drafting-manual') else 'excluded_uncodified_ordinances' if name=='ordinances' else 'unresolved'), 'scope_evidence':'Repository family path; no legal currency inferred from commit','files':items} for name,items in sorted(families.items())]

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    a=sub.add_parser('acquire');a.add_argument('--commit',required=True,help='full immutable 40-character commit SHA');a.add_argument('--out',type=Path,required=True);a.add_argument('--archive',action='store_true',help='Retain complete publisher repository archive; no full extraction')
    p=sub.add_parser('parse');p.add_argument('--input',type=Path,required=True);p.add_argument('--source-url',required=True);p.add_argument('--commit',required=True);p.add_argument('--publication',default='municipal-code');p.add_argument('--out',type=Path,required=True);p.add_argument('--scrape-date',default=None)
    args=ap.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.commit):ap.error('--commit must be a complete immutable SHA')
    if args.command=='acquire':
        args.out.mkdir(parents=True,exist_ok=True)
        for label_,url in [('commit',f'https://api.github.com/repos/{REPO}/commits/{args.commit}'),('tree',f'https://api.github.com/repos/{REPO}/git/trees/{args.commit}?recursive=1')]:acquire(url,args.out/(label_+'.json'))
        tree=json.loads((args.out/'tree.json').read_text());dump(args.out/'publications.json',publication_inventory(tree,args.commit))
        if args.archive:acquire(f'https://github.com/{REPO}/archive/{args.commit}.zip',args.out/'repository.zip',timeout=60)
    else:
        result=parse_xml(args.input.read_bytes(),args.source_url,args.publication,args.commit,str(args.input),args.scrape_date)
        print(package(args.out,'San Mateo, CA',args.publication,result['rows'],result['nodes'],result['dispositions'],result['provenance'],args.commit,[args.input]))
if __name__=='__main__':main()
