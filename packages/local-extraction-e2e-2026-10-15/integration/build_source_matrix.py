#!/usr/bin/env python3
"""Reconcile the30-row planning inventory with final bounded live reports."""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(path): return json.loads((ROOT / path).read_text())
def main():
    old = read('SOURCE-MATRIX.json')
    ec = {x['slug']: x for x in read('ecode360/E2E-VALIDATION.json')['jurisdictions']}
    cp = {x['jurisdiction_slug']: x for x in read('codepublishing/E2E-VALIDATION.json')['results']}
    mc = {x['slug']: x for x in read('municipal-codes/E2E-VALIDATION.json')['cities']}
    rows = []
    for previous in old['jurisdictions']:
        r = {k: previous[k] for k in ['slug','jurisdiction','state','baseline_source_type','baseline_url','current_source_type','current_source_url']}
        slug = r['slug']; kind = r['current_source_type']
        r.update(e2e_status='bounded_live_acquisition_parse_export_pass', full_collection_verified=False, release_eligible=False)
        if kind == 'ecode360':
            x=ec[slug];package='ecode360';r.update(validated_records=x['record_count'], tested_source_url=x['discovery_url'], runtime_status={'cua':'pass','direct_http':x['standalone_http_status'],'standalone_browser':x['standalone_browser_status']}, qualified_method='CUA script → exact DOM source → importer → parser → verified JSON/CSV', validation_summary=f"Current chapter sample: {x['record_count']} records; requested identity, retained source hashes and all source-text comparisons pass.", source_receipt=package+'/'+x['latest_success_receipt'], output_directory=package+'/'+x['current_output_directory'], source_version=x['supported_cua']['source_version_before'], official_route_currentness=x['official_route_currentness'], remaining_gate='Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.')
            if slug=='foster-city-ca':r['remaining_gate']+=' Separately resolve Estero Municipal Improvement District Code scope.'
        elif kind == 'codepublishing':
            x=cp[slug];package='codepublishing';r.update(validated_records=x['records'], runtime_status={'cua':'pass','standalone_browser':'blocked_http_403'}, qualified_method='CUA script → resolved chapter/frame DOM → acquisition CLI → clean/resumed parser exports', validation_summary=f"{x['records']} current records; source currency equal before/after; clean/resumed exports and CSV/JSON agree.", source_version=x['source_currency'], source_receipts=[package+'/'+p for p in x['source_receipts']], observed_publication_links=x.get('root_inventory_links',[]), remaining_gate='Complete publication/family inventory and whole-corpus version coherence; standalone transport blocked; broader images/spans/incorporated PDFs.')
        elif kind == 'municipal_codes':
            x=mc[slug];package='municipal-codes';r.update(validated_records=x['export_records'], runtime_status={'cua':'pass','direct_http':x['direct_http']['status'],'standalone_browser':x['standalone_browser']['status']}, qualified_method='CUA script → Contents and chapter DOM → stable section-card parser → verified exports', validation_summary=f"{x['inventory_nodes']:,} primary navigation nodes; {x['export_records']} current records including difficult samples; primary inventory, displayed currency and chapter bodies equal before/after.", observed_inventory_nodes=x['inventory_nodes'], source_version=x['currency_before'], extra_publication_families=x['extra_families'], output_directory=package+'/'+x['exports_path'], remaining_gate='; '.join(x['remaining_gates']))
        elif kind == 'gridics':
            package='gridics';r.update(validated_records=59, runtime_status={'cua':'pass','standalone_browser':'pass'}, qualified_method='Standalone Playwright or CUA → UUID DOM → resumable parser → verified exports', validation_summary='Three standalone routes HTTP200; intentional acquisition resume;65 Title1 source fingerprints equal CUA;59 records/66 rendered nodes;2,687 observed navigation identities;2,621 bodies unresolved.', observed_inventory_nodes=2687, remaining_gate='Legal current-through unknown; no independent publisher total or exhaustive route validity.35 compound/descendant routes unqualified;2,621 bodies unacquired. Full observed tree expansion does not mean complete legal corpus.')
        elif kind == 'civicplus_pdf':
            package='civicplus';portland=slug=='portland-me';r.update(validated_records=13 if portland else 92, runtime_status=({'cua':'pass','standalone_browser':'pass','direct_http':'PDF pass; index certificate-chain failure'} if portland else {'direct_http':'pass','cua':'not_needed_for_qualified_HTTP_path','standalone_browser':'not_needed_for_qualified_HTTP_path'}), qualified_method=('Verified Chrome/CUA index → HTTP PDF → parser → integrity verification' if portland else 'HTTP official index → PDF bytes → parser → integrity verification'), validation_summary=('44 labelled assets;13 Chapter13 records; standalone/CUA ordered provisions equal; source-bound table and line recoveries.' if portland else '21-document index; fresh Chapter1 and Charter PDFs;92 records; start/end inventory coherent.'), observed_inventory_documents=44 if portland else 21, semantic_complete=False, unresolved_exceptions=10 if portland else 28, remaining_gate=('Unreadable symbol, other PDF tables/layouts and unacquired documents; integrity PASS does not establish semantic completeness.' if portland else 'Obscured Charter text, microscopic markers, unnumbered-body classification and unacquired chapters; integrity PASS does not establish semantic completeness.'))
        else:
            package='bulk-and-official-html'
            if kind=='openlaw_xml':
                r.update(validated_records=135,runtime_status={'direct_http_archive':'pass','cua':'not_needed','standalone_browser':'not_needed'},qualified_method='Resolve repository HEAD → pinned archive → Git blob verification → bounded actual XInclude traversal → XML parser',validation_summary='All291 archive Git blobs verified;96 Charter +39 Title1 records.',remaining_gate='Only declared XML include subset parsed; mixed own-body/include files deliberately rejected; commit reproducibility does not establish legal currency.')
            elif kind=='municode':
                r.update(validated_records=3,runtime_status={'direct_api':'pass','standalone_browser':'adoption-body parity pass','cua':'official-route and adoption-body parity pass'},qualified_method='Live client/publication API discovery → TOC →3 exact content requests → parser; CUA and standalone adoption-body comparison',validation_summary='2,506-node TOC;3 provisions including table and appendix; publication/tree stable before/after; adoption body equals both browser runtimes.',observed_inventory_nodes=2506,remaining_gate='Full-node acquisition/reconciliation; rendered parity for table/appendix samples; uncodified ordinances separately inventoried; whole-publication acceptance.')
            else:
                r.update(validated_records=261,runtime_status={'direct_http':'pass after CUA discovery capture','cua':'official landing discovery pass','standalone_browser':'full discovery not qualified'},qualified_method='Fresh CUA landing discovery → standalone HTTP original HTML/Word bytes →3 document parser runs',validation_summary='121 Title1 +20 Title2A +120 Charter records. Original CP1252 bytes preserved; Word corroborates source numbering/date discrepancies.',remaining_gate='Resolve publisher numbering/date conflicts; Title21A issues and broader Word/HTML paragraph parity remain; full discovery is hybrid CUA+HTTP, not wholly unattended.')
        r['assigned_package']=package;r['package_readme']=package+'/README.md';r['validation_report']=package+'/E2E-VALIDATION.json'
        if package=='bulk-and-official-html':r['jurisdiction_report']=package+'/live/final-'+slug.rsplit('-',1)[0]+'/E2E-VALIDATION.json'
        if slug in {'foster-city-ca','seatac-wa','daly-city-ca'}:r['migration_note']='Original registry source superseded by current publisher; use current source and package above.'
        rows.append(r)
    assert len(rows)==30 and len({r['slug'] for r in rows})==30
    counts=dict(collections.Counter(r['current_source_type'] for r in rows))
    assert counts['ecode360']==14 and counts['codepublishing']==5
    result={'as_of':'2026-10-15','basis':'30 outstanding jurisdictions in reviewed project handoff inventory; no current database audit. Live method qualification does not remove a jurisdiction from the collection backlog.','status':'bounded_live_methods_validated_for_all30','current_source_counts':counts,'full_collections_completed_by_this_task':0,'jurisdictions':rows}
    (ROOT/'SOURCE-MATRIX.json').write_text(json.dumps(result,indent=2)+'\n')
    text=['# Current source and validation matrix — October15,2026','',result['basis'],'','All30 have a bounded live acquisition → parser → export path. None is a completed jurisdiction corpus. Runtime results below apply to observed samples and environments, not a guarantee of future access.','', '| Jurisdiction | Current source | Tested records | Qualified path | Evidence |','|---|---|---:|---|---|']
    for r in sorted(rows,key=lambda x:(x['current_source_type'],x['jurisdiction'])):
        text.append(f"| {r['jurisdiction']} ({r['state']}) | [{r['current_source_type']}]({r['current_source_url']}) | {r['validated_records']} | {r['qualified_method']} | [Report]({r['validation_report']}) |")
    for r in sorted(rows,key=lambda x:x['jurisdiction']):
        text+=['',f"## {r['jurisdiction']} ({r['state']})",'',r['validation_summary'],'','**Runtime status:** '+ '; '.join(k.replace('_',' ')+': '+v for k,v in r['runtime_status'].items())+'.','', '**Remaining:** '+r['remaining_gate'],'',f"[Runnable package]({r['package_readme']}) · [Evidence report]({r['validation_report']})"]
        if r.get('tested_source_url'):text+=['',f"[Exact tested source]({r['tested_source_url']})"]
        if r.get('migration_note'):text+=['',r['migration_note']]
        if r.get('source_version'):text+=['','**Observed source marker:** '+(r['source_version'] if isinstance(r['source_version'],str) else json.dumps(r['source_version']))]
        if r.get('extra_publication_families'):
            text+=['','Additional observed publication families (scope unresolved):']
            for f in r['extra_publication_families']:text+=['',f"- [{f.get('id','Publication')}]({f['url']}): capture {'accepted' if f['accepted'] else 'not accepted'}; {f.get('inventory_nodes','unknown')} navigation nodes."]
    (ROOT/'SOURCE-MATRIX.md').write_text('\n'.join(text)+'\n')
    print(json.dumps({'rows':len(rows),'counts':counts},indent=2))

if __name__=='__main__': main()
