"""Daly City current Municode route; historical eLaws parser is explicitly separate."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from datetime import date
from urllib.parse import urljoin,urlparse,urlencode
from bs4 import BeautifulSoup
from common import acquire,clean,decode,semantic,readable,record,sha,dump,package
ROOT='https://library.municode.com/ca/daly_city/codes/code_of_ordinances'
SECTION=re.compile(r'^(?:§\s*)?(\d+(?:\.\d+)+[A-Z]?)\s*[-–—:]\s*(.+)$',re.I)
def route_evidence(html):
    s=BeautifulSoup(html,'html.parser');links=[]
    for a in s.select('a[href]'):
        u=urljoin('https://www.dalycity.org/',a['href'])
        if urlparse(u).hostname in {'library.municode.com','dalycity-ca.elaws.us'}:links.append({'label':clean(a.get_text(' ',strip=True)),'url':u})
    return list({x['url']:x for x in links}.values())

def inventory(tree):
    result=[];seen=set()
    def visit(n,parent,trail):
        ident=str(n.get('Id',''))
        if not ident or ident in seen:raise ValueError('Missing/duplicate TOC node identity')
        seen.add(ident);heading=clean(n.get('Heading',''));children=n.get('Children') or []
        result.append({'node_id':ident,'parent_node_id':parent,'source_order':len(result),'node_kind':'section' if SECTION.match(heading) else 'container','display_heading':heading,'hierarchy':trail,'has_children':bool(children),'source_url':ROOT+'?'+urlencode({'nodeId':ident})})
        for c in children:visit(c,ident,trail+[heading])
    visit(tree,None,[]);return result

def parse_content(payload,node,raw_bytes,raw_path='',scrape_date=None):
    docs=[d for d in payload.get('Docs',[]) if d.get('Id')==node['node_id']]
    if len(docs)!=1:raise ValueError('Requested source node absent or ambiguous in chapter response')
    d=docs[0];heading=clean(d.get('Title',''))
    if heading!=node['display_heading']:raise ValueError('TOC/content heading drift')
    m=SECTION.match(heading)
    if not m:raise ValueError('Explicit substantive-container profile required for unnumbered node')
    soup=BeautifulSoup(d.get('Content',''),'html.parser');body=soup.select_one('.chunk-content')
    if body is None:raise ValueError('No legal content; shell rejected')
    structured=semantic(body);text=readable(structured)
    if not text:raise ValueError('Empty source body requires disposition review')
    hierarchy={}
    for t in node.get('hierarchy',[]):
        for kind in ('title','chapter','article','part'):
            if t.lower().startswith(kind+' '):hierarchy[kind]=t
    row=record(jurisdiction='Daly City, CA',code_name='Code of Ordinances',section_number=m.group(1),section_name=m.group(2),citation=heading,full_text=text,source_url=node['source_url'],scrape_date=scrape_date or date.today().isoformat(),**hierarchy)
    identity='16311::'+node['node_id'];rid=sha(identity.encode());source_node=dict(node,raw_artifact_path=raw_path,raw_sha256=sha(raw_bytes),publication_id='municipal-code',locator={'kind':'json-doc-id','value':node['node_id']})
    provenance={'record_id':rid,'node_id':node['node_id'],'publication_id':'municipal-code','raw_sha256':sha(raw_bytes),'locator':source_node['locator'],'semantic_html':structured,'source_title_html':d.get('TitleHtml',''),'footnotes':d.get('Footnotes'),'parser_version':'bulk-official-html-1'}
    return row,source_node,{'node_id':node['node_id'],'disposition':'included','record_ids':[rid]},provenance

def parse_elaws(html,url,toc_heading=None,scrape_date=None):
    """Historical mode only: heading/TOC corroboration, never URL-only identity."""
    if urlparse(url).hostname!='dalycity-ca.elaws.us' or not urlparse(url).path.startswith('/code/coor'):raise ValueError('Outside historical publication boundary')
    s=BeautifulSoup(html,'html.parser');body=s.select_one('.Daly.City_content')
    if body is None:raise ValueError('Missing legal container; error/shell rejected')
    candidates=[clean(h.get_text(' ',strip=True)) for h in s.select('h1,h2,h3,.title')]
    if toc_heading:candidates.append(toc_heading)
    matches=[SECTION.match(x) for x in candidates];matches=[x for x in matches if x]
    if not matches:raise ValueError('Source heading/TOC identity required; URL inference forbidden')
    identities={(m.group(1),m.group(2)) for m in matches}
    if len(identities)!=1:raise ValueError('Conflicting source identities')
    num,name=identities.pop();return record(jurisdiction='Daly City, CA',code_name='Code of Ordinances (historical eLaws)',section_number=num,section_name=name,citation=num+' - '+name,full_text=readable(semantic(body)),source_url=url,scrape_date=scrape_date or date.today().isoformat())

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    a=sub.add_parser('acquire');a.add_argument('--out',type=Path,required=True);a.add_argument('--node-id',action='append',default=[],help='Observed fullTree node ID, up to four; never full corpus')
    p=sub.add_parser('parse');p.add_argument('--toc',type=Path,required=True);p.add_argument('--content',type=Path,required=True);p.add_argument('--node-id',required=True);p.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.command=='acquire':
        if len(args.node_id)>4:ap.error('Bounded validation limit is four content requests')
        base='https://library.municode.com'
        for filename,url in [('clients.json',base+'/api/Clients/keyword?keyword=daly+city'),('publications.json',base+'/api/ClientContent/1857'),('toc.json',base+'/api/codesToc/fullTree/latest?productId=16311&nodeId=16311')]:acquire(url,args.out/filename,headers={'X-CSRF':'1'})
        client=json.loads((args.out/'clients.json').read_text())
        if not any(c.get('ClientID')==1857 and c.get('ClientName')=='Daly City' and c.get('State',{}).get('StateAbbreviation')=='CA' for c in client):raise ValueError('Client changed; requalify')
        publications=json.loads((args.out/'publications.json').read_text())
        if not any(c.get('productId')==16311 and c.get('productName')=='Code of Ordinances' for c in publications['codes']):raise ValueError('Publication changed; requalify')
        toc=inventory(json.loads((args.out/'toc.json').read_text()));ids={n['node_id'] for n in toc}
        for i,ident in enumerate(args.node_id):
            if ident not in ids:raise ValueError('Node not in independent TOC')
            acquire(base+'/api/codesContent?'+urlencode({'productId':16311,'nodeId':ident}),args.out/f'content-{i}.json',headers={'X-CSRF':'1'})
    else:
        nodes=inventory(json.loads(args.toc.read_text()));node=next(n for n in nodes if n['node_id']==args.node_id);data=args.content.read_bytes();row,n,d,p=parse_content(json.loads(data),node,data,str(args.content))
        print(package(args.out,'Daly City, CA','municipal-code',[row],[n],[d],[p],sha(args.toc.read_bytes()),[args.toc,args.content]))
if __name__=='__main__':main()
