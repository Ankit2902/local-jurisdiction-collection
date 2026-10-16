import copy, json, tempfile, unittest
from pathlib import Path
from bs4 import BeautifulSoup
import cp_collect as cp
import validate_e2e as e2e
HERE=Path(__file__).resolve().parent
class CurrentSourceTests(unittest.TestCase):
    def test_every_current_capture_integrity(self):
        total=0
        for p in (HERE/'current-cua').glob('*/*.receipt.json'):
            r=json.loads(p.read_text())
            if r.get('accepted') and r.get('browser_state',{}).get('sha256'):
                e2e.receipt(HERE/'current-cua',p.parent.name,p.name.replace('.receipt.json',''));total+=1
        self.assertGreaterEqual(total,35)
    def test_receipt_raw_mutation_fails_closed(self):
        p=HERE/'current-cua/fremont-ca/chapter.receipt.json';r=json.loads(p.read_text())
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'fremont-ca';dest.mkdir();(dest/p.name).write_text(json.dumps(r));(dest/r['raw_artifact_path']).write_text('changed')
            with self.assertRaisesRegex(ValueError,'raw hash'):e2e.receipt(Path(d),'fremont-ca','chapter')
    def test_version_unknown_changed_and_unbracketed_fail(self):
        def r(label,start,finish):return {'browser_state':{'currency':label},'started_at':start,'finished_at':finish}
        a,b,c=r('Known','1','2'),r('Known','3','4'),r('Known','5','6')
        self.assertEqual(e2e.compare_markers(a,b,c),'Known')
        for bad in [r('Changed','5','6'),r('','5','6'),r('Known','0','1')]:
            with self.assertRaises(ValueError):e2e.compare_markers(a,b,bad)
    def test_real_supplementary_table_heading_and_structure(self):
        path=HERE/'current-cua/fremont-ca/cross-reference-table.html';raw=path.read_bytes();url='https://www.codepublishing.com/CA/Fremont/#!/FremontCR.html'
        page={'url':url,'path':'raw/table.html','sha256':cp.digest(raw),'publication_id':'city-code','content_selector':'#mainContent','expected_heading_id':'CR'}
        s={'jurisdiction_slug':'fremont-ca','jurisdiction':'Fremont','snapshot_id':'current-table-unit','publications':[{'publication_id':'city-code','title':'Fremont Municipal Code'}]}
        parsed=cp.parse_page(raw,page,s);self.assertEqual(len(parsed['records']),1)
        result=e2e.audit(raw,parsed['records'],True);self.assertEqual(result['structure_counts']['table'],1);self.assertEqual(result['structure_counts']['tr'],2212);self.assertEqual(result['structure_counts']['td'],4422)
        self.assertEqual(parsed['records'][0]['section_number'],'');self.assertEqual(parsed['nodes'][0]['locator'],{'kind':'html-id','value':'CR'})
        with self.assertRaisesRegex(ValueError,'stale rendered'):cp.parse_page(raw,dict(page,expected_heading_id='not-present'),s)
    def test_nested_styled_hidden_elements(self):
        raw='<main id="mainContent"><h1 id="CR">Table</h1><div style="display:none"><span style="color:red">Hidden</span></div><table><tr><td>Kept</td></tr></table></main>'
        node=cp.content(raw,'#mainContent');self.assertNotIn('Hidden',str(node));self.assertIn('Kept',str(node))
    def test_current_migration_roots_fail_parser(self):
        for slug,name in [('seatac-wa','root-confirmed'),('foster-city-ca','municipal-migration')]:
            with self.assertRaisesRegex(ValueError,'migration'):cp.content((HERE/'current-cua'/slug/(name+'.html')).read_text(),'#mainContent')
if __name__=='__main__':unittest.main()
