"""Rebuild bounded validation samples and evidence reports offline."""
from __future__ import annotations
import argparse,json,re,unittest,io
from pathlib import Path
from datetime import datetime,timezone
from bs4 import BeautifulSoup
from common import *
from san_mateo import parse_xml,publication_inventory,BASE as XML_BASE
from king_county import parse_title,landing_inventory
from daly_city import inventory,parse_content,route_evidence,ROOT as DALY_ROOT
HERE=Path(__file__).resolve().parent
KING_ROOT='https://kingcounty.gov/en/dept/council/governance-leadership/county-legislation-codes/king-county-code'
KING_FILES={'king-title1.dom.html':'04_Title_1.htm','king-title2a.dom.html':'05_Title_2A.htm','king-title21a.dom.html':'24-30_Title_21A.htm','king-charter.dom.html':'03_Charter.htm'}
def raw_url(raw,name):
    side=raw/(name.replace('.bin','.json'))
    return json.loads(side.read_text())['url']
def evidence(raw,names):
    return [{'path':'raw/'+name,'sha256':sha((raw/name).read_bytes()),'bytes':(raw/name).stat().st_size} for name in names]
def selected(result,numbers):
    indices=[i for i,row in enumerate(result['rows']) if row['section_number'] in numbers]
    rows=[result['rows'][i] for i in indices];prov=[result['provenance'][i] for i in indices];ids={p['node_id'] for p in prov}
    return {'rows':rows,'provenance':prov,'nodes':[n for n in result['nodes'] if n['node_id'] in ids],'dispositions':[d for d in result['dispositions'] if d['node_id'] in ids]}
def emit(out,jur,pub,result,source,version):
    return package(out,jur,pub,result['rows'],result['nodes'],result['dispositions'],result['provenance'],version,[source])
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE);ap.add_argument('--raw',type=Path,default=HERE/'raw');a=ap.parse_args();out=a.out.resolve();raw=a.raw.resolve();out.mkdir(parents=True,exist_ok=True)
    if raw != out/'raw':
        import shutil
        shutil.copytree(raw,out/'raw',dirs_exist_ok=True);raw=out/'raw'
    suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_methods.py');log=io.StringIO();tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite);(out/'TEST-RESULTS.txt').write_text(log.getvalue());assert tests.wasSuccessful(),log.getvalue()
    test_info={'command':'python -m unittest discover -s . -p test_methods.py -v','tests_run':tests.testsRun,'passed':tests.wasSuccessful(),'details':'TEST-RESULTS.txt','human_review':False}
    commit=json.loads((raw/'san-commit.bin').read_bytes());revision=commit['sha'];tree=json.loads((raw/'san-tree.bin').read_bytes());san=out/'san-mateo-ca';san.mkdir(exist_ok=True)
    families=publication_inventory(tree,revision);dump(san/'publications.json',families)
    include_inventory=[]
    for name in ['san-index.bin','san-code-index.bin']:
        import xml.etree.ElementTree as ET,posixpath
        root=ET.fromstring((raw/name).read_bytes());document='index.xml' if name=='san-index.bin' else XML_BASE+'code/index.xml'
        for n in root.iter():
            if n.tag.rsplit('}',1)[-1]=='include':
                target=posixpath.normpath(posixpath.join(posixpath.dirname(document),n.get('href','')));include_inventory.append({'document':document,'href':n.get('href'),'target':target,'present_in_frozen_tree':any(x['path']==target for x in tree['tree'])})
    dump(san/'include-inventory.json',include_inventory)
    san_samples=[]
    for name,pub in [('san-title1.bin','municipal-code'),('san-charter.bin','charter')]:
        result=parse_xml((raw/name).read_bytes(),raw_url(raw,name),pub,revision,'raw/'+name,scrape_date='2026-10-15');stats=emit(san/'samples'/pub,'San Mateo, CA',pub,result,raw/name,revision);stats.update({'sample':str((san/'samples'/pub).relative_to(out)),'section_nodes':sum(n['node_kind']=='section' for n in result['nodes']),'tag_counts':result['tag_counts']});san_samples.append(stats)
    san_report={'jurisdiction':'San Mateo, CA','method':'publisher_designated_openlaw_xml','status':'bounded_pilot_validated_full_collection_not_run','full_corpus_ready':False,'path_base':'bundle_root','tests':test_info,'live_evidence':evidence(raw,['san-commit.bin','san-tree.bin','san-index.bin','san-code-index.bin','san-title1.bin','san-charter.bin','san-drafting.bin']),'official_repository':'https://github.com/cityofsanmateo/law-xml','pinned_commit':revision,'commit_time':commit['commit']['committer']['date'],'publication_currency':{'current_through':None,'reason':'Commit timestamp is not legal currency; code metadata effective=0001-01-02 is a sentinel and not a current-through date'},'samples':san_samples,'publication_roots':[x['publication_id'] for x in families],'include_references':len(include_inventory),'all_inventory_includes_present':all(x['present_in_frozen_tree'] for x in include_inventory),'limitations':['Complete repository archive acquisition command provided but not exercised; frozen recursive Git tree retained instead.','Only Title 1 and Charter parsed; no full Municipal Code extraction.','XML-to-official-bulk-HTML comparison at the same commit remains unperformed.','Includes are inventoried and unresolved includes fail disposition; general cross-file include expansion remains an integration task.','Images/nested XML sections tested synthetically; no live image-rich XML title qualified.']}
    dump(san/'VALIDATION-REPORT.json',san_report)
    king=out/'king-county-wa';king.mkdir(exist_ok=True);publications=landing_inventory((raw/'king-landing.dom.html').read_text(),KING_ROOT);dump(king/'publications.json',publications)
    king_results=[];independent=[]
    targets={'king-title1.dom.html':{'1.02.030','1.03.020','1.12.050'},'king-title2a.dom.html':{'2A.300.050','2A.320.510'},'king-title21a.dom.html':{'21A.04.010','21A.06.025N','21A.06.333A'},'king-charter.dom.html':{'','110','220','220.10','350.20.61'}}
    for name,filename in KING_FILES.items():
        result=parse_title((raw/name).read_bytes(),'https://aqua.kingcounty.gov/council/clerk/code/'+filename,charter='charter' in name,raw_path='raw/'+name,scrape_date='2026-10-15');sample=selected(result,targets[name]);label=name.split('.')[0].replace('king-','');stats=emit(king/'samples'/label,'King County, WA','charter' if 'charter' in name else 'county-code',sample,raw/name,sha((raw/name).read_bytes()))
        toc_numbers={n['number'] for n in result['toc']};body_numbers={r['section_number'] for r in result['rows'] if r['section_number']};missing=sorted(toc_numbers-body_numbers);extra=sorted(body_numbers-toc_numbers) if result['toc'] else []
        stats.update({'document':filename,'sample':str((king/'samples'/label).relative_to(out)),'parsed_section_bodies':sum(bool(r['section_number']) for r in result['rows']),'unique_printed_section_labels':len(body_numbers),'independent_toc_entries':len(result['toc']),'toc_without_body':missing,'body_without_toc':extra,'tables_in_source':result['tables'],'selected_sections':[r['section_number'] for r in sample['rows']]});king_results.append(stats);independent.append({'document':filename,'section_toc':result['toc'],'source_heading_inventory':result['nodes']})
    dump(king/'independent-inventory.json',independent)
    king_report={'jurisdiction':'King County, WA','method':'first_party_title_html_plus_charter','status':'bounded_pilot_validated_with_source_reconciliation_gaps','full_corpus_ready':False,'path_base':'bundle_root','tests':test_info,'live_evidence':evidence(raw,['king-landing.dom.html',*KING_FILES]),'source_transport':'Codex in-app browser DOM, saved in 60,000-character chunks; HTTP status unavailable through DOM capture. Direct Requests landing HTTP 403 retained separately.','original_byte_decoding_live_validated':False,'encoding_validation':'Live browser DOM is browser-decoded/transcoded UTF-8. CP1252/UTF8 strict decode regression uses synthetic original-byte fixtures.','title_documents_in_landing':sum(x['kind']=='title' for x in publications['documents']),'charter_currency_discrepancy':{'landing':'Updated: 1/10/2024','document':'UPDATED: January 10, 2023','resolution':'unresolved; retain both markers'},'samples':king_results,'limitations':['TOC/body differences are potential source amendments, stale TOC or unsupported source variants pending reconciliation, not definitive omissions.','Full title HTML retained but only named representative provisions exported; other titles not acquired.','Board of Health linked compilation inventoried but scope decision remains pending.','Original HTTP bytes and official PDF/Word parity comparison were not obtained; browser-decoded text is the live evidence.','Chapter introductory/editorial cross-references require full-corpus container disposition profile beyond sampled sections.','Browser acquisition requires supported session; no standalone browser transport is claimed.']}
    dump(king/'VALIDATION-REPORT.json',king_report)
    daly=out/'daly-city-ca';daly.mkdir(exist_ok=True);toc=inventory(json.loads((raw/'daly-toc.json').read_bytes()));dump(daly/'source-inventory.json',toc);dump(daly/'publications.json',json.loads((raw/'daly-publications.json').read_bytes()));route=route_evidence((raw/'daly-city.dom.html').read_text());dump(daly/'official-route.json',route)
    daly_rows=[];daly_nodes=[];daly_disp=[];daly_prov=[];daly_samples=[]
    selections=[('daly-content-0.json','1.01.010 - Adoption.'),('daly-content-0.json','1.04.020 - Definitions—Rules of construction.'),('daly-content-1.json',None),('daly-content-2.json','15.32.210 - Appendix D—Section D101.2—Added.')]
    for name,heading in selections:
        if heading is None:node=next(n for n in toc if n['display_heading'].startswith('15.08.080 -'))
        else:node=next(n for n in toc if n['display_heading']==heading)
        data=(raw/name).read_bytes();row,n,d,p=parse_content(json.loads(data),node,data,'raw/'+name,scrape_date='2026-10-15');daly_rows.append(row);daly_nodes.append(n);daly_disp.append(d);daly_prov.append(p);daly_samples.append({'number':row['section_number'],'heading':row['section_name'],'text_length':len(row['full_text']),'tables':len(BeautifulSoup(p['semantic_html'],'html.parser').select('table'))})
    stats=package(daly/'samples'/'municipal-code','Daly City, CA','municipal-code',daly_rows,daly_nodes,daly_disp,daly_prov,sha((raw/'daly-toc.json').read_bytes()),[raw/'daly-toc.json',raw/'daly-content-0.json',raw/'daly-content-1.json',raw/'daly-content-2.json'])
    daly_report={'jurisdiction':'Daly City, CA','method':'current_official_municode_replacement','status':'bounded_replacement_pilot_validated_historical_elaws_deauthorized','full_corpus_ready':False,'path_base':'bundle_root','tests':test_info,'live_evidence':evidence(raw,['daly-city.dom.html','daly-municode-ordinances.dom.html','daly-municode-code.dom.html','daly-clients.json','daly-publications.json','daly-toc.json','daly-content-0.json','daly-content-1.json','daly-content-2.json','daly-content-3.json']),'official_routing':{'city_homepage_link':'https://library.municode.com/ca/daly_city/ordinances/code_of_ordinances','observed_browse_codes_link':DALY_ROOT,'elaws_current_official_link_confirmed':False,'elaws_http_probe':'Requests timed out after 40 seconds; not retried/bypassed'},'client_id':1857,'product_id':16311,'publication_currency':{'raw':'DALY MUNICIPAL CODE Codified through Ordinance No. 1488, passed March 9, 2026. (Supp. No. 38)','normalized_current_through':'2026-03-09','online_content_updated':'2026-05-21','distinction':'Four adopted ordinances not yet codified are listed separately; no updates collected.'},'inventory_nodes':len(toc),'section_shaped_nodes':sum(n['node_kind']=='section' for n in toc),'sample':stats,'representative_checks':daly_samples,'limitations':['Municode API latest version is moving; final full-tree/version-marker comparison is required before full collection.','Four bounded requests only; exact selected nodes emitted from chapter bundles; most inventory nodes not acquired.','No standalone Charter or appendix family appeared at root; section amendments referring to Appendix D were sampled, not imported external model-code appendices.','Historical eLaws identity/error-shell tests are synthetic offline checks; current source authority is Municode.','Live browser-to-API representative body parity beyond publication currency remains to be reviewed.']}
    dump(daly/'VALIDATION-REPORT.json',daly_report)
    # Capture immutable evidence lineage, never pretend DOM captures preserve original HTTP bytes.
    dump(out/'VALIDATION-REPORT.json',{'scope':'Three isolated bounded method pilots; no full-corpus extraction or import','tests':test_info,'reports':[str((d/'VALIDATION-REPORT.json').relative_to(out)) for d in [san,king,daly]],'production_changes':False,'runtime_dependencies':'requirements.txt','full_corpus_ready':False})
    print(json.dumps({'tests_run':tests.testsRun,'passed':tests.wasSuccessful(),'reports':3,'san_samples':san_samples,'king_samples':king_results,'daly_samples':daly_samples},indent=2))
if __name__=='__main__':main()
