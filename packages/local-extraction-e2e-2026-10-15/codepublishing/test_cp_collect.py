import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
import cp_collect as cp

HERE = Path(__file__).resolve().parent
ROOT = 'https://www.codepublishing.com/WA/Renton/'
RICH = '''<main id="mainContent"><h1 id="I">Title I ADMINISTRATIVE</h1><p>The parent shall apply.</p>
<section><h2 id="ch">Chapter 1 Introductory rules</h2><p>Parent introduction remains operative.</p>
<div><h3 id="one">1-1-1 Rule.</h3><p>A long opening paragraph shall remain.</p><ol start="3"><li><p>Nested once.</p><ol type="a"><li>Child entry.</li></ol></li></ol>
<table><caption>Fees</caption><tr><th rowspan="2">Class</th><th colspan="2">Rates</th></tr><tr><td>First</td><td>Second</td></tr></table><p>H<sub>2</sub>O and x<sup>2</sup>; <a href="#two">see rule two</a>.</p><img alt="Diagram" src="d.png"><p class="Footnote">History and note.</p></div>
<div><h3 id="two">1-1-1 Duplicate printed locator.</h3><p>Second distinct legal body.</p><p>Last paragraph survives wrappers.</p></div></section>
<h2 id="appendix">Appendix A</h2><p>Appendix text applies.</p><h3 id="reserved">1-1-3 Reserved.</h3>
<h3 id="empty">1-1-4 Empty but unresolved.</h3></main>'''


def page(raw=RICH, url=ROOT+'#!/Renton01/Renton0101.html', publication='city-code'):
    return {'url':url,'path':'raw/a.html','sha256':cp.digest(raw.encode()),'publication_id':publication,'content_selector':'#mainContent'}


def snapshot(pages=None):
    return {'root_url': ROOT, 'jurisdiction_slug':'renton-wa', 'jurisdiction':'Renton',
            'snapshot_id':'fixture-immutable','retrieved_at':'2026-10-15',
            'publications':[{'publication_id':'city-code','scope_decision':'synthetic fixture only'}], 'pages':pages or [page()]}


class RouteTests(unittest.TestCase):
    def test_jurisdiction_boundary_and_encoded_escape(self):
        for bad in ['https://www.codepublishing.com/WA/Burien/html/B.html', ROOT+'../Burien/', ROOT+'%2e%2e/Burien/', 'http://www.codepublishing.com/WA/Renton/', ROOT+'%2F../Burien/']:
            self.assertFalse(cp.allowed(ROOT,bad),bad)
        self.assertTrue(cp.allowed(ROOT,ROOT+'html/Renton01/Renton0101.html'))
        self.assertFalse(cp.allowed(ROOT, 'https://www.codepublishing.com/WA/RentonOther/a'))

    def test_hash_identity_and_section_anchor(self):
        a=ROOT+'#!/Renton01/Renton0101.html'
        self.assertEqual(cp.doc_key(a+'#1-1-1'),a)
        self.assertNotEqual(cp.doc_key(a),cp.doc_key(ROOT+'#!/Renton01/Renton0102.html'))
        self.assertEqual(cp.doc_key(ROOT+'html/a.html#s1'),cp.doc_key(ROOT+'html/a.html#s2'))
        self.assertEqual(cp.anchor_url(a,'one'),a+'#one')

    def test_frames_are_explicit_documents_and_cross_city_rejected(self):
        html='<frameset><frame name="toc" src="FlagstaffNT.html"><frame name="body" src="html/Flagstaff01/Flagstaff01.html"><frame src="/WA/Renton/"></frameset>'
        rows=cp.links(html,'https://www.codepublishing.com/AZ/Flagstaff/','https://www.codepublishing.com/AZ/Flagstaff/')
        self.assertEqual(len(rows),2);self.assertTrue(all(r['node_kind']=='frame' for r in rows))

    def test_roman_and_hash_observed_inventory(self):
        rows=cp.links('<a href="#!/Renton01/Renton01.html">Title I ADMINISTRATIVE</a>', ROOT, ROOT)
        self.assertEqual(rows[0]['node_kind'],'title');self.assertTrue(rows[0]['requires_rendered_acquisition'])

    def test_hash_http_acquisition_fails_closed(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(ValueError,'rendered'):
            cp.fetch(ROOT+'#!/a.html',ROOT,d,0)

    def test_provider_migration_is_not_followed(self):
        fake=type('R',(),{'status_code':302,'headers':{'Location':'https://ecode360.com/FO4449'}})()
        with tempfile.TemporaryDirectory() as d, patch.object(cp.requests.Session,'get',return_value=fake) as get:
            with self.assertRaisesRegex(ValueError,'migration'):
                cp.fetch(ROOT,ROOT,d,0)
            self.assertEqual(get.call_count,1)


class ParsingTests(unittest.TestCase):
    def setUp(self):
        self.got=cp.parse_page(RICH.encode(),page(),snapshot())

    def test_source_identity_keeps_repeated_citations(self):
        got=[r for r in self.got['records'] if r['section_number']=='1-1-1']
        self.assertEqual(len(got),2)
        self.assertEqual(len({p['record_id'] for p in self.got['provenance']}),len(self.got['records']))
        self.assertNotEqual(got[0]['source_url'],got[1]['source_url'])

    def test_structure_and_once_only_nested_blocks(self):
        text=self.got['records'][2]['full_text'];s=BeautifulSoup(text,'html.parser')
        self.assertEqual(text.count('Nested once.'),1)
        self.assertEqual(s.select_one('th[rowspan]')['rowspan'],'2')
        self.assertEqual(s.select_one('th[colspan]')['colspan'],'2')
        self.assertEqual(s.select_one('ol')['start'],'3')
        self.assertTrue(s.select_one('li ol li'));self.assertTrue(s.select_one('sub'));self.assertTrue(s.select_one('sup'))
        self.assertEqual(text.count('[IMAGE]'),1);self.assertLess(text.index('[IMAGE]'),text.index('History and note.'))

    def test_substantive_parents_appendix_and_final_body(self):
        rows=self.got['records'];self.assertIn('parent shall apply',rows[0]['full_text'])
        self.assertIn('Parent introduction',rows[1]['full_text'])
        self.assertIn('Last paragraph survives',rows[3]['full_text'])
        self.assertEqual(rows[4]['section_number'],'');self.assertIn('Appendix text',rows[4]['full_text'])

    def test_all_heading_dispositions_and_status(self):
        self.assertEqual(len(self.got['nodes']),7)
        dispositions=self.got['dispositions']
        self.assertEqual(dispositions[-2]['disposition'],'reserved_or_repealed')
        self.assertEqual(dispositions[-1]['disposition'],'unresolved')
        self.assertEqual(self.got['nodes'][2]['parent_node_id'],self.got['nodes'][1]['node_id'])

    def test_flagstaff_four_part_number_and_stable_different_anchor(self):
        raw='<main id="mainContent"><h3 id="1.01.001.0001">1-01-001-0001 TITLE:</h3><p>Text.</p></main>'
        result=cp.parse_page(raw.encode(),page(raw),snapshot())
        self.assertEqual(result['records'][0]['section_number'],'1-01-001-0001')
        self.assertTrue(result['records'][0]['source_url'].endswith('#1.01.001.0001'))

    def test_zero_heading_and_preamble_are_rejected(self):
        for raw in ['<main id="mainContent"><p>Uninventoried body.</p></main>', '<main id="mainContent"><p>Uninventoried intro.</p><h3>1-1-1 A</h3><p>B</p></main>']:
            with self.assertRaises(ValueError):cp.parse_page(raw.encode(),page(raw),snapshot())

    def test_challenge_and_wrong_selector_rejected(self):
        for raw in ['<title>Just a moment...</title><main id="mainContent"><h3>1-1-1 Fake</h3><p>Error</p></main>','<main><h3>1-1-1 Fake</h3></main>']:
            with self.assertRaises(ValueError):cp.parse_page(raw.encode(),page(raw),snapshot())


class ReplayTests(unittest.TestCase):
    def make(self,d):
        root=Path(d);(root/'raw').mkdir()
        (root/'raw/a.html').write_text(RICH)
        q=page(url=ROOT+'#!/Renton01/Renton0102.html');q['path']='raw/b.html'
        (root/'raw/b.html').write_text(RICH)
        s=snapshot([page(),q]);cp.save(root/'snapshot.json',s)
        return root,s

    def test_clean_interrupted_resume_and_contract(self):
        with tempfile.TemporaryDirectory() as d:
            root,s=self.make(d);checkpoint=root/'checkpoint.json'
            self.assertEqual(cp.replay(root/'snapshot.json',root/'resume',checkpoint,1)['status'],'interrupted')
            resumed=cp.replay(root/'snapshot.json',root/'resume',checkpoint)
            clean=cp.replay(root/'snapshot.json',root/'clean')
            self.assertEqual(resumed,clean)
            for f in ['aggregate-fulltext.json','aggregate-fulltext.csv','source-nodes.jsonl','record-provenance.jsonl','node-dispositions.jsonl']:
                self.assertEqual((root/'resume'/f).read_bytes(),(root/'clean'/f).read_bytes())
            self.assertFalse(clean['whole_corpus_complete']);self.assertTrue(clean['csv_json_equal'])

    def test_changed_snapshot_rejects_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            root,s=self.make(d);checkpoint=root/'cp.json';cp.replay(root/'snapshot.json',root/'out',checkpoint,1)
            s['snapshot_id']='different-edition';cp.save(root/'snapshot.json',s)
            with self.assertRaisesRegex(ValueError,'binding'):cp.replay(root/'snapshot.json',root/'out',checkpoint)

    def test_config_change_rejects_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            root,s=self.make(d);checkpoint=root/'cp.json';cp.replay(root/'snapshot.json',root/'out',checkpoint,1)
            s['pages'][0]['content_selector']='main';cp.save(root/'snapshot.json',s)
            with self.assertRaisesRegex(ValueError,'binding'):cp.replay(root/'snapshot.json',root/'out',checkpoint)

    def test_tampered_already_processed_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root,s=self.make(d);checkpoint=root/'cp.json';cp.replay(root/'snapshot.json',root/'out',checkpoint,1)
            (root/'raw/a.html').write_text(RICH+'tamper')
            with self.assertRaisesRegex(ValueError,'hash'):cp.replay(root/'snapshot.json',root/'out',checkpoint)

    def test_same_node_acquisition_twice_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root,s=self.make(d);s['pages'][1]['url']=s['pages'][0]['url']+'#another-anchor';cp.save(root/'snapshot.json',s)
            with self.assertRaisesRegex(ValueError,'duplicate'):cp.replay(root/'snapshot.json',root/'out')

    def test_same_printed_number_different_publications_survives(self):
        with tempfile.TemporaryDirectory() as d:
            root,s=self.make(d);s['pages'][1]['publication_id']='charter'
            s['publications'].append({'publication_id':'charter','scope_decision':'fixture'})
            cp.save(root/'snapshot.json',s);got=cp.replay(root/'snapshot.json',root/'out')
            self.assertEqual(got['records'],10)
            p=[json.loads(x) for x in (root/'out/record-provenance.jsonl').read_text().splitlines()]
            self.assertEqual(len({x['record_id'] for x in p}),10)


class RetainedActualSourceTests(unittest.TestCase):
    def test_all_seven_retained_chapters_inventory_and_every_body_paragraph(self):
        expected={'flagstaff-az':5,'foster-city-ca':7,'fremont-ca':11,'san-carlos-ca':10,'burien-wa':6,'renton-wa':1,'seatac-wa':12}
        for slug,count in expected.items():
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as d:
                src=HERE/slug/'historical';s=json.loads((src/'snapshot.json').read_text());p=s['pages'][0]
                raw=(src/p['path']).read_bytes();soup=BeautifulSoup(raw,'html.parser')
                # Independent chapter TOC is retained separately from body headings; compare its anchors.
                toc_anchors={a['href'].split('#')[-1] for a in soup.select('#mainContent .CiteTOC a[href]')}
                actual=cp.parse_page(raw,p,s)
                section_ids={n['locator']['value'] for n in actual['nodes'] if n['node_kind']=='section'}
                self.assertEqual(toc_anchors,section_ids)
                self.assertEqual(len(actual['records']),count)
                result=cp.replay(src/'snapshot.json',Path(d)/'out')
                self.assertEqual(result['records'],count)
                # Every direct source legal paragraph occurs in the delivered text; no arbitrary truncation.
                combined=' '.join(cp.plain(row['full_text']) for row in actual['records'])
                normalize=lambda text:' '.join(text.split())
                for el in soup.select('#mainContent p[class^="P"]'):
                    self.assertIn(normalize(el.get_text()),normalize(combined))
                self.assertNotIn('Sections:',combined)
                self.assertEqual(len({x['node_id'] for x in actual['nodes']}),len(actual['nodes']))


class AdditionalContractTests(unittest.TestCase):
    def test_display_publication_and_hierarchy(self):
        spec=page();s=snapshot();s['publications'][0]['title']='Renton Municipal Code'
        got=cp.parse_page(RICH.encode(),spec,s)
        self.assertEqual(got['records'][2]['code_name'],'Renton Municipal Code')
        self.assertEqual(got['records'][2]['title'],'Title I ADMINISTRATIVE')
        self.assertEqual(got['records'][2]['chapter'],'Chapter 1 Introductory rules')
        self.assertIsNone(got['nodes'][0]['source_version'])
        self.assertEqual(got['nodes'][0]['snapshot_id'],'fixture-immutable')

    def test_migration_notice_not_legal_text(self):
        raw='<main id="mainContent"><h1>FOSTER CITY MUNICIPAL CODE</h1><p>Your municipal code is now hosted on the eCode360 platform and can be viewed here:</p><a href="https://ecode360.com/FO4449">Current code</a></main>'
        with self.assertRaisesRegex(ValueError,'migration'):cp.parse_page(raw.encode(),page(raw),snapshot())

    def test_contents_page_cannot_emit_provision(self):
        raw='<main id="mainContent"><h1>Title I ADMINISTRATIVE</h1><div class="TitleTOC_outer"><table><tr><td>1</td><td>Seal</td></tr></table></div></main>'
        with self.assertRaisesRegex(ValueError,'navigation'):cp.parse_page(raw.encode(),page(raw),snapshot())

    def test_matching_route_but_stale_body_is_rejected(self):
        spec=page();spec['expected_heading_id']='missing-current-section'
        with self.assertRaisesRegex(ValueError,'stale'):cp.parse_page(RICH.encode(),spec,snapshot())

    def test_named_anchor_locator(self):
        raw='<main id="mainContent"><h3><a name="source-anchor"></a>1-1-1 Title.</h3><p>Body.</p></main>'
        got=cp.parse_page(raw.encode(),page(raw),snapshot())
        self.assertEqual(got['nodes'][0]['locator'],{'kind':'html-anchor-name','value':'source-anchor'})

    def test_all_seven_observed_navigation_rendered_imports(self):
        for route in json.loads((HERE/'routes.json').read_text()):
            with self.subTest(slug=route['slug']),tempfile.TemporaryDirectory() as d:
                plan=HERE/route['slug']/'historical/acquisition-plan.json'
                got=cp.acquire(plan,Path(d)/'acquired')
                self.assertEqual(got['pages'],1)
                replay=cp.replay(Path(d)/'acquired/snapshot.json',Path(d)/'out')
                self.assertGreater(replay['records'],0)
                self.assertFalse(replay['whole_corpus_complete'])

    def test_stale_rendered_route_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'raw').mkdir()
            nav='<a href="#!/a.html">Chapter 1</a>'
            (root/'raw/nav.html').write_text(nav);(root/'raw/a.html').write_text(RICH)
            plan=snapshot();plan['pages']=[dict(page(url=ROOT+'#!/a.html'),navigation_evidence={
                'path':'raw/nav.html','url':ROOT,'sha256':cp.digest(nav.encode())},rendered_artifact={
                'path':'raw/a.html','sha256':cp.digest(RICH.encode()),'rendered_url':ROOT+'#!/stale.html','retrieved_at':'2026-10-15'})]
            cp.save(root/'plan.json',plan)
            with self.assertRaisesRegex(ValueError,'rendered route'):cp.acquire(root/'plan.json',root/'out')

if __name__=='__main__':unittest.main(verbosity=2)
