"""Offline source-owned reader helpers; no collector, browser or PDF imports."""
import json
from datetime import datetime,timezone
from common import *

HIERARCHY={'division':'division','title':'title','subtitle':'subtitle','chapter':'chapter','subchapter':'subchapter','article':'article','part':'part','subpart':'subpart'}
def lines(path):
    # Literal U+0085/U+2028/U+2029 inside source text are not JSONL delimiters.
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').split('\n') if x]
def envelope(root,proof,family,mode):
    require(proof.get('schema')=='offline-family-readonly-proof-1' and proof.get('family')==mode,'Unsupported verification adapter/mode')
    require(proof.get('evidence_read_only') is True and proof.get('publisher_requests')==0 and proof.get('source_changed_during_run') is False and proof.get('runtime_changed_during_run') is False,'Unbound read-only source proof')
    require(proof.get('evidence_sha256_before')==proof.get('evidence_sha256_after') and proof.get('evidence_sha256_before'),'Changed/unbound evidence')
    require(proof.get('collector_sources_before')==proof.get('collector_sources_after') and proof.get('collector_sources_before'),'Changed/unbound historical parser')
    require(proof['verification']['family_report_sha256']==sha(encoded(family)),'Wrong family verification payload')
    require(not proof['verification'].get('forbidden_calls'),'Verification used forbidden source/image operation')
    return Path(root)
def raw(root,path,expected):
    p=safe(root,path);require(file_hash(p)==expected,'Corrupt raw source '+path);return p

def literal_components(chain,heading,numbered_leaf=False):
    """Only explicit printed hierarchy names, on independently owned source ancestors.

    Numeric section captions are admitted only when their literal prefix is within
    the exact explicitly printed Chapter prefix on this source parent chain.
    No numeric-depth or node-ID hierarchy inference occurs.
    """
    result={x:'' for x in HIERARCHY};evidence=[];conflicts=[];groups={k:[] for k in HIERARCHY}
    for n in chain:
        label=n['heading'].strip();token,sep,rest=label.partition(' ');kind=HIERARCHY.get(token.lower().rstrip('.'))
        if kind and sep and rest:
            groups[kind].append((n,label));evidence.append({'field':kind,'node_id':n['id'],'source_heading':n['heading'],'rule':'Explicit printed hierarchy-unit name on source-proven ancestry'})
    for field,values in groups.items():
        unique=list(dict.fromkeys(v for _,v in values))
        if len(unique)==1:result[field]=unique[0]
        elif len(unique)>1:conflicts.append({'field':field,'source_values':unique,'disposition':'Cannot flatten repeated same-type ancestry into one authoritative scalar; full chain retained'})
    current=heading.strip();token,sep,rest=current.partition(' ');number='';name=current;basis=None
    if token.lower() in ['sec.','section','section.'] and sep:
        candidate,gap,suffix=rest.partition(' ')
        if any(x.isdigit() for x in candidate) and all(x.isalnum() or x in '.-()' for x in candidate):number=candidate;name=suffix;basis='Literal explicitly labelled source section component'
    elif numbered_leaf:
        candidate,gap,suffix=current.partition(' ')
        chapters=groups['chapter']
        if len(chapters)==1 and gap:
            chapter_number=chapters[0][1].split(' ',2)[1].rstrip('.')
            if candidate.startswith(chapter_number+'.') and any(x.isdigit() for x in candidate) and all(x.isalnum() or x in '.-' for x in candidate):number=candidate;name=suffix;basis='Literal numeric source heading component within exact explicitly named Chapter ancestry; no generated citation'
    if number:
        if name.startswith('- '):name=name[2:]
        evidence.append({'field':'section_number','source_heading':heading,'value':number,'rule':basis})
    return result,number,name,evidence,conflicts

def acquired_date(value):
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        require(value>0,"Invalid source acquisition epoch")
        return datetime.fromtimestamp(value,timezone.utc).isoformat()
    require(isinstance(value,str) and value,"Missing exact source acquisition timestamp")
    return value

def corpus_row(jurisdiction,code,chain,heading,html,url,date,numbered_leaf=False):
    check_html(html)
    row={f:'' for f in FIELDS};parts,number,name,evidence,conflicts=literal_components(chain,heading,numbered_leaf)
    row.update(parts);row.update(jurisdiction=jurisdiction,code_name=code,section_number=number,section_name=name,citation=heading,full_text=html,source_url=url,scrape_date=acquired_date(date))
    return row,evidence,conflicts

def finish(publication_id,rows,pubs,nodes,dispositions,provenance,exceptions,metadata,coverage):
    for i,(row,pr) in enumerate(zip(rows,provenance)):
        pr.update(publication_id=publication_id,row_ordinal=i,corpus_row_sha256=sha(canonical(row)))
    return Projection(publication_id,rows,pubs,nodes,dispositions,provenance,exceptions,metadata,coverage)
