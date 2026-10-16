"""Portable source retention, semantic serialization, and bounded sample exports."""
from __future__ import annotations
import csv, hashlib, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag, Comment
import requests

FIELDS = 'jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()
VERSION = 'bulk-official-html-1'
def sha(data): return hashlib.sha256(data).hexdigest()
def clean(s): return re.sub(r'\s+', ' ', str(s).replace('\xa0',' ')).strip()
def dump(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(path)
def jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')

def acquire(url, path, timeout=30, headers=None):
    """Ordinary verified HTTPS; no access bypass, bounded transient retries."""
    path=Path(path); meta=path.with_suffix(path.suffix+'.http.json')
    if path.exists():
        old=json.loads(meta.read_text())
        if old['url']!=url or old['sha256']!=sha(path.read_bytes()): raise ValueError('cache binding/hash mismatch')
        return old
    for attempt in range(3):
        r=requests.get(url,timeout=(8,timeout),headers=dict({'User-Agent':'CompliSolv source validation/1.0'},**(headers or {})))
        if r.status_code not in (429,503): break
        if attempt<2: time.sleep(min(5,2**attempt))
    r.raise_for_status();path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(r.content)
    result={'url':url,'final_url':r.url,'status':r.status_code,'retrieved_at':datetime.now(timezone.utc).isoformat(),'headers':dict(r.headers),'redirect_chain':[x.url for x in r.history],'sha256':sha(r.content),'bytes':len(r.content)}
    dump(meta,result);return result

def decode(data, content_type=''):
    """Prefer BOM/strict UTF-8; honor declarations, map HTML latin1 to cp1252."""
    if data.startswith(b'\xef\xbb\xbf'): encoding='utf-8-sig'
    else:
        try:
            text=data.decode('utf-8',errors='strict')
            if '\ufffd' in text or re.search('[\x80-\x9f]',text): raise ValueError('unresolved decoding defect')
            return text,'utf-8'
        except UnicodeDecodeError:
            pass
        declared=re.search(br'charset\s*=\s*[\"\']?([\w-]+)',data[:4096],re.I)
        header=re.search(r'charset=([\w-]+)',content_type,re.I)
        encoding=declared.group(1).decode() if declared else (header.group(1) if header else '')
        if encoding.lower() in ('iso-8859-1','latin1','windows-1252'): encoding='cp1252'
        if not encoding:
            try: data.decode('utf-8');encoding='utf-8'
            except UnicodeDecodeError: encoding='cp1252'
    text=data.decode(encoding,errors='strict')
    if '\ufffd' in text or re.search('[\x80-\x9f]',text): raise ValueError('unresolved decoding defect')
    return text,encoding

KEEP={'p','div','br','ul','ol','li','table','thead','tbody','tfoot','tr','td','th','caption','sup','sub','a','b','strong','i','em','u','blockquote','pre','h1','h2','h3','h4','span','dl','dt','dd'}
ATTRS={'id','name','href','src','alt','rowspan','colspan','start','value','type'}
def semantic(node):
    """Retain semantic relationships once; scripts/styles/navigation excluded."""
    if isinstance(node,Comment): return ''
    if isinstance(node,NavigableString):
        from html import escape
        return escape(re.sub(r'\s+',' ',str(node)))
    if not isinstance(node,Tag): return ''
    if node.name in {'script','style','nav','noscript'}: return ''
    if node.name=='img':
        from html import escape
        return '<span data-image-src="'+escape(node.get('src',''),quote=True)+'">[IMAGE]</span>'
    inner=''.join(semantic(c) for c in node.children)
    if node.name not in KEEP: return inner
    from html import escape
    attrs=''.join(' '+k+'="'+escape(str(v),quote=True)+'"' for k,v in node.attrs.items() if k in ATTRS)
    if node.name=='br':return '<br/>'
    return '<'+node.name+attrs+'>'+inner+'</'+node.name+'>'

def readable(html):
    """Plain paragraphs/list levels; tables stay semantic HTML to preserve spans."""
    soup=BeautifulSoup(html,'html.parser')
    def render(n,depth=0):
        if isinstance(n,NavigableString):return str(n)
        if not isinstance(n,Tag):return ''
        if n.name=='table':return '\n'+str(n)+'\n'
        if n.name=='br':return '\n'
        if n.name in ('sup','sub'):return '<'+n.name+'>'+''.join(render(x,depth) for x in n.children)+'</'+n.name+'>'
        content=''.join(render(x,depth+(n.name in ('ul','ol'))) for x in n.children)
        if n.name=='li':return '\n'+'  '*max(0,depth-1)+'• '+content.strip()+'\n'
        if n.name in ('p','div','blockquote','h1','h2','h3','h4','dt','dd'):return '\n'+content.strip()+'\n'
        return content
    text=''.join(render(n) for n in soup.contents)
    return re.sub(r'\n[ \t]*\n+', '\n\n',text).strip()

def record(**values):
    row=dict.fromkeys(FIELDS,''); row.update(values);return row

def package(out, jurisdiction, publication, rows, nodes, dispositions, provenance, version, raw_paths):
    """Export a bounded sample, explicitly never a completed jurisdiction corpus."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True);pub=out/'publications'/publication;pub.mkdir(parents=True,exist_ok=True)
    retained={}
    raw_entries=[]
    for source in raw_paths:
        source=Path(source);data=source.read_bytes();digest=sha(data)
        target=out/'raw'/(digest[:16]+'_'+source.name);target.parent.mkdir(exist_ok=True)
        if target.exists() and target.read_bytes()!=data:raise ValueError('raw hash/name collision')
        target.write_bytes(data);rel=str(target.relative_to(out));retained[digest]=rel;raw_entries.append({'path':rel,'sha256':digest})
    nodes=[dict(n,raw_artifact_path=retained.get(n.get('raw_sha256'),n.get('raw_artifact_path',''))) for n in nodes]
    ids=[n['node_id'] for n in nodes]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate source node identity')
    if sorted(ids)!=sorted(d['node_id'] for d in dispositions):raise ValueError('node disposition mismatch')
    def exports(dest,stem,items):
        dump(dest/(stem+'.json'),{'metadata':{'scope':'bounded_validation_sample','source_version':version,'record_count':len(items)},'provisions':items})
        with (dest/(stem+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(items)
        with (dest/(stem+'.csv')).open(encoding='utf-8-sig',newline='') as f:assert list(csv.DictReader(f))==items
    toc=[dict(r,full_text='') for r in rows]
    exports(pub,'fulltext',rows);exports(pub,'toc',toc);exports(out,'aggregate-fulltext',rows);exports(out,'aggregate-toc',toc)
    jsonl(out/'source-nodes.jsonl',nodes);jsonl(out/'node-dispositions.jsonl',dispositions);jsonl(out/'record-provenance.jsonl',provenance)
    jsonl(out/'exceptions.jsonl',[])
    dump(out/'publications.json',[{'publication_id':publication,'scope':'sample_only','source_version':version}])
    dump(out/'run-manifest.json',{'jurisdiction':jurisdiction,'parser_version':VERSION,'scope':'bounded_validation_sample','complete':False,'source_version':version,'records':len(rows),'nodes':len(nodes),'raw_artifacts':raw_entries})
    return {'records':len(rows),'nodes':len(nodes),'csv_json_equal':True}

def checkpoint(path, binding, completed):
    """Bind resumable work to complete version/config/parser/raw identities."""
    path=Path(path)
    if path.exists() and json.loads(path.read_text())['binding']!=binding:raise ValueError('checkpoint version/config mismatch')
    dump(path,{'binding':binding,'completed':completed})

def resume_units(units, path, binding, stop_after=None):
    """Replay explicit bounded units; completed outputs are persisted atomically."""
    path=Path(path);completed={}
    if path.exists():
        saved=json.loads(path.read_text())
        if saved['binding']!=binding:raise ValueError('checkpoint version/config mismatch')
        completed=saved['completed']
    for index,(identity,parse) in enumerate(units):
        if identity not in completed:
            completed[identity]=parse();dump(path,{'binding':binding,'completed':completed})
        if stop_after is not None and index+1>=stop_after:raise InterruptedError('simulated bounded interruption')
    if set(completed)!=set(identity for identity,_ in units):raise ValueError('stale checkpoint unit membership')
    return [completed[identity] for identity,_ in units]
