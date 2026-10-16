#!/usr/bin/env python3
"""Replayable, fail-closed CivicPlus PDF pilot collector. Python 3.10+."""
from __future__ import annotations
import argparse, csv, hashlib, html, json, re, shutil, sys, time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import json5
import pdfplumber
import requests
from bs4 import BeautifulSoup

VERSION = 'civicplus-layout-e2e-1.1'
FIELDS = 'jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()
ROOTS = {'portland-me':'https://portlandmaine.gov/city-code','rockland-me':'https://rocklandmaine.gov/288/Charter-Code-Ordinances'}
UUID = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',re.I)
SECTION = re.compile(r'^Sec(?:tion)?\.?\s+(\d+(?:[-.]\d+)*)(?:\.)?\s+(.+)$',re.I)
TOC_ENTRY = re.compile(r'^(\d+(?:[-.]\d+)*)\s+([A-Za-z].*)$')


def sha(data): return hashlib.sha256(data).hexdigest()
def readj(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def writej(p, data):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jsonl(p, rows): Path(p).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
def now(): return datetime.now(timezone.utc).isoformat()
def norm(s): return ' '.join(s.split())

def js_object(script, start):
    """Read a data-only object, respecting braces inside quoted strings. Never eval JS."""
    depth=0; quote=None; escape=False
    for pos in range(start,len(script)):
        c=script[pos]
        if quote:
            if escape: escape=False
            elif c=='\\': escape=True
            elif c==quote: quote=None
        elif c in '\"\'': quote=c
        elif c=='{': depth+=1
        elif c=='}':
            depth-=1
            if not depth:
                # CivicPlus minifier's boolean literals; replace outside strings only.
                literal=script[start:pos+1]
                tokens=re.split(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')',literal)
                return json5.loads(''.join(t if i%2 else re.sub(r'!([01])',lambda m:'true' if m[1]=='0' else 'false',t) for i,t in enumerate(tokens)))
    raise ValueError('Unterminated widget data object')

def classify(label):
    if re.search(r'Charter (Index|Comparative)',label,re.I): return 'charter','editorial_reference'
    if re.search(r'Code (Index|Comparative)|Table of Contents',label,re.I): return 'municipal-code','editorial_reference'
    if re.search(r'City Charter',label,re.I): return 'charter','in_scope'
    return 'municipal-code','in_scope'

def portland_inventory(source, rendered=None):
    soup=BeautifulSoup(source,'html.parser'); candidates=[]
    for script in soup.find_all('script'):
        text=script.string or script.get_text()
        m=re.search(r'const\s+n\s*=\s*\{',text)
        if not m: continue
        obj=js_object(text,text.index('{',m.start()))
        if norm(obj.get('options',{}).get('header','')).casefold()=='city code documents':
            widget=re.search(r'renderWidget\(n,\s*"([^"]+)"',text)
            candidates.append((obj,widget[1] if widget else None))
    if len(candidates)!=1: raise ValueError(f'Expected exactly one semantic City Code Documents widget; found {len(candidates)}. Retain rendered HTML if platform changed.')
    obj,wid=candidates[0]; ids=obj.get('manualContentItemIds',[])
    if not ids or len(ids)!=len(set(ids)) or not all(UUID.fullmatch(x) for x in ids): raise ValueError('Invalid or duplicate widget membership')
    for i in ids:
        opt=obj.get('manualContentItemsOptions',{}).get(i,{})
        if opt.get('contentType')!='pdf' or not opt.get('isAsset'): raise ValueError('Non-PDF widget member: '+i)
    # Display order is columns, not the potentially stale manual selection order.
    display=[i for col in obj.get('columns',[]) for i in col]
    if display and (set(display)!=set(ids) or len(display)!=len(ids)): raise ValueError('Widget columns do not reconcile to membership')
    display=display or ids
    labels={}; urls={}
    if rendered:
        rs=BeautifulSoup(rendered,'html.parser'); wrapper=(rs.find(id=wid) or rs.find(id='widget'+wid)) if wid else None
        if not wrapper: raise ValueError('Rendered widget identity missing')
        for a in wrapper.select('a[href]'):
            match=UUID.search(a['href'])
            if match and match[0] in ids:
                labels[match[0]]=norm(a.get_text(' ',strip=True)); urls[match[0]]=urljoin(ROOTS['portland-me'],a['href'])
    rows=[]
    for n,i in enumerate(display):
        label=labels.get(i,''); family,scope=classify(label)
        rows.append({'node_id':i,'source_order':n,'selection_order':ids.index(i),'widget_id':wid,'label':label,'publication_id':family,'scope':scope if label else 'unresolved','url':urls.get(i,f'https://content.civicplus.com/api/assets/{i}'),'label_status':'observed_rendered' if label else 'requires_rendered_widget','locator':{'kind':'widget-membership','widget_id':wid,'column_order':n}})
    return rows

def rockland_inventory(source, base):
    soup=BeautifulSoup(source,'html.parser'); main=soup.find(id='page') or soup.find('main')
    if not main: raise ValueError('Official legal index content container missing')
    rows=[]; seen=set()
    for a in main.select('a[href]'):
        label=norm(a.get_text(' ',strip=True)); url=urljoin(base,a['href'])
        if not re.match(r'^(Chapter\s+\d+\b|City Charter\b)',label,re.I): continue
        parsed=urlparse(url)
        if parsed.hostname not in {'rocklandmaine.gov','www.rocklandmaine.gov'}: raise ValueError('Unexpected source host: '+url)
        m=re.search(r'/DocumentCenter/View/(\d+)/',parsed.path,re.I)
        if not m: raise ValueError('Unexpected document link: '+url)
        if m[1] in seen: continue
        seen.add(m[1]); family,scope=classify(label)
        rows.append({'node_id':'document-'+m[1],'source_order':len(rows),'label':label,'publication_id':family,'scope':scope,'url':url,'locator':{'kind':'documentcenter-id','value':m[1]}})
    if not rows or not any(r['publication_id']=='charter' for r in rows): raise ValueError('Code/Charter inventory incomplete or changed')
    return rows

class Fetcher:
    def __init__(self, out, delay=0.5):
        self.out=Path(out); self.out.mkdir(parents=True,exist_ok=True); self.delay=delay
        self.session=requests.Session(); self.session.headers['User-Agent']='CompliSolv source qualification/1.0 (sequential public-document retrieval)'
    def get(self,url,ext):
        key=sha(url.encode()); receipt=self.out/(key+'.response.json')
        if receipt.exists():
            meta=readj(receipt)
            if meta.get('status')!=200 or 'path' not in meta: raise ValueError('Cached unsuccessful acquisition; inspect receipt and use a fresh run after resolving transport: '+url)
            path=self.out/meta['path']
            if meta['status']==200 and path.exists() and sha(path.read_bytes())==meta['sha256']:
                if ext=='pdf' and not path.read_bytes().startswith(b'%PDF'): raise ValueError('Cached non-PDF response: '+url)
                return path,meta
            raise ValueError('Cached failed request exists. Use a new run directory after resolving access: '+url)
        start=now(); attempts=[]
        for attempt in range(3):
            time.sleep(self.delay)
            try:
                r=self.session.get(url,timeout=(15,60),allow_redirects=True)
                attempts.append({'attempt':attempt+1,'status':r.status_code})
            except requests.RequestException as e:
                attempts.append({'attempt':attempt+1,'error':str(e)})
                if attempt==2:
                    writej(receipt,{'url':url,'status':None,'attempts':attempts,'started_at':start,'retrieved_at':now()}); raise
                time.sleep(2**attempt); continue
            if r.status_code not in (429,503) or attempt==2: break
            wait=r.headers.get('Retry-After','')
            time.sleep(min(float(wait) if wait.isdigit() else 2**(attempt+1),30))
        data=r.content; path=self.out/(key+'.'+ext); path.write_bytes(data)
        meta={'url':url,'final_url':r.url,'status':r.status_code,'redirect_chain':[{'url':x.url,'status':x.status_code,'location':x.headers.get('Location')} for x in r.history],'headers':{k:v for k,v in r.headers.items() if k.lower() not in ('set-cookie',)},'attempts':attempts,'started_at':start,'retrieved_at':now(),'path':path.name,'sha256':sha(data),'transport':'http_tls_verified'}
        writej(receipt,meta)
        if r.status_code!=200: raise ValueError(f'HTTP {r.status_code}: {url}; saved receipt. Use supported browser or stop, never bypass access controls.')
        if ext=='pdf' and not data.startswith(b'%PDF'): raise ValueError('Non-PDF response: '+url)
        return path,meta

def discover(args):
    package=Path(args.out); raw=package/'raw'; raw.mkdir(parents=True,exist_ok=True)
    url=args.base_url or ROOTS[args.jurisdiction]
    if args.index_html:
        source=Path(args.index_html).read_bytes(); path=raw/(sha(source)+'.index.html'); path.write_bytes(source)
        meta={'url':url,'transport':args.transport,'sha256':sha(source),'path':path.name,'retrieved_at':args.retrieved_at or now(),'note':'Operator retained source; retrieval timestamp is operator declaration, no HTTP status inferred.'}
        writej(raw/(path.name+'.receipt.json'),meta)
    else:
        path,meta=Fetcher(raw).get(url,'html'); source=path.read_bytes()
    rendered=Path(args.rendered_html).read_text(encoding='utf-8') if args.rendered_html else None
    if rendered:
        data=rendered.encode(); (raw/(sha(data)+'.rendered.html')).write_bytes(data)
    docs=portland_inventory(source.decode('utf-8'),rendered) if args.jurisdiction=='portland-me' else rockland_inventory(source.decode('utf-8'),url)
    if (package/'inventory.json').exists() and readj(package/'inventory.json')['inventory_sha256']!=sha(source):
        raise ValueError('Inventory changed: use a fresh package directory to avoid mixing a previous acquisition snapshot.')
    for d in docs: d.update({'jurisdiction_slug':args.jurisdiction,'inventory_sha256':sha(source),'inventory_path':str(path.relative_to(package))})
    inv={'jurisdiction_slug':args.jurisdiction,'root_url':url,'parser_version':VERSION,'index_receipt':meta,'inventory_sha256':sha(source),'documents':docs,'coverage':'document_inventory_only','corpus_complete':False}
    writej(package/'inventory.json',inv)
    pubs=[]
    for pub in sorted({d['publication_id'] for d in docs}):
        pubs.append({'publication_id':pub,'official_title':'City Charter' if pub=='charter' else 'Code of Ordinances','scope':'in_scope','scope_evidence':'Official code widget/index explicitly links these documents','root_url':url,'document_count':sum(d['publication_id']==pub for d in docs),'currency_text':[d['label'] for d in docs if d['publication_id']==pub and 'Revised' in d['label']],'legal_current_through':None,'currency_note':'Per-document revision labels retained verbatim; no global current-through date inferred.'})
    writej(package/'publications.json',pubs)
    print(json.dumps({'inventory_documents':len(docs),'unresolved_labels':sum(not d['label'] for d in docs),'out':str(package)}))

def acquire(args):
    package=Path(args.package); inv=readj(package/'inventory.json'); wanted=set(args.id or [])
    if not wanted and not args.all: raise ValueError('Select --id document IDs or explicitly --all; bounded default never downloads corpus')
    available={d['node_id']:d for d in inv['documents']}
    if wanted-set(available): raise ValueError('Unknown source ID(s): '+str(wanted-set(available)))
    acquisition=readj(package/'acquisition.json') if (package/'acquisition.json').exists() else {}
    for ident,d in available.items():
        if not args.all and ident not in wanted: continue
        if d['scope']=='unresolved': raise ValueError('Resolve document identity/label before acquisition: '+ident)
        file,meta=Fetcher(package/'raw').get(d['url'],'pdf')
        acquisition[ident]={'raw_path':str(file.relative_to(package)),'sha256':meta['sha256'],'receipt':meta}
        writej(package/'acquisition.json',acquisition)
    print(json.dumps({'acquired_documents':len(acquisition)}))

def import_pdf(args):
    package=Path(args.package); inv=readj(package/'inventory.json'); docs={d['node_id']:d for d in inv['documents']}
    if args.id not in docs: raise ValueError('ID is not in retained official inventory')
    data=Path(args.file).read_bytes()
    if not data.startswith(b'%PDF'): raise ValueError('Not a PDF')
    target=package/'raw'/(sha(data)+'.pdf'); target.write_bytes(data)
    receipt={'transport':'browser_operator_download','source_url':docs[args.id]['url'],'retrieved_at':args.retrieved_at,'sha256':sha(data),'original_filename':Path(args.file).name,'note':args.note,'status':None}
    writej(target.with_suffix('.receipt.json'),receipt)
    acquisition=readj(package/'acquisition.json') if (package/'acquisition.json').exists() else {}
    acquisition[args.id]={'raw_path':str(target.relative_to(package)),'sha256':sha(data),'receipt':receipt}
    writej(package/'acquisition.json',acquisition)

def lines_from_chars(page):
    """Separate precise baselines; a floating footer must not contaminate body words."""
    groups=[]
    for c in sorted(page.chars,key=lambda c:(c['top'],c['x0'])):
        if not c['text'].strip(): continue
        if not groups or abs(c['top']-groups[-1][0]['top'])>0.7: groups.append([c])
        else: groups[-1].append(c)
    result=[]
    for chars in groups:
        chars.sort(key=lambda c:c['x0']); text=''; prev=None
        for c in chars:
            gap=c['x0']-prev['x1'] if prev else 0
            if prev and gap>max(1.3,c['size']*.18):
                text+=' ' * max(1,min(40,round(gap/(c['size']*.5))))
            text+=c['text']; prev=c
        result.append({'text':text,'bbox':[round(min(c['x0'] for c in chars),3),round(min(c['top'] for c in chars),3),round(max(c['x1'] for c in chars),3),round(max(c['bottom'] for c in chars),3)],'font_sizes':sorted(set(round(c['size'],2) for c in chars)),'fonts':sorted(set(c['fontname'] for c in chars))})
    return result

def footer_kind(line,page,profile):
    s=norm(line['text']); x,t,r,b=line['bbox']
    if t<0 or b>page.height+.5 or x<0 or r>page.width+.5: return 'outside_page_bounds'
    if profile=='portland':
        if t<110 and (s.startswith('City of Portland') or s.startswith('Code of Ordinances') or re.match(r'^Sec\.\s+[\d.-]+\s+Rev\.',s)): return 'running_header'
        if t>page.height*.88 and re.fullmatch(r'\d+(?:\.\d+)?-\d+',s) and x>page.width*.4 and r<page.width*.6: return 'page_number'
    if profile.startswith('rockland'):
        if t>page.height*.90 and re.fullmatch(r'(?:CH|\d+)-\d+',s): return 'page_number'
        if x>page.width*.65 and re.fullmatch(r'(?:Ch\.\s*\d+,\s*)?Sec\.\s*\d+(?:-\d+)*',s):
            boxed=any(q.get('fill') and q['x0']-1<=x and q['x1']+1>=r and q['top']-1<=t and q['bottom']+1>=b for q in page.rects)
            if t>page.height*.9 or boxed: return 'running_locator'
        if t>page.height*.9 and s=='CHAPTER 1': return 'running_chapter'
    return None

def page_quality(page,lines,profile=''):
    text=''.join(l['text'] for l in lines); reasons=[]
    images=[{'bbox':[i['x0'],i['top'],i['x1'],i['bottom']],'name':i.get('name')} for i in page.images]
    if images: reasons.append('mixed_text_image' if len(text.strip())>=40 else 'image_only_ocr_required')
    if len(text.strip())<40 and not images: reasons.append('sparse_or_blank_page_review')
    if '\ufffd' in text or '(cid:' in text: reasons.append('broken_text_mapping')
    # White floating locator boxes can hide legal words. Raw bytes are authoritative;
    # never silently accept recovered text behind the box as visually verified text.
    boxes=[r for r in page.rects if r.get('fill') and r['x0']>page.width*.65 and 0<r['top']<page.height]
    if not profile.startswith('rockland'): boxes=[]
    for box in boxes:
        if any(l['bbox'][0]<box['x0'] and l['bbox'][2]>box['x0'] and l['bbox'][1]<box['bottom'] and l['bbox'][3]>box['top'] for l in lines): reasons.append('source_footer_box_overlaps_legal_text'); break
    if any(l['bbox'][1]<0 or l['bbox'][3]>page.height+.5 for l in lines): reasons.append('off_page_native_text_review')
    if any(c['text'].strip() and c['size']<3 for c in page.chars): reasons.append('microscopic_heading_marker_review')
    if any(not c.get('upright',True) for c in page.chars): reasons.append('rotated_text_reading_order')
    return images,sorted(set(reasons))

def table_html(table):
    """Cell geometry remains authoritative, including missing/spanned cells."""
    rows=table.extract(x_tolerance=2,y_tolerance=2,layout=True); cells=table.cells
    xs=sorted(set(round(c[0],2) for c in cells)|set(round(c[2],2) for c in cells))
    ys=sorted(set(round(c[1],2) for c in cells)|set(round(c[3],2) for c in cells))
    blocks=[]
    for row,values in zip(table.rows,rows):
        cells_html=[]
        for box,value in zip(row.cells,values):
            if box is None: continue
            x0,y0,x1,y1=[round(x,2) for x in box]
            cs=xs.index(x1)-xs.index(x0); rs=ys.index(y1)-ys.index(y0)
            cells_html.append(f'<td colspan="{cs}" rowspan="{rs}"><pre>{html.escape(value or "")}</pre></td>')
        blocks.append('<tr>'+''.join(cells_html)+'</tr>')
    return '<table>'+''.join(blocks)+'</table>',rows

def extract_document(path,profile):
    pages=[]; blocks=[]; issues=[]
    with pdfplumber.open(path) as pdf:
        for pn,page in enumerate(pdf.pages,1):
            rawlines=lines_from_chars(page); images,flags=page_quality(page,rawlines,profile)
            removed=[]; kept=[]
            for line in rawlines:
                line['page']=pn; kind=footer_kind(line,page,profile)
                if kind: removed.append(dict(line,reason=kind))
                else: kept.append(line)
            tables=[]
            for idx,t in enumerate(page.find_tables()):
                # Boxes containing a running section locator are not legal tables.
                if t.bbox[0]>page.width*.65 and t.bbox[1]>page.height*.8: continue
                markup,rows=table_html(t)
                tables.append({'kind':'table','page':pn,'bbox':list(t.bbox),'html':markup,'rows':rows,'cells':[list(c) for c in t.cells]})
            if tables: issues.append({'page':pn,'condition':'table_semantics_and_cross_page_review','disposition':'unresolved','required_action':'Compare cell coordinates and fixed-spacing cell text to source; reconcile continued table headers across pages.'})
            content=[]
            for line in kept:
                x,y,r,b=line['bbox']
                if any(y>=t['bbox'][1]-.8 and b<=t['bbox'][3]+.8 and x>=t['bbox'][0]-1 and r<=t['bbox'][2]+1 for t in tables): continue
                content.append(dict(line,kind='line'))
            content.extend(tables)
            for im in images: content.append({'kind':'image','page':pn,'bbox':im['bbox'],'text':'[IMAGE]','name':im['name']})
            content.sort(key=lambda l:(l['bbox'][1],l['bbox'][0]))
            pages.append({'page':pn,'width':page.width,'height':page.height,'raw_lines':rawlines,'removed':removed,'images':images,'review_reasons':flags,'native_character_count':len(page.chars),'ocr':{'performed':False,'confidence':None,'required_review':bool(images)}})
            blocks.extend(content)
            for reason in flags: issues.append({'page':pn,'condition':reason,'disposition':'unresolved','required_action':'Render source page and review/transcribe affected content with evidence; OCR is never silently assumed complete.'})
    return pages,blocks,issues

def render_blocks(blocks):
    """Retain indent/list order and tables; join only normal wrapped prose lines."""
    parts=[]; group=[]
    def flush():
        if group:
            parts.append('<pre>'+html.escape('\n'.join(group))+'</pre>'); group.clear()
    for b in blocks:
        if b['kind']=='line':
            # Indentation is preserved from PDF positions, and page continuations stay
            # in the same pre block/record. Raw page coordinates bind every line.
            indent=max(0,round((b['bbox'][0]-54)/6))
            group.append(' '*indent+b['text'])
        elif b['kind']=='table': flush(); parts.append(b['html'])
        else: flush(); parts.append('[IMAGE]')
    flush(); return '\n'.join(parts)

def legal_heading(block,profile):
    if block['kind']!='line': return None
    match=SECTION.match(norm(block['text']))
    if match and profile=='portland' and block.get('fonts') and not any('Bold' in font for font in block['fonts']): return None
    return match

def segment(blocks,profile):
    sections=[]; current=None; expected=[]; pre=[]; article=''; first=True
    # Independent printed TOC is before first explicit Sec heading for Rockland.
    first_sec=next((i for i,b in enumerate(blocks) if legal_heading(b,profile)),None)
    if first_sec is None: return [],[],[{'condition':'zero_legal_headings','disposition':'unresolved'}]
    if profile.startswith('rockland'):
        for b in blocks[:first_sec]:
            m=TOC_ENTRY.match(norm(b.get('text','')))
            if m: expected.append({'display_number':m[1],'heading':m[2],'page':b['page'],'bbox':b['bbox']})
    # Do not treat an entire pre-first-section region as a TOC: Rockland Ch1 has
    # substantive adopting text on the next page, after its actual contents page.
    toc_pages=set(x['page'] for x in expected)
    for i,b in enumerate(blocks):
        s=norm(b.get('text','')); m=legal_heading(b,profile)
        if i<first_sec and b['page'] in toc_pages: continue
        if b['kind']=='line' and re.match(r'^ARTICLE\s+[IVXLC]+\b',s):
            article=s
            if current: sections.append(current); current=None
            pre.append(b); continue
        if m:
            if current: sections.append(current)
            if pre:
                sections.append({'number':'','name':'Substantive or editorial introductory text','citation':'','article':article,'blocks':pre,'kind':'unnumbered_body'});pre=[]
            current={'number':m[1],'name':m[2],'citation':s,'article':article,'blocks':[],'heading_locator':{'page':b['page'],'bbox':b['bbox']},'kind':'section'}
        elif current: current['blocks'].append(b)
        else: pre.append(b)
    if current: sections.append(current)
    if pre: sections.append({'number':'','name':'Unnumbered text','citation':'','article':article,'blocks':pre,'kind':'unnumbered_body'})
    # Printed TOC provides independent denominator; differing TOC/body headings are
    # retained as displayed, and reported instead of silently overwritten.
    issues=[]; actual=Counter(s['number'] for s in sections if s['number'])
    for e in expected:
        if actual[e['display_number']]!=1: issues.append({'condition':'printed_toc_body_mismatch','entry':e,'occurrences':actual[e['display_number']],'disposition':'unresolved'})
    return sections,expected,issues

def export_pair(base,records,metadata):
    writej(base.with_suffix('.json'),{'metadata':metadata,'provisions':records})
    with base.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(records)

def parse_package(args):
    package=Path(args.package); inv=readj(package/'inventory.json'); acquired=readj(package/'acquisition.json') if (package/'acquisition.json').exists() else {}
    nodes=[]; dispositions=[]; provenance=[]; exceptions=[]; allrecords=[]; bypub=defaultdict(list); doc_reports=[]
    snapshot=sha(json.dumps({'inventory':inv['inventory_sha256'],'acquired':{i:a['sha256'] for i,a in sorted(acquired.items())},'parser':sha(Path(__file__).read_bytes()),'review_file':sha(Path(args.review_file).read_bytes()) if getattr(args,'review_file',None) else None,'review_engine':sha(Path(__file__).with_name('review_pdf.py').read_bytes()) if getattr(args,'review_file',None) else None},sort_keys=True).encode())
    for doc in inv['documents']:
        ident=doc['node_id']; pub=doc['publication_id']; a=acquired.get(ident)
        node=dict(doc,node_kind='document',parent_node_id=None,source_version=snapshot)
        nodes.append(node)
        if not a:
            dispositions.append({'node_id':ident,'disposition':'unresolved','reason':'Not acquired in bounded pilot','record_ids':[]});continue
        path=package/a['raw_path']
        if sha(path.read_bytes())!=a['sha256']: raise ValueError('Raw hash mismatch: '+ident)
        profile='portland' if inv['jurisdiction_slug']=='portland-me' else ('rockland-charter' if pub=='charter' else 'rockland-code')
        pages,blocks,issues=extract_document(path,profile);review_events=[]
        if getattr(args,'review_file',None):
            from review_pdf import apply_review
            pages,blocks,issues,review_events=apply_review(args.review_file,ident,a['sha256'],pages,blocks,issues,package)
        sections,expected,segissues=segment(blocks,profile); issues+=segissues
        local=package/'layout'/ident; local.mkdir(parents=True,exist_ok=True)
        writej(local/'pages.json',pages);jsonl(local/'blocks.jsonl',blocks);writej(local/'printed-toc.json',expected)
        ids=[]
        for n,section in enumerate(sections):
            locator=section.get('heading_locator') or {'page':section['blocks'][0]['page'],'bbox':section['blocks'][0]['bbox']}
            nid=f'{ident}:p{locator["page"]}:y{locator["bbox"][1]}:n{n}'; rid=sha((inv['jurisdiction_slug']+'|'+pub+'|'+nid).encode())[:24]
            ids.append(rid)
            record={k:'' for k in FIELDS};record.update(jurisdiction=inv['jurisdiction_slug'].replace('-me',', Maine').title(),code_name='City Charter' if pub=='charter' else 'Code of Ordinances',chapter=doc['label'] if pub!='charter' else '',article=section['article'],section_number=section['number'],section_name=section['name'],citation=section['citation'],full_text=render_blocks(section['blocks']),source_url=doc['url']+'#page='+str(locator['page']),scrape_date=a['receipt']['retrieved_at'][:10])
            if not record['full_text']: issues.append({'condition':'empty_section','node_id':nid,'disposition':'unresolved'})
            if section['kind']=='unnumbered_body': issues.append({'condition':'unnumbered_body_classification_review','node_id':nid,'disposition':'unresolved'})
            nodes.append({'node_id':nid,'parent_node_id':ident,'publication_id':pub,'jurisdiction_slug':inv['jurisdiction_slug'],'node_kind':section['kind'],'display_number':section['number'],'display_heading':section['name'],'source_order':n,'raw_artifact_path':a['raw_path'],'raw_sha256':a['sha256'],'locator':locator,'source_version':snapshot,'inventory_basis':'PDF printed heading; printed TOC independently retained where present'})
            dispositions.append({'node_id':nid,'disposition':'included' if record['full_text'] else 'unresolved','record_ids':[rid]})
            provenance.append({'record_id':rid,'node_id':nid,'publication_id':pub,'source_url':record['source_url'],'raw_path':a['raw_path'],'sha256':a['sha256'],'extraction_version':VERSION,'profile':profile,'locator':locator,'content_locators':[{'page':b['page'],'bbox':b['bbox'],'kind':b['kind'],'source_fragments':b.get('source_fragments'),'review_id':b.get('review_id')} for b in section['blocks']],'notes':'Original line order/indents retained; tables use cells plus raw geometry. Review findings gate completion.'})
            bypub[pub].append(record);allrecords.append(record)
        dispositions.append({'node_id':ident,'disposition':'structural' if sections else 'unresolved','reason':'Acquired PDF; child headings and page ledger retained','record_ids':ids})
        for page in pages:
            pnid=f'{ident}:page:{page["page"]}';nodes.append({'node_id':pnid,'parent_node_id':ident,'publication_id':pub,'node_kind':'page','locator':{'page':page['page']},'raw_sha256':a['sha256'],'source_version':snapshot})
            dispositions.append({'node_id':pnid,'disposition':'unresolved' if page['review_reasons'] else 'structural','reason':','.join(page['review_reasons']) or 'Text, tables and removed running matter accounted in layout ledger','record_ids':[]})
        for issue in issues: exceptions.append(dict(issue,document_id=ident,raw_sha256=a['sha256']))
        doc_reports.append({'document_id':ident,'publication_id':pub,'profile':profile,'pages':len(pages),'records':len(sections),'printed_toc_entries':len(expected),'review_conditions':issues,'native_text_only':not any(p['images'] for p in pages),'sha256':a['sha256'],'reviewed_recoveries':review_events})
    metadata={'parser':VERSION,'snapshot_id':snapshot,'corpus_complete':False,'scope':'bounded pilot; independent document inventory includes unacquired documents','record_count':len(allrecords)}
    for pub in {d['publication_id'] for d in inv['documents']}:
        dest=package/'publications'/pub;dest.mkdir(parents=True,exist_ok=True); records=bypub[pub]
        export_pair(dest/'fulltext',records,metadata);export_pair(dest/'toc',[dict(r,full_text='') for r in records],metadata)
    export_pair(package/'aggregate-fulltext',allrecords,metadata);export_pair(package/'aggregate-toc',[dict(r,full_text='') for r in allrecords],metadata)
    jsonl(package/'source-nodes.jsonl',nodes);jsonl(package/'node-dispositions.jsonl',dispositions);jsonl(package/'record-provenance.jsonl',provenance);jsonl(package/'exceptions.jsonl',exceptions)
    report={'status':'bounded_pilot_requires_review','corpus_complete':False,'inventory_documents':len(inv['documents']),'acquired_documents':len(acquired),'unacquired_documents':len(inv['documents'])-len(acquired),'record_count':len(allrecords),'source_node_count':len(nodes),'disposition_count':len(dispositions),'documents':doc_reports,'unresolved_exception_count':len(exceptions),'snapshot_id':snapshot,'limits':['Full jurisdiction collection was not run.','Heading and page ledger are not an independently verified full legal-node inventory.','OCR is not performed; mixed/image pages remain unresolved.','Table fragments crossing pages require source review before a corpus can be accepted.','Unnumbered introductory text is retained and requires operative/editorial classification.','No global legal current-through date was inferred.']}
    writej(package/'validation-report.json',report)
    artifacts={str(p.relative_to(package)):sha(p.read_bytes()) for p in sorted(package.rglob('*')) if p.is_file() and p.name!='run-manifest.json'}
    writej(package/'run-manifest.json',dict(metadata,jurisdiction_slug=inv['jurisdiction_slug'],configuration_sha256=sha(json.dumps(inv,sort_keys=True).encode()),artifact_hashes=artifacts,completion_status=report['status'],document_inventory_count=len(inv['documents']),downloaded_document_count=len(acquired),parser_sha256=sha(Path(__file__).read_bytes())))
    print(json.dumps({k:report[k] for k in ['status','record_count','inventory_documents','acquired_documents','unresolved_exception_count']}))

def verify_package(args):
    package=Path(args.package); manifest=readj(package/'run-manifest.json'); errors=[]
    for rel,digest in manifest['artifact_hashes'].items():
        p=package/rel
        if not p.exists() or sha(p.read_bytes())!=digest: errors.append('hash:'+rel)
    for p in package.rglob('fulltext.json'):
        rows=readj(p)['provisions']
        with p.with_suffix('.csv').open(encoding='utf-8-sig',newline='') as f:
            if list(csv.DictReader(f))!=rows: errors.append('csv/json:'+str(p))
    rows=readj(package/'aggregate-fulltext.json')['provisions']
    with (package/'aggregate-fulltext.csv').open(encoding='utf-8-sig',newline='') as f:
        if list(csv.DictReader(f))!=rows: errors.append('aggregate csv/json')
    nodes=[json.loads(x) for x in (package/'source-nodes.jsonl').read_text().splitlines()]; disp=[json.loads(x) for x in (package/'node-dispositions.jsonl').read_text().splitlines()]
    if Counter(x['node_id'] for x in nodes)!=Counter(x['node_id'] for x in disp) or any(n!=1 for n in Counter(x['node_id'] for x in disp).values()): errors.append('source node disposition mismatch')
    prov=[json.loads(x) for x in (package/'record-provenance.jsonl').read_text().splitlines()]
    if len(prov)!=len(rows) or len({p['record_id'] for p in prov})!=len(prov): errors.append('record identity/provenance count')
    print(json.dumps({'integrity_passed':not errors,'errors':errors,'corpus_complete':False,'status':'bounded pilot, manual review outstanding'}))
    return 1 if errors else 0

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    d=sub.add_parser('discover');d.add_argument('--jurisdiction',choices=ROOTS,required=True);d.add_argument('--out',required=True);d.add_argument('--index-html');d.add_argument('--rendered-html');d.add_argument('--base-url');d.add_argument('--transport',default='operator_retained_html');d.add_argument('--retrieved-at');d.set_defaults(func=discover)
    a=sub.add_parser('acquire');a.add_argument('--package',required=True);a.add_argument('--id',action='append');a.add_argument('--all',action='store_true');a.set_defaults(func=acquire)
    i=sub.add_parser('import-browser-pdf');i.add_argument('--package',required=True);i.add_argument('--id',required=True);i.add_argument('--file',required=True);i.add_argument('--retrieved-at',required=True);i.add_argument('--note',required=True);i.set_defaults(func=import_pdf)
    for cmd,func in [('parse',parse_package),('verify',verify_package)]:
        a=sub.add_parser(cmd);a.add_argument('--package',required=True);a.add_argument('--review-file');a.set_defaults(func=func)
    args=p.parse_args()
    try: return args.func(args) or 0
    except Exception as e: print(json.dumps({'status':'blocked','error':str(e)}),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
