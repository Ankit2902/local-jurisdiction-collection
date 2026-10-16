#!/usr/bin/env python3
"""Verify live acquisition receipts, invoke delivered acquisition/replay CLIs, audit exports.
This is a bounded verification runner, never a full-corpus completeness assertion.
"""
import argparse, csv, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
import cp_collect as cp
HERE=Path(__file__).resolve().parent

def digest(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def norm(s): return ' '.join(s.split())
def receipt(captures,slug,id):
    p=captures/slug/(id+'.receipt.json');r=load(p)
    if not r.get('accepted'): raise ValueError('Acquisition receipt rejected: '+str(p))
    raw=(p.parent/r['raw_artifact_path']).read_bytes()
    if digest(raw)!=r['sha256']: raise ValueError('Receipt raw hash mismatch')
    if r['browser_state']['sha256']!=r['sha256'] or r['after_capture']['sha256']!=r['sha256']: raise ValueError('Browser/raw integrity mismatch')
    for key in ['acquisition_script_sha256','checksum_module_sha256']:
        if digest((captures/'script-versions'/(r[key]+'.mjs')).read_bytes())!=r[key]: raise ValueError('Source script archive hash mismatch')
    return r,raw

def compare_markers(before,chapter,after):
    b,c,a=[x['browser_state']['currency'] for x in (before,chapter,after)]
    if not b or b!=a or (c and c!=b): raise ValueError('Unknown or changing publication currency; no coherent bounded run')
    if not before['finished_at']<=chapter['started_at']<=chapter['finished_at']<=after['started_at']: raise ValueError('Version receipts do not bracket legal acquisition')
    return b

def audit(raw,rows,supplementary=False):
    source=BeautifulSoup(raw,'html.parser').select_one('#mainContent')
    raw_table_count=len(source.select('table'))
    # Independent visible-source denominator: publisher sticky-header table clones
    # live under display:none and are UI duplicates, not legal table rows.
    for el in list(source.select('[hidden],[aria-hidden="true"],[style]')):
        if el.attrs is not None and (el.has_attr('hidden') or el.get('aria-hidden')=='true' or re.search(r'display\s*:\s*none',el.get('style',''),re.I)):
            el.decompose()
    # Compare real source paragraphs in every publisher P-level to complete export bodies.
    pars=[p for p in source.select('p') if any(re.fullmatch('P[0-9]+',c) for c in p.get('class',[]))]
    exported=BeautifulSoup(''.join(r['full_text'] for r in rows),'html.parser')
    for p in pars:
        if norm(p.get_text(' ',strip=True)) not in norm(exported.get_text(' ',strip=True)): raise ValueError('Missing complete P-level body')
    src_ids=[h.get('id') for h in source.select('h3.Cite')]
    cite_links=[urlsplit(a.get('href','')).fragment.split('#')[-1] for a in source.select('.CiteTOC a[href]')]
    if cite_links and set(cite_links)!=set(src_ids): raise ValueError('Chapter CiteTOC/section heading inventory mismatch')
    actual=[r['section_number'] for r in rows if r['section_number']]
    expected=[cp.NUMBER.match(norm(h.get_text(' ',strip=True))).group(1) for h in source.select('h3.Cite')]
    if actual!=expected: raise ValueError('Source section numbers/order differ from export')
    # Exact table cell text and span attributes, list order, and superscripts survive HTML export.
    structure={}
    for tag in ['table','tr','td','th','ol','ul','li','sup','sub','blockquote']:
        src=source.select(tag);dst=exported.select(tag)
        signature=lambda e:(norm(e.get_text(' ',strip=True)),e.get('rowspan'),e.get('colspan'),e.get('start'),e.get('type'))
        if [signature(e) for e in src]!=[signature(e) for e in dst]: raise ValueError('Structure mismatch '+tag)
        structure[tag]=len(src)
    if not all(r['code_name'] and (supplementary or (r['title'] and r['chapter'])) for r in rows): raise ValueError('Observed hierarchy/display publication missing')
    if supplementary and any(r['title'] or r['chapter'] or r['section_number'] for r in rows): raise ValueError('Invented supplementary hierarchy/number')
    return dict(source_sections=len(src_ids),export_records=len(rows),p_level_paragraphs=len(pars),p_classes=sorted({c for p in pars for c in p.get('class',[]) if re.fullmatch('P[0-9]+',c)}),chapter_toc_equals_section_inventory=bool(cite_links),complete_p_level_bodies=True,source_section_order_equal=True,observed_hierarchy_present=True,structure_counts=structure,raw_dom_table_count=raw_table_count,excluded_hidden_table_clones=raw_table_count-structure['table'])

def invoke(args,log):
    command=[sys.executable,str(HERE/'cp_collect.py')]+list(map(str,args))
    p=subprocess.run(command,capture_output=True,text=True)
    log.append(dict(argv=command,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
    if p.returncode: raise ValueError('Delivered CLI failed: '+p.stderr[-1000:])

def run(captures,output):
    captures=Path(captures).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    results=[]
    for route in load(HERE/'routes.json'):
        slug=route['slug']
        if slug=='foster-city-ca':continue
        root,rootraw=receipt(captures,slug,'root-confirmed');title,titleraw=receipt(captures,slug,'title')
        post,postraw=receipt(captures,slug,'root-final-table' if slug=='fremont-ca' else 'root-post')
        chapterid='chapter-bracketed' if slug=='flagstaff-az' else 'chapter'
        chapter,chapterraw=receipt(captures,slug,chapterid)
        before=root;after=post
        if slug=='flagstaff-az':before,_=receipt(captures,slug,'currency-before');after,_=receipt(captures,slug,'currency-after-bracket')
        currency=compare_markers(before,chapter,after)
        cases=[('adoption',title,titleraw,chapter,chapterraw)]
        if slug=='fremont-ca':
            rt,rr=receipt(captures,slug,'title-business');rc,rb=receipt(captures,slug,'chapter-business');compare_markers(root,rc,post)
            cases.append(('business',rt,rr,rc,rb))
            rt,rr=root,rootraw;rc,rb=receipt(captures,slug,'cross-reference-table');compare_markers(root,rc,post)
            cases.append(('cross-reference-table',rt,rr,rc,rb))
        migration=bool(re.search(r'code.{0,40}now hosted',root['browser_state']['body_text'],re.I))
        work=output/slug;work.mkdir(exist_ok=True); logs=[];audits=[]
        pages=[];publications=[dict(publication_id='city-code',title=route['jurisdiction']+(' City Code' if slug=='flagstaff-az' else ' Municipal Code'),currency_raw=currency,scope_status='bounded_observed_inventory_only')]
        for i,(name,nav,navraw,legal,legalraw) in enumerate(cases):
            rawdir=work/'plan-raw';rawdir.mkdir(exist_ok=True)
            navpath='plan-raw/'+name+'-navigation.html';rawpath='plan-raw/'+name+'.html'
            (work/navpath).write_bytes(navraw);(work/rawpath).write_bytes(legalraw)
            first=legal['browser_state']['legal_headings'][0]['id'] if name!='cross-reference-table' else BeautifulSoup(legalraw,'html.parser').select_one('#mainContent h1')['id']
            heading=BeautifulSoup(navraw,'html.parser').select_one('#mainContent h1.Title').get_text(' ',strip=True) if name!='cross-reference-table' else ''
            pages.append(dict(publication_id='city-code',content_selector='#mainContent',url=legal['job']['url'],publisher_version=currency,hierarchy={'title':heading} if heading else {},expected_heading_id=first,navigation_evidence={'path':navpath,'sha256':digest(navraw),'url':nav['job']['url']},rendered_artifact={'path':rawpath,'sha256':digest(legalraw),'rendered_url':legal['browser_state']['url'],'retrieved_at':legal['finished_at']}))
        plan=dict(jurisdiction_slug=slug,jurisdiction=route['jurisdiction'],root_url=route['discovery_url'],snapshot_id='live-2026-10-15-'+digest(chapterraw)[:16],publications=publications,pages=pages)
        cp.save(work/'acquisition-plan.json',plan)
        invoke(['acquire','--plan',work/'acquisition-plan.json','--out',work/'acquired'],logs)
        snapshot=work/'acquired/snapshot.json';checkpoint=work/'checkpoint.json'
        if checkpoint.exists(): checkpoint.unlink() # this runner's disposable isolated checkpoint only
        invoke(['replay','--snapshot',snapshot,'--out',work/'resumed','--checkpoint',checkpoint,'--stop-after','1'],logs)
        invoke(['replay','--snapshot',snapshot,'--out',work/'resumed','--checkpoint',checkpoint],logs)
        invoke(['replay','--snapshot',snapshot,'--out',work/'export'],logs)
        for name in ['aggregate-fulltext.json','aggregate-fulltext.csv','source-nodes.jsonl','node-dispositions.jsonl','record-provenance.jsonl']:
            if (work/'resumed'/name).read_bytes()!=(work/'export'/name).read_bytes():raise ValueError('Resumed/clean output differs '+name)
        rows=load(work/'export/aggregate-fulltext.json')['provisions']
        with (work/'export/aggregate-fulltext.csv').open(encoding='utf-8-sig',newline='') as f:
            if list(csv.DictReader(f))!=rows: raise ValueError('CSV/JSON mismatch')
        for name,nav,navraw,legal,legalraw in cases:
            key=cp.doc_key(legal['job']['url']);case_rows=[r for r in rows if cp.doc_key(r['source_url'])==key]
            audits.append(dict(case=name,raw_sha256=digest(legalraw),**audit(legalraw,case_rows,name=='cross-reference-table')))
        inventory_links=[a for a in root['browser_state']['all_links'] if re.search(r'title|reference|ordinance|annexation|franchise|district|handbook|charter|resolution',a['label'],re.I)]
        if slug=='flagstaff-az': inventory_links=receipt(captures,slug,'family-toc')[0]['browser_state']['all_links']
        legacy_migration_target=next((a['href'] for a in root['browser_state']['all_links'] if 'ecode360.com' in a['href']),None)
        used_receipts={r['job']['id'] for r in [root,post,before,after]+[x for case in cases for x in [case[1],case[3]]]}
        report=dict(jurisdiction_slug=slug,status='legacy_migrated_vendor_sample_passed' if migration else 'bounded_live_cua_acquisition_parser_export_passed',current_authoritative_route=legacy_migration_target if migration else route['discovery_url'],legacy_migration_notice=migration,whole_corpus_complete=False,publication_inventory_complete=False,source_currency=currency,pre_post_currency_equal=True,version_atomicity='same publisher label bracketing bounded DOM capture; no publisher snapshot token',source_receipts=[str((captures/slug/(id+'.receipt.json')).relative_to(HERE)) for id in sorted(used_receipts)],acquisition_script_sha256=chapter['acquisition_script_sha256'],checksum_module_sha256=chapter['checksum_module_sha256'],parser_sha256=digest((HERE/'cp_collect.py').read_bytes()),csv_json_equal=True,restart_equal=True,pages=len(cases),records=len(rows),audits=audits,root_inventory_links=inventory_links,source_hierarchy='root/title observed hrefs, legal heading IDs and publisher paragraph levels',limitations=['Only listed bounded chapters parsed; other chapters, appendices, supplements, images, incorporated documents and PDF contents are not fully inventoried/extracted.','Publication label equality is not whole-corpus version atomicity.','Supported CUA uses connected browser session; standalone transport has separate results.'])
        cp.save(work/'commands.json',logs);cp.save(work/'E2E-VALIDATION.json',report);results.append(report)
    cp.save(output/'E2E-VALIDATION.json',{'schema_version':1,'whole_corpus_complete':False,'results':results})
    return [{'slug':r['jurisdiction_slug'],'status':r['status'],'records':r['records']} for r in results]
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--captures',default=str(HERE/'current-cua'));a.add_argument('--out',default=str(HERE/'current-pipeline'));args=a.parse_args();print(json.dumps(run(args.captures,args.out),indent=2))
