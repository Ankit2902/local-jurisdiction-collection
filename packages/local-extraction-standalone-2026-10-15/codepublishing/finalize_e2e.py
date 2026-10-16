#!/usr/bin/env python3
"""Build handoff reports from retained receipts and final checks; never acquire network data."""
import argparse, hashlib, json, platform, re
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(p): return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def artifact(p):return {'path':str(p.relative_to(HERE)),'sha256':sha(p),'bytes':p.stat().st_size}
def build():
    freeze=load(HERE/'CODE-FREEZE.json')
    for name,h in freeze['source_sha256'].items():
        if sha(HERE/name)!=h:raise ValueError('Post-freeze source change '+name)
    tests=(HERE/'test-results-final.txt').read_text()
    if not re.search(r'\nOK\s*$',tests):raise ValueError('Final Python tests not passed')
    node=load(HERE/'node-test-results-final.json')
    if node['status']!='passed':raise ValueError('Final Node tests not passed')
    pipeline=load(HERE/'current-pipeline/E2E-VALIDATION.json')
    if len(pipeline['results'])!=6:raise ValueError('Missing bounded city results')
    results=[]
    for report in pipeline['results']:
        slug=report['jurisdiction_slug']
        if report['parser_sha256']!=freeze['source_sha256']['cp_collect.py']:raise ValueError('Parser was not revalidated after freeze')
        cmds=HERE/'current-pipeline'/slug/'commands.json'
        if any(c['returncode'] for c in load(cmds)):raise ValueError('Nonzero final CLI invocation')
        browser_receipts=[]
        for p in sorted((HERE/'current-cua'/slug).glob('*.receipt.json')):
            r=load(p);raw=p.parent/r['raw_artifact_path']
            browser_receipts.append(dict(used_in_final_pipeline=str(p.relative_to(HERE)) in report['source_receipts'],receipt=artifact(p),raw=artifact(raw),accepted=r['accepted'],job=r['job'],acquisition_script_sha256=r.get('acquisition_script_sha256'),checksum_module_sha256=r.get('checksum_module_sha256'),before_after_sha256_match=r.get('browser_state',{}).get('sha256')==r.get('after_capture',{}).get('sha256')==r['sha256']))
        sp=HERE/'current-playwright'/slug/'chapter.receipt.json';sr=load(sp)
        standalone={'status':'blocked_http403_challenge' if sr['http_status']==403 and sr['challenge'] and not sr['accepted'] else 'inspect_receipt','accepted':sr['accepted'],'receipt':artifact(sp),'raw':artifact(sp.parent/sr['raw_artifact_path']),'runtime':sr['runtime'],'acquisition_script_sha256':sr['acquisition_script_sha256'],'archived_script':artifact(HERE/'current-playwright/acquisition-script.py'),'blocker':'Vendor returns challenge to isolated standalone Chrome; no accepted legal body. Connected CUA session result is separate.'}
        finaltrial=HERE/'final-playwright'/slug/'chapter.receipt.json'
        if finaltrial.exists():
            fr=load(finaltrial);standalone['final_guarded_revision_trial']={'receipt':artifact(finaltrial),'accepted':fr['accepted'],'http_status':fr['http_status'],'acquisition_script_sha256':fr['acquisition_script_sha256'],'matches_frozen_script':fr['acquisition_script_sha256']==freeze['source_sha256']['acquire_playwright.py']}
        report.update(supported_cua={'status':'bounded_live_acquisition_parser_export_passed','complete_DOM_integrity':'pureJS UTF8SHA256 before/after equals NodeSHA256 retained raw; joined UTF16 chunk strings written once','receipts':browser_receipts,'final_guarded_module_live_check':artifact(HERE/'current-cua/fremont-ca/root-final-table.receipt.json'),'immutable_target_guard_test':'test_acquire_cua.mjs plus live repeated-target rejection'},standalone_playwright=standalone,commands=artifact(cmds),export_manifest=artifact(HERE/'current-pipeline'/slug/'export/run-manifest.json'),tests={'python_count':int(re.search(r'Ran (\d+) tests',tests).group(1)),'python_passed':True,'node':node},code_freeze=artifact(HERE/'CODE-FREEZE.json'),remaining_blockers=['Standalone HTTP403 prevents qualifying unattended browser CLI transport here.','Complete multi-family publication inventory, missing/unlinked status-node reconciliation, scope decisions and whole-corpus version checks remain unperformed.','Live rowspan/colspan, image and incorporated-PDF handling beyond these samples still require source qualification; synthetic tests cover spans/lists/images.'])
        if slug=='seatac-wa':report['current_ecode_report']='../ecode360/E2E-VALIDATION.json';report['remaining_blockers'].insert(0,'Legacy source announces eCode360 SE4633; current municipal edition is outside this legacy adapter.')
        save(HERE/slug/'E2E-VALIDATION.json',report);results.append(report)
    scope=[]
    for id in ['root-scope-confirmed','scope-toc','municipal-migration','district-landing','district-currency']:
        p=HERE/'current-cua/foster-city-ca'/(id+'.receipt.json');r=load(p)
        if not r['accepted']:raise ValueError('Foster scope evidence rejected')
        scope.append({'receipt':artifact(p),'raw':artifact(p.parent/r['raw_artifact_path']),'source_url':r['job']['url']})
    foster=dict(jurisdiction_slug='foster-city-ca',status='municipal_migrated_ecode360_district_scope_discovery_only',current_authoritative_route='https://ecode360.com/FO4449',current_ecode_report='../ecode360/E2E-VALIDATION.json',whole_corpus_complete=False,municipal_extracted=False,district_extracted=False,district={'name':'Estero Municipal Improvement District Code','observed_url':'https://www.codepublishing.com/CA/FosterCity/EsteroMIDC/EsteroNT.html','currency':load(HERE/'current-cua/foster-city-ca/district-currency.receipt.json')['browser_state']['currency'],'inventory':'Source TOC exposes enabling act,9titles including reserved3/7,annexations,disposition table; scope must be decided separately.'},evidence=scope,remaining_blockers=['Municipal code current route reassigned to eCode360.','District inclusion/scope decision required before extracting; no district legal bodies parsed.'])
    save(HERE/'foster-city-ca/E2E-VALIDATION.json',foster)
    final=dict(schema_version=1,date='2026-10-15',scope='bounded live acquisition and sample export; no full corpus/import',whole_corpus_complete=False,current_codepublishing_municipalities=5,current_codepublishing_records=sum(r['records'] for r in results if r['jurisdiction_slug']!='seatac-wa'),legacy_seatac_records=12,current_supported_cua_path_passed=True,standalone_playwright_live_status='all6 observed chapter jobs HTTP403 challenge; final guarded Flagstaff trial separate',tests={'python':artifact(HERE/'test-results-final.txt'),'node':artifact(HERE/'node-test-results-final.json'),'current_pipeline':artifact(HERE/'current-pipeline-results-final.txt')},source_freeze=artifact(HERE/'CODE-FREEZE.json'),environment={'python':platform.python_version(),'python_dependencies':artifact(HERE/'requirements.txt'),'optional_browser_dependencies':artifact(HERE/'requirements-browser.txt'),'node_requirement':'Node20+; CUA managed Node host','recorded_commands':'current-pipeline/<slug>/commands.json'},results=results+[foster])
    save(HERE/'E2E-VALIDATION.json',final)
    files={str(p.relative_to(HERE)):sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in {'PACKAGE-SHA256.json','package-verify-final.json'} and not any(x in p.parts for x in ['__pycache__','.venv','work'])}
    save(HERE/'PACKAGE-SHA256.json',{'schema_version':2,'files':files})
    print(json.dumps({'status':'reports_built','current_cities':5,'current_records':final['current_codepublishing_records'],'legacy_seatac_records':12,'files_hashed':len(files)}))
if __name__=='__main__':build()
