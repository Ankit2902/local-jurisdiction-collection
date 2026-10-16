"""King County complete section DOM ranges, alphanumeric numbering and Charter profile."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from datetime import date
from urllib.parse import urljoin,urlparse,quote
from bs4 import BeautifulSoup,Tag
from common import clean,decode,semantic,readable,record,sha,dump,package
TITLE=re.compile(r'^Title\s+\d+[A-Z]?(?::|\s)',re.I)
SECTION=re.compile(r'^(\d+[A-Z]?(?:\.\d+[A-Z]?){2,})\s+(.+)$',re.I)
CHARTER=re.compile(r'^(?:Section\s+)?(\d{3}(?:\.\d+)*[A-Z]?)\.?\s+(.+)$',re.I)
CHAPTER=re.compile(r'^(\d+[A-Z]?\.\d+[A-Z]?)\s+',re.I)

def landing_inventory(html,base):
    s=BeautifulSoup(html,'html.parser');documents=[]
    for h in s.select('h3'):
        a=h.find('a',href=True)
        if not a:continue
        url=urljoin(base,a['href']);label=clean(a.get_text(' ',strip=True))
        if urlparse(url).hostname!='aqua.kingcounty.gov':continue
        context=[];formats=[]
        for sib in h.next_siblings:
            if isinstance(sib,Tag) and sib.name in {'h2','h3'}:break
            if isinstance(sib,Tag):
                context.append(clean(sib.get_text(' ',strip=True)))
                formats.extend({'label':clean(x.get_text()),'url':urljoin(base,x['href'])} for x in sib.select('a[href]'))
        currency=re.search(r'\(Updated[^)]*\)',' '.join(context),re.I)
        kind='title' if TITLE.match(label) else 'charter' if label.casefold()=='charter' else 'editorial_reference'
        documents.append({'publication_id':'charter' if kind=='charter' else 'county-code','kind':kind,'label':label,'url':url,'alternatives':formats,'updated_marker_raw':currency.group(0) if currency else '', 'scope_decision':'in_scope' if kind in ('charter','title') else 'editorial_reference'})
    related=[]
    for a in s.select('a[href]'):
        text=clean(a.get_text(' ',strip=True))
        if 'Board of Health code' in text:related.append({'label':text,'url':urljoin(base,a['href']),'scope_decision':'separate_compilation_requires_scope_review'})
    return {'documents':documents,'related_publications':list({x['url']:x for x in related}.values())}

def atomic_blocks(root):
    """Walk source order, treating tables/lists as whole semantic blocks once."""
    for n in root.children:
        if not isinstance(n,Tag):continue
        if n.name in {'script','style','nav','head'}:continue
        if n.name in {'p','h1','h2','h3','h4','table','ul','ol','pre','blockquote'}:yield n
        else:yield from atomic_blocks(n)

def parse_title(data,url,charter=False,raw_path='',content_type='',scrape_date=None):
    if b'[Truncated]' in data:raise ValueError('Truncated DOM capture rejected; reacquire in chunks')
    text,encoding=decode(data,content_type);s=BeautifulSoup(text,'html.parser');blocks=list(atomic_blocks(s.body or s))
    title_label=next((clean(p.get_text(' ',strip=True)) for p in s.select('p') if re.fullmatch(r'Title\s+\d+[A-Z]?',clean(p.get_text(' ',strip=True)),re.I)),'')
    pattern=CHARTER if charter else SECTION
    nodes=[];rows=[];disp=[];provenance=[];toc=[];chapter='';article='';active=None;body=[];editorial=False
    def flush():
        nonlocal active,body
        if active is None:return
        html=''.join(semantic(x) for x in body);full=readable(html);rid=sha(active['node_id'].encode())
        disposition='included' if full else 'structural'
        if full:
            rows.append(record(jurisdiction='King County, WA',code_name='Charter' if charter else 'King County Code',title=title_label,chapter=active.get('chapter',''),article=active.get('article',''),section_number=active['display_number'],section_name=active['display_heading'],citation=active['citation'],full_text=full,source_url=active['source_url'],scrape_date=scrape_date or date.today().isoformat()))
        disp.append({'node_id':active['node_id'],'disposition':disposition,'record_ids':[rid] if full else []})
        if full:provenance.append({'record_id':rid,'node_id':active['node_id'],'raw_sha256':sha(data),'locator':active['locator'],'semantic_html':html,'parser_version':'bulk-official-html-1','encoding':encoding})
        active=None;body=[]
    for idx,b in enumerate(blocks):
        label=clean(b.get_text(' ',strip=True)); bold=next((x for x in b.find_all(['b','strong']) if clean(x.get_text(' ',strip=True))),None)
        leading=clean(bold.get_text(' ',strip=True)) if bold else ''
        if leading and re.fullmatch(r'(?:Section\s+)?\d+[A-Z]?(?:\.\d+[A-Z]?)*\.?',leading,re.I):
            following=[x for x in b.find_all(['b','strong']) if clean(x.get_text(' ',strip=True))]
            if len(following)>1:leading+=' '+clean(following[1].get_text(' ',strip=True))
        match=pattern.match(leading)
        if b.name in {'h1','h2'}:
            flush()
            if CHAPTER.match(label):chapter=label
            if charter:
                article=label
                editorial=not (label=='PREAMBLE' or label.startswith('ARTICLE '))
            nid=url+'::block-'+str(idx)
            node={'node_id':nid,'node_kind':'container','display_number':'','display_heading':label,'source_url':url,'parent_node_id':None,'source_order':len(nodes),'raw_sha256':sha(data),'raw_artifact_path':raw_path,'locator':{'kind':'atomic-block-index','value':idx},'citation':label,'chapter':chapter,'article':article}
            nodes.append(node)
            if charter and (label=='PREAMBLE' or label.startswith('ARTICLE ')):
                active=node;body=[]
            else:disp.append({'node_id':nid,'disposition':'editorial_reference' if editorial else 'structural','record_ids':[]})
            continue
        # Publisher heading paragraphs: bold citation at paragraph start, never a reference mid-body.
        is_heading=match and label.startswith(match.group(1) if not leading.startswith('Section ') else 'Section '+match.group(1))
        if is_heading and not editorial:
            flush();num,name=match.groups();anchor=b.get('id') or next((a.get('id') or a.get('name') for a in b.select('a[id],a[name]')),None)
            source=url+'#'+quote(anchor) if anchor else url
            nid=url+'::block-'+str(idx)
            active={'node_id':nid,'parent_node_id':None,'node_kind':'section','display_number':num,'display_heading':name,'citation':leading,'source_url':source,'raw_artifact_path':raw_path,'raw_sha256':sha(data),'source_order':len(nodes),'locator':{'kind':'atomic-block-index','value':idx},'chapter':chapter,'article':article}
            nodes.append(active);body=[b]
        elif active is not None:body.append(b)
        elif pattern.match(label) and not bold and not editorial:
            m=pattern.match(label);toc.append({'number':m.group(1),'heading':m.group(2),'chapter':chapter,'locator':{'kind':'atomic-block-index','value':idx}})
    flush()
    updated=re.search(r'UPDATED:\s*[^\n<]+',text,re.I)
    return {'rows':rows,'nodes':nodes,'dispositions':disp,'provenance':provenance,'toc':toc,'encoding':encoding,'updated_marker_raw':updated.group(0) if updated else '', 'tables':len(s.select('table'))}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--source-url',required=True);ap.add_argument('--charter',action='store_true');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    result=parse_title(a.input.read_bytes(),a.source_url,a.charter,str(a.input));print(package(a.out,'King County, WA','charter' if a.charter else 'county-code',result['rows'],result['nodes'],result['dispositions'],result['provenance'],sha(a.input.read_bytes()),[a.input]));dump(a.out/'independent-section-toc.json',result['toc'])
if __name__=='__main__':main()
