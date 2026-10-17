#!/usr/bin/env python3
"""Build exact publisher type strategy overrides from bundled observed source; no network."""
import json,re,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    pubs=json.loads((HERE/'publications.json').read_text())['publications'];overrides={}
    with zipfile.ZipFile(HERE/'source-evidence.zip') as z:
        books={}
        for name in z.namelist():
            if not name.endswith('/overview.html') or '/american-legal/' not in name:continue
            m=re.search(r'window\._redux_state\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")',z.read(name).decode())
            if not m:continue
            for b in json.loads(json.loads(m[1]))['codes']['selectedVersion']['toc']:
                books[(b['client_slug'],b['slug'])]=(b,name)
        for pub in pubs:
            if pub['publisher']!='american-legal':continue
            client=pub['source_url'].split('/codes/')[1].split('/')[0];slug=pub.get('selector',{}).get('publication')
            alias=None
            if not slug:
                matches=[(key,value) for key,value in books.items() if key[0]==client and value[0]['title']==pub['title']]
                if len(matches)!=1:continue
                (client,slug),(b,name)=matches[0]
                canonical=[x for x in pubs if x['id']!=pub['id'] and x['publisher']=='american-legal' and x.get('selector',{}).get('publication')==slug and '/codes/'+client+'/' in x['source_url']]
                if len(canonical)!=1:continue
                alias=canonical[0]['id']
            b,name=books[(client,slug)]
            overrides[pub['id']]={'acquisition_strategy':'traverse' if b['is_pdf'] else 'native','observed_is_pdf':b['is_pdf'],'strategy_evidence':{'bundle':'source-evidence.zip','member':name,'client_slug':client,'publication_slug':slug}}
            if alias:overrides[pub['id']].update(runnable=True,unsupported_reason=None,selector={'publication':slug},configuration_alias_of=alias,scope_kind='publication',qualification_note='Retained overview has one exact title match to the separately configured publication; this discovery route is an alias, not another independent book')
    additional=HERE/'readiness-additional-publications.json'
    if additional.exists():
        for pub in json.loads(additional.read_text())['publications']:
            parent=pub.get('discovered_as_required_dependency_of')
            if parent:overrides.setdefault(parent,{})['required_publication_dependencies']=[pub['id']]
    for pub in pubs:
        if pub['id'] in ('82-cfe47a936088','82-7a796760f2f3','82-8fbdce15716d','82-301463c368c5','82-02572b382672'):
            overrides.setdefault(pub['id'],{}).update(required_for_jurisdiction=False,edition_scope='historical_explicit_publisher_date_label',scope_note='Retained historical publication candidate. Publisher title explicitly ends before2026-10-17; current requiredSTO/UPOC effective2026-10-02 stayseparate.')
    out={'schema_version':1,'note':'Explicit source-backed runtime overrides; frozen base registry evidence is unchanged','publications':overrides}
    (HERE/'readiness-overrides.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
