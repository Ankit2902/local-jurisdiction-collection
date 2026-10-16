#!/usr/bin/env python3
"""Seal standalone/operator-export reports from actual download/intake/test evidence."""
import hashlib,json,re
from pathlib import Path
from bs4 import BeautifulSoup
HERE=Path(__file__).resolve().parent

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evidence(p):return {'path':str(p.relative_to(HERE)),'sha256':sha(p),'bytes':p.stat().st_size}
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def main():
    freeze=load(HERE/'STANDALONE-CODE-FREEZE.json')
    for name,h in freeze['source_sha256'].items():
        if sha(HERE/name)!=h:raise ValueError('Post-freeze source mutation '+name)
    tests=(HERE/'standalone-test-results-final.txt').read_text()
    if not re.search(r'\nOK\s*$',tests):raise ValueError('Final Python tests not passed')
    node=load(HERE/'standalone-node-tests-final.json')
    if node['status']!='passed':raise ValueError('Final Node checks not passed')
    pilots=load(HERE/'publisher-intake-final/pilot-results.json');reports=[]
    for result in pilots:
        slug=result['slug'];folder=HERE/'publisher-downloads'/slug;r=load(folder/'download-receipt.json');source=folder/'publisher-export.html';raw=source.read_bytes();parsed=BeautifulSoup(raw,'html.parser');probe=HERE/'public-export-probes'/slug/'receipt.json';pr=load(probe)
        if result['parser_sha256']!=freeze['source_sha256']['cp_collect.py'] or result['import_script_sha256']!=freeze['source_sha256']['import_publisher_export.py']:raise ValueError('Final intake uses unfrozen parser/importer')
        if result['original_download_sha256']!=sha(source) or r['raw_sha256']!=sha(source):raise ValueError('Final raw download mismatch')
        commands=HERE/'publisher-intake-final'/slug/'commands.json'
        if any(x['returncode'] for x in load(commands)):raise ValueError('Parser CLI failure')
        report={'slug':slug,'best_method_status':'operator_assisted_publisher_export_semantic_e2e_passed','source_url':r['source_url'],'export_format':'HTML','acquisition_evidence':{'download_receipt':evidence(folder/'download-receipt.json'),'downloaded_file':evidence(source),'actual_executed_download_module':evidence(folder/'executed-download-module.mjs'),'operator_assistance':'Ordinary publisher browser selections and SaveHTML operated with supported CUA for this validation. Human operator can reproduce without Codex using README manual steps.','codex_free_manual_workflow_documented':True,'unattended_acquisition':False},'report_path':slug+'/STANDALONE-VALIDATION.json','currentness':{'publisher_currency_in_download':result['publisher_currency'],'expected_currency_source':'operator-pilot-jobs.json','embedded_evidence':'h1/h2 headerdisc attributes and/or exported footer','immutable_publisher_edition_token':None,'coherent_whole_corpus_version':False},'coverage':{'downloaded_scope':result['downloaded_title_scope'],'raw_download_legal_heading_count':len(parsed.select('#mainContent h3.Cite')),'raw_download_chapter_count':len(parsed.select('#mainContent h2.CH')),'parsed_chapters':result['parsed_chapters'],'whole_corpus_complete':False,'raw_download_only':False,'semantic_e2e':True,'image_assets_not_acquired':True},'output_records':result['audit']['records'],'semantic_intake':result,'intake_report':evidence(HERE/'publisher-intake-final'/slug/'intake-validation.json'),'parser_commands':evidence(commands),'source_lineage':evidence(HERE/'publisher-intake-final'/slug/'source-lineage.json'),'verified_output_manifest':evidence(HERE/'publisher-intake-final'/slug/'export/run-manifest.json'),'unattended_public_export_probe':{'status':'blocked_http403_challenge','receipt':evidence(probe),'response':evidence(probe.parent/'response.bin'),'executed_script':evidence(probe.parent/'executed-script.py'),'http_status':pr['http_status'],'challenge':pr['challenge'],'retries':0,'cookies_imported':False},'blockers':['Fresh unattended export acquisition is challenged in this environment; no unattended network success established.','Only listed bounded chapters are parsed/qualified; other titles/families, unlinked status nodes, uncodified updates, images and incorporated PDFs remain outside scope.'],'next_action':'Operator opens ordinary publisher page, selects scope, Print/SaveSelections→HTML→Save, registers unchanged file with actual time/source URL, then runs local importer with explicit expected currency and1–3 observed chapter numbers. For unattended fresh acquisition, obtain a normal supported environment or documented sanctioned publisher integration.','source_freeze':evidence(HERE/'STANDALONE-CODE-FREEZE.json'),'baseline_note':'Copied E2E/VALIDATION reports describe earlier sealed parser1.1; STANDALONE report qualifies new parser1.2 and actual downloaded publisherHTML.'}
        if slug=='flagstaff-az':report['ordinary_headed_browser_contrast']=evidence(HERE/'diagnostics/flagstaff-chromium148-headed/receipt.json')
        save(HERE/slug/'STANDALONE-VALIDATION.json',report);reports.append(report)
    report={'schema_version':1,'scope':'Five current Code Publishing municipalities; bounded semantic processing of actual publisherHTML downloads. No full corpus/database import.','unattended_fresh_acquisition_passed':0,'operator_assisted_publisher_export_semantic_passed':len(reports),'output_records':sum(x['output_records'] for x in reports),'whole_corpus_complete':False,'publisher_help_url':'https://www.codepublishing.com/help.html','runbook':'README.md','source_investigation':evidence(HERE/'source-investigation.json'),'source_freeze':evidence(HERE/'STANDALONE-CODE-FREEZE.json'),'tests':{'python_count':int(re.search(r'Ran (\d+) tests',tests).group(1)),'python_passed':True,'python_log':evidence(HERE/'standalone-test-results-final.txt'),'node':node,'node_log':evidence(HERE/'standalone-node-tests-final.json'),'actual_pilot_commands':evidence(HERE/'publisher-intake-final/executed-commands.json')},'results':reports}
    save(HERE/'STANDALONE-VALIDATION.json',report)
    files={str(p.relative_to(HERE)):sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['PACKAGE-SHA256.json','standalone-package-verify-final.json'] and not any(x in p.parts for x in ['__pycache__','.venv','work'])}
    save(HERE/'PACKAGE-SHA256.json',{'schema_version':3,'files':files})
    print(json.dumps({'status':'sealed','cities':len(reports),'operator_export_records':report['output_records'],'unattended_fresh_acquisition_passed':0,'files_hashed':len(files)}))
if __name__=='__main__':main()
