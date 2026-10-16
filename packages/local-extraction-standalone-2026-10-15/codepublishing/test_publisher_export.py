import copy,json,tempfile,unittest,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
import cp_collect as cp
import import_publisher_export as intake
import publisher_export as probe
HERE=Path(__file__).resolve().parent
JOBS=json.loads((HERE/'operator-pilot-jobs.json').read_text())
class PublisherExportTests(unittest.TestCase):
    def test_all5_actual_download_metadata_bodies_inventory_structure(self):
        count=0;tables=0
        for job in JOBS:
            r,raw,main,name=intake.read_export(HERE/job['receipt'],job['expected_currency']);derived,ranges=intake.bounded_selection(main,job['chapters']);slug=job['slug']
            page={'publication_id':'city-code','url':r['source_url'],'path':'raw/selected.html','sha256':cp.digest(derived)}
            snap={'jurisdiction_slug':slug,'jurisdiction':intake.ROUTES[slug]['jurisdiction'],'snapshot_id':'real-export-test','publications':[{'publication_id':'city-code','title':name}]}
            parsed=cp.parse_page(derived,page,snap);audit=intake.audit(derived,parsed['records'],parsed['nodes']);count+=len(parsed['records']);tables+=audit['structure_counts']['table']
            self.assertEqual([x['chapter'] for x in ranges],job['chapters']);self.assertTrue(all(x['locator']['kind']=='html-id' for x in parsed['nodes'] if x['node_kind']=='section'))
        self.assertEqual(count,43);self.assertEqual(tables,8)
    def test_download_module_and_source_byte_binding(self):
        for job in JOBS:
            p=HERE/job['receipt'];r=json.loads(p.read_text());self.assertEqual(r['raw_sha256'],cp.digest((p.parent/r['raw_artifact']).read_bytes()));self.assertEqual(r['executed_module_sha256'],cp.digest((p.parent/'executed-download-module.mjs').read_bytes()));self.assertEqual(r['executed_module_sha256'],cp.digest((HERE/'retain_publisher_download.mjs').read_bytes()));self.assertFalse(r['unattended_acquisition'])
    def test_unexpected_currency_rejected(self):
        with self.assertRaisesRegex(ValueError,'currency'):intake.read_export(HERE/JOBS[0]['receipt'],'unknown')
    def test_tampered_raw_and_escape_rejected(self):
        source=HERE/JOBS[1]['receipt'];r=json.loads(source.read_text())
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);r['raw_artifact']='export.html';(p/'export.html').write_text('tampered');(p/'receipt.json').write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'SHA256'):intake.read_export(p/'receipt.json',JOBS[1]['expected_currency'])
            r['raw_artifact']='../escape.html';(p/'receipt.json').write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'escapes'):intake.read_export(p/'receipt.json',JOBS[1]['expected_currency'])
    def test_missing_chapter_and_excess_scope_rejected(self):
        r,raw,main,name=intake.read_export(HERE/JOBS[1]['receipt'],JOBS[1]['expected_currency'])
        for chapters in [['999'],['1.05']*2,['1.05','1.10','1.15','1.20']]:
            with self.assertRaises(ValueError):intake.bounded_selection(main,chapters)
    def test_child_anchor_id_without_name_regression(self):
        raw=b'<main id="mainContent"><h2>Chapter 1 Intro</h2><h3 class="Cite"><a id="a1x1">1.1</a> Rule</h3><p>Whole body.</p></main>'
        p={'publication_id':'city-code','url':'https://www.codepublishing.com/CA/Fremont/cgi/menuCompile.pl','path':'raw/a.html','sha256':cp.digest(raw)};s={'jurisdiction_slug':'fremont-ca','jurisdiction':'Fremont','snapshot_id':'fixture','publications':[{'publication_id':'city-code','title':'Fremont Municipal Code'}]}
        parsed=cp.parse_page(raw,p,s);self.assertEqual(parsed['nodes'][1]['locator'],{'kind':'html-id','value':'a1x1'});self.assertTrue(parsed['records'][0]['source_url'].endswith('#a1x1'))
    def test_manual_registration_cli_is_browser_free(self):
        source=HERE/JOBS[1]['receipt'];r=json.loads(source.read_text())
        with tempfile.TemporaryDirectory() as t:
            command=[sys.executable,str(HERE/'register_manual_export.py'),'--file',str(source.parent/r['raw_artifact']),'--slug','fremont-ca','--source-url',r['source_url'],'--selection',r['metadata']['selection'],'--retrieved-at',r['finished_at'],'--out',str(Path(t)/'registered')]
            result=subprocess.run(command,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
            registered=Path(t)/'registered/download-receipt.json';rr=json.loads(registered.read_text());self.assertEqual(rr['classification'],'operator_attested_manual_publisher_download');self.assertEqual(rr['raw_sha256'],r['raw_sha256']);self.assertFalse(rr['unattended_acquisition']);intake.read_export(registered,JOBS[1]['expected_currency'])
    def test_all5_observed_public_form_probes_fail_closed(self):
        for slug in probe.SLUGS:
            job=probe.observed_form(slug);r=json.loads((HERE/'public-export-probes'/slug/'receipt.json').read_text());self.assertEqual(r['job'],json.loads(json.dumps(job)));self.assertEqual(r['http_status'],403);self.assertTrue(r['challenge']);self.assertFalse(r['accepted_menu_response']);self.assertFalse(r['download_acquired'])
if __name__=='__main__':unittest.main()
