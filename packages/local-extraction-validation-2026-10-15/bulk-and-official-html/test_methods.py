from __future__ import annotations
import json,tempfile,unittest,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
from common import decode,readable,semantic,checkpoint,sha,resume_units
from san_mateo import parse_xml,publication_inventory
from king_county import parse_title,landing_inventory
from daly_city import parse_elaws,parse_content,inventory,route_evidence
BASE=Path(__file__).resolve().parent
RAW=BASE/'raw'

class SemanticTests(unittest.TestCase):
    def test_once_nested_list_spans_notes_images(self):
        s=BeautifulSoup('<div><ol><li><p>FIRST</p><ol><li>SECOND</li></ol></li></ol><table><tr><th colspan="2">HEADER</th></tr><tr><td rowspan="2">A</td><td>B<sup>2</sup></td></tr></table><img src="a.png"/><p>END</p></div>','html.parser')
        html=semantic(s.div);text=readable(html)
        self.assertEqual(text.count('FIRST'),1);self.assertEqual(text.count('SECOND'),1);self.assertIn('colspan="2"',text);self.assertIn('rowspan="2"',text);self.assertIn('<sup>2</sup>',text);self.assertLess(text.index('[IMAGE]'),text.index('END'))
    def test_cp1252_and_utf8(self):
        for data in [b'<meta charset="iso-8859-1"><p>Words \x96 words \x97</p>','<p>Words – words —</p>'.encode()]:
            t,e=decode(data);self.assertIn('–',t);self.assertNotRegex(t,'[\x80-\x9f]')
    def test_reject_c1(self):
        with self.assertRaises(ValueError):decode('<p>bad\u0096</p>'.encode())
    def test_interrupted_real_xml_replay_matches_clean(self):
        units=[(name,lambda name=name:parse_xml((RAW/name).read_bytes(),'https://example/'+name,scrape_date='2026-10-15')) for name in ['san-title1.bin','san-charter.bin']]
        binding={'parser':'bulk-official-html-1','source_hashes':[sha((RAW/n).read_bytes()) for n in ['san-title1.bin','san-charter.bin']],'config':{'scrape_date':'2026-10-15'}}
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            state=Path(temp)/'resume.json'
            with self.assertRaises(InterruptedError):resume_units(units,state,binding,stop_after=1)
            resumed=resume_units(units,state,binding)
            clean=resume_units(units,Path(temp)/'clean.json',binding)
            self.assertEqual(resumed,clean)
    def test_checkpoint_binding(self):
        with tempfile.TemporaryDirectory(dir=BASE) as t:
            p=Path(t)/'state.json';checkpoint(p,{'version':'a','raw':'hash'},['x']);checkpoint(p,{'version':'a','raw':'hash'},['x','y'])
            with self.assertRaises(ValueError):checkpoint(p,{'version':'b','raw':'hash'},[])

class XmlTests(unittest.TestCase):
    def test_nested_sections_and_parent_bodies_and_identity(self):
        data=b'<container xmlns="urn:law" id="t"><prefix>Title</prefix><num>1</num><text>INTRO</text><section id="p"><num>1.1</num><heading>Parent</heading><text>OWN</text><para><num>(a)</num><text>A</text></para><section id="c"><num>1.1</num><heading>Child</heading><text>CHILD</text></section></section></container>'
        r=parse_xml(data,'https://example/title.xml',version='a',scrape_date='2000-01-01')
        self.assertEqual(len(r['rows']),3);self.assertNotIn('CHILD',r['rows'][1]['full_text']);self.assertIn('(a)',r['rows'][1]['full_text']);self.assertEqual(len({n['node_id'] for n in r['nodes']}),3);self.assertEqual(r['nodes'][1]['source_attributes']['id'],'p');self.assertEqual(r['rows'][0]['scrape_date'],'2000-01-01')
    def test_include_explicit_unresolved(self):
        r=parse_xml(b'<container xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="child.xml"/></container>','https://example/index.xml')
        self.assertEqual(r['dispositions'][0]['disposition'],'unresolved')
    def test_reject_entity(self):
        with self.assertRaises(ValueError):parse_xml(b'<!DOCTYPE x [<!ENTITY f SYSTEM "file:///etc/passwd">]><section/>','x')
    def test_live_retained_lists_table_and_charter(self):
        r=parse_xml((RAW/'san-title1.bin').read_bytes(),'https://example/1.xml');row=next(x for x in r['rows'] if x['section_number']=='1.01.030')
        self.assertIn('(k)',row['full_text']);self.assertIn('Written',row['full_text']);self.assertTrue(any('<table' in x['full_text'] for x in r['rows']))
        c=parse_xml((RAW/'san-charter.bin').read_bytes(),'https://example/charter.xml',publication='charter');self.assertEqual(len([n for n in c['nodes'] if n['node_kind']=='section']),96)
    def test_repository_inventory(self):
        t=json.loads((RAW/'san-tree.bin').read_bytes());families=publication_inventory(t,'a');self.assertEqual({f['publication_id'] for f in families},{'municipal-code','charter','drafting-manual','editorial-actions','ordinances'})
        with self.assertRaises(ValueError):publication_inventory(dict(t,truncated=True),'a')

class KingTests(unittest.TestCase):
    def test_r05_complete_range_and_real_anchor_alphanumeric(self):
        data=b'<html><body><p>2A.01.010 Navigation</p><div><p><a name="actual"></a><b>2A.01.010 Heading.</b></p><p>BODY SURVIVES</p><table><tr><td>TABLE SURVIVES</td></tr></table><p><b>2A.01.020 Next.</b>STOP</p></div></body></html>'
        r=parse_title(data,'https://example/title.htm');self.assertEqual(len(r['rows']),2);self.assertIn('BODY SURVIVES',r['rows'][0]['full_text']);self.assertIn('TABLE SURVIVES',r['rows'][0]['full_text']);self.assertNotIn('STOP',r['rows'][0]['full_text']);self.assertEqual(r['rows'][0]['source_url'],'https://example/title.htm#actual');self.assertEqual(r['rows'][1]['source_url'],'https://example/title.htm')
    def test_repeated_printed_number_retains_distinct_source_nodes(self):
        r=parse_title(b'<p><b>1.01.010 First version.</b>A</p><p><b>1.01.010 Second version.</b>B</p>','https://example/title.htm')
        self.assertEqual(len(r['rows']),2);self.assertNotEqual(r['nodes'][0]['node_id'],r['nodes'][1]['node_id'])
    def test_split_bold_number_heading(self):
        r=parse_title(b'<p><b> </b><b>21A.06.333A </b><b>Dredging.</b>BODY</p>','https://example/title.htm');self.assertEqual(r['rows'][0]['section_number'],'21A.06.333A');self.assertEqual(r['rows'][0]['section_name'],'Dredging.')
    def test_truncated_capture_rejected(self):
        with self.assertRaises(ValueError):parse_title(b'<p>BODY[Truncated]','x')
    def test_charter_preamble_and_subsections(self):
        r=parse_title(b'<h1>PREAMBLE</h1><p>WE THE PEOPLE</p><h1>ARTICLE 1</h1><p><b>Section 110 General.</b></p><p>OWN</p><p><b>110.10 Detail.</b></p><p>DETAIL</p>','https://example/charter.htm',True)
        self.assertEqual([x['section_number'] for x in r['rows']],['','110','110.10']);self.assertNotIn('DETAIL',r['rows'][1]['full_text'])
    def test_live_retained_body_and_publication_inventory(self):
        r=parse_title((RAW/'king-title1.dom.html').read_bytes(),'https://example/title1.htm');d=next(x for x in r['rows'] if x['section_number']=='1.02.030');self.assertIn('"Written"',d['full_text']) if '"Written"' in d['full_text'] else self.assertIn('"Person"',d['full_text']);self.assertIn('state of Washington',d['full_text'])
        inv=landing_inventory((RAW/'king-landing.dom.html').read_text(),'https://kingcounty.gov/code');self.assertTrue(any(x['kind']=='charter' for x in inv['documents']));self.assertTrue(any('Title 2A:' in x['label'] for x in inv['documents']));self.assertTrue(inv['related_publications'])

class DalyTests(unittest.TestCase):
    def test_historical_elaws_identity_repair_and_no_url_guess(self):
        h='<h1>1.01.010 - Adoption.</h1><div class="Daly City_content"><p>Pursuant to the provisions.</p></div>';url='https://dalycity-ca.elaws.us/code/coor_title1_ch1.01_sec1.01.010'
        self.assertEqual(parse_elaws(h,url)['section_number'],'1.01.010')
        with self.assertRaises(ValueError):parse_elaws(h.replace('<h1>1.01.010 - Adoption.</h1>',''),url)
        with self.assertRaises(ValueError):parse_elaws('<h1>Access denied</h1>',url)
    def test_current_route_and_requested_node(self):
        route=route_evidence((RAW/'daly-city.dom.html').read_text());self.assertTrue(any('library.municode.com' in x['url'] for x in route))
        inv=inventory(json.loads((RAW/'daly-toc.json').read_bytes()));node=next(n for n in inv if n['display_heading']=='1.01.010 - Adoption.');data=(RAW/'daly-content-0.json').read_bytes();row,n,d,p=parse_content(json.loads(data),node,data);self.assertEqual(row['section_number'],'1.01.010');self.assertIn('Pursuant to',row['full_text']);self.assertNotIn('1.01.020',row['full_text'])
        with self.assertRaises(ValueError):parse_content({'Docs':[]},node,b'{}')
    def test_content_heading_drift(self):
        n={'node_id':'x','display_heading':'1.01.010 - Adoption.'};p={'Docs':[{'Id':'x','Title':'1.01.020 - Other.'}]}
        with self.assertRaises(ValueError):parse_content(p,n,b'{}')
    def test_duplicate_toc_node_rejected(self):
        with self.assertRaises(ValueError):inventory({'Id':'r','Children':[{'Id':'a'},{'Id':'a'}]})

class PortableCliTests(unittest.TestCase):
    def test_xml_cli_input_outside_output_parent(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            out=Path(temp)/'replay';result=subprocess.run([sys.executable,str(BASE/'san_mateo.py'),'parse','--input',str(RAW/'san-title1.bin'),'--source-url','https://example/title.xml','--commit','a'*40,'--out',str(out),'--scrape-date','2000-01-01'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);m=json.loads((out/'run-manifest.json').read_text());self.assertTrue((out/m['raw_artifacts'][0]['path']).is_file());self.assertEqual(json.loads((out/'aggregate-fulltext.json').read_text())['provisions'][0]['scrape_date'],'2000-01-01')
if __name__=='__main__':unittest.main()
