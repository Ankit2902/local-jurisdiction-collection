"""Pure offline package primitives. No collector imports or network/image APIs."""
from __future__ import annotations
import csv, hashlib, io, json, os, re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote,urlsplit

VERSION='corpus-package-1'
FIELDS='jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()

def require(ok,message):
    if not ok: raise ValueError(message)
def sha(data): return hashlib.sha256(data).hexdigest()
def encoded(value): return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def canonical(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def jsonl(rows): return b''.join(canonical(r)+b'\n' for r in rows)
def safe(root,name):
    p=PurePosixPath(name)
    require(isinstance(name,str) and name and not p.is_absolute() and '..' not in p.parts and str(p)==name and '\\' not in name,'Unsafe artifact path')
    root=Path(root).resolve();path=root/name
    require(not path.is_symlink() and all(not x.is_symlink() for x in path.parents if x!=root.parent),'Symlinks forbidden')
    require(path.resolve().is_relative_to(root),'Escaping artifact path')
    return path
def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
def files(root):
    root=Path(root)
    require(not root.is_symlink(),'Symlink root forbidden')
    result={}
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(),'Symlink input forbidden')
        if p.is_file(): result[p.relative_to(root).as_posix()]=file_hash(p)
    return result
def checked_write(path,data):
    path=Path(path)
    if path.exists():
        require(path.is_file() and path.read_bytes()==data,'Existing artifact differs; no overwrite: '+str(path))
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.package-tmp')
    require(not temp.exists(),'Interrupted temporary file requires operator review')
    with temp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(temp,path)
def state_write(path,value):
    path=Path(path);tmp=path.with_name(path.name+'.state-tmp')
    require(not tmp.exists(),'Interrupted state temporary requires operator review')
    with tmp.open('xb') as f:f.write(encoded(value));f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
def csv_bytes(rows):
    buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=FIELDS,extrasaction='raise')
    writer.writeheader();writer.writerows(rows)
    return buf.getvalue().encode('utf-8-sig')

class InertHTML(HTMLParser):
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        require(tag not in {'img','picture','svg','image','script','style'},'Active image/script markup in canonical HTML')
        require(not any(k in attrs for k in ['background','poster','srcset']),'Active image attribute in canonical HTML')
        require(not re.search(r'\burl\s*\(',attrs.get('style',''),re.I),'Active image CSS in canonical HTML')
        require(not attrs.get('type','').lower().startswith('image/'),'Active image MIME in canonical HTML')
        require(not (tag=='input' and attrs.get('type','').strip().lower()=='image'),'Active image input in canonical HTML')
        for key in ['src','data','href','xlink:href']:
            value=attrs.get(key,'')
            path=unquote(urlsplit(value).path) if value else ''
            require(not re.search(r'\.(?:png|jpe?g|gif|svg|webp|avif|bmp|tiff?|ico)(?:$)',path,re.I),'Active known image URL in canonical HTML')
        require(not any('data:image/' in str(v).lower() for v in attrs.values()),'Image payload in canonical metadata')
        if tag in {'object','embed','source','input'}:
            require(not any(str(attrs.get(k,'')).lower().startswith('data:') for k in ['src','data']),'Opaque embedded image/document must be qualified before export')
    handle_startendtag=handle_starttag
    def handle_data(self,data):require('data:image/' not in data.lower(),'Image payload in canonical text')
def check_html(html):
    require(isinstance(html,str),'Canonical HTML must be text')
    parser=InertHTML(convert_charrefs=True);parser.feed(html);parser.close()

def check_metadata(value,image_context=False):
    """Refuse unsafe projected payloads; never strip or decode legal prose.

    Immutable input evidence is deliberately outside this normalized-output guard.
    Image URL references may remain as references, but data payloads never do.
    """
    if isinstance(value,dict):
        typed=any(str(value.get(k,'')).lower().startswith('image/') or str(value.get(k,'')).lower() in ['image','img','picture','svg'] for k in ['type','mime','media_type','content_type','tag','kind'])
        for key,item in value.items():
            check_metadata(str(key));check_metadata(item,image_context or typed or 'image' in str(key).lower())
    elif isinstance(value,(list,tuple)):
        for item in value:check_metadata(item,image_context)
    elif isinstance(value,str):
        require(not re.search(r'data\s*:\s*image/',value,re.I),'Image payload in normalized metadata/text')
        require(not (image_context and re.search(r'\bdata\s*:',value,re.I)),'Opaque data payload in known image metadata')
        if '<' in value:check_html(value)

@dataclass
class Projection:
    """Reader ABI. Writers never infer legal hierarchy or concatenate diagnostics.

    rows have exactly FIELDS; sidecars preserve source identity and structure.
    inherited_coverage is original JSON, never strengthened by serialization.
    """
    publication_id:str
    rows:list
    publications:list
    nodes:list
    dispositions:list
    provenance:list
    exceptions:list
    metadata:dict
    inherited_coverage:dict

def validate_projection(p):
    require(p.rows and len(p.provenance)==len(p.rows),'Empty or unbound corpus rows')
    ids=[x['record_id'] for x in p.provenance]
    require(len(ids)==len(set(ids)),'Duplicate stable output record IDs')
    nodeids=[x['node_id'] for x in p.nodes];disp=[x['node_id'] for x in p.dispositions]
    require(len(nodeids)==len(set(nodeids)) and len(disp)==len(set(disp)) and set(nodeids)==set(disp),'Missing/duplicate source disposition')
    for i,(row,proof) in enumerate(zip(p.rows,p.provenance)):
        require(list(row)==FIELDS and all(isinstance(v,str) for v in row.values()),'Invalid16-field corpus row')
        require(proof['row_ordinal']==i and proof['corpus_row_sha256']==sha(canonical(row)),'Wrong row provenance binding')
        require(proof['publication_id']==p.publication_id and proof['node_ids'] and set(proof['node_ids'])<=set(nodeids),'Foreign or missing source node binding')
        check_html(row['full_text'])
        check_metadata({k:v for k,v in row.items() if k!='full_text'})
    represented=set()
    for d in p.dispositions:
        require(d['disposition'] in ['included','structural','reserved_or_repealed','editorial_reference','excluded_by_scope','unresolved'],'Unknown source disposition')
        require(set(d['record_ids'])<=set(ids),'Disposition maps unknown output')
        represented.update(d['record_ids'])
    require(represented==set(ids),'Output lacks source disposition')

def artifacts(p):
    validate_projection(p)
    for value in [p.metadata,p.publications,p.nodes,p.dispositions,p.provenance,p.exceptions,p.inherited_coverage]:check_metadata(value)
    meta=dict(p.metadata,packager_version=VERSION,publication_id=p.publication_id,record_count=len(p.rows),full_text_representation='Canonical image-free semantic HTML from verified source IR; diagnostics never concatenated')
    toc=[dict(r,full_text='') for r in p.rows];out={}
    for folder,stem,rows in [('', 'aggregate-fulltext',p.rows),('', 'aggregate-toc',toc),('publications/'+p.publication_id+'/', 'fulltext',p.rows),('publications/'+p.publication_id+'/', 'toc',toc)]:
        out[folder+stem+'.json']=encoded({'metadata':meta,'provisions':rows});out[folder+stem+'.csv']=csv_bytes(rows)
    for name,rows in [('source-nodes',p.nodes),('node-dispositions',p.dispositions),('record-provenance',p.provenance),('exceptions',p.exceptions)]:out[name+'.jsonl']=jsonl(rows)
    out['publications.json']=encoded(p.publications)
    out['inherited-coverage.json']=encoded(p.inherited_coverage)
    # Serialization passes neither acquisition nor independent legal qualification.
    gates=['publication_accepted','complete','whole_jurisdiction_complete','external_adopted_legal_dependency_closure_complete','independent_final_review_complete']
    ready=all(p.inherited_coverage.get(g) is True for g in gates) and not any(d['disposition']=='unresolved' for d in p.dispositions)
    out['validation-report.json']=encoded({'schema_version':1,'serialization_complete':True,'source_verification_mode':'Hash-bound preexisting read-only raw-replay proof; source parser not rerun by packager','source_coverage_unchanged':True,'inherited_gate_values':{g:p.inherited_coverage.get(g) for g in gates},'downstream_ready':ready,'complete':ready,'status':'complete' if ready else 'incomplete','source_node_count':len(p.nodes),'record_count':len(p.rows),'exception_count':len(p.exceptions),'independent_source_inventory_is_not_derived_toc':True,'image_policy':'No image acquisition/decoding/extraction/render/OCR; exact [IMAGE] preserved','automated_checks':['input proof/source/code hash bindings','all16field values and JSON/CSV/TOC equality','one disposition per source node','canonical source row/record provenance','image-free normalized HTML'],'human_source_comparisons_performed_by_packager':0})
    return out
