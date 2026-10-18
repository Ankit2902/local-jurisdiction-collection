"""Offline marker fidelity and observed-response guards; no publisher requests."""
import copy,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import Mock,patch
from bs4 import BeautifulSoup
from collectors.gridics.model import normalize,native_records,stylesheet_evidence,digest,Invalid
from collectors.gridics.source_response import response_role,read_nonimage_response

BASE='https://codehub.gridics.com/us/fl/miami'

class ListFidelityTests(unittest.TestCase):
    def test_custom_marker_classes_are_preserved_and_never_guessed(self):
        for cls in ['paren-value-paren','value-paren','style-square','default-style']:
            value=normalize('<ol class="'+cls+'" start="3"><li>Source text</li></ol>',BASE)
            self.assertIn('class="'+cls+'"',value['html'])
            self.assertEqual(value['text'],'Source text')
            self.assertFalse(value['lists'][0]['marker_format_qualified'])
            self.assertEqual(value['lists'][0]['source_attributes']['class'],[cls])
            self.assertEqual(value['lists'][0]['items'][0]['counter_value'],3)

    def test_declared_nonnumeric_square_never_becomes_decimal(self):
        value=normalize('<ol style="list-style-type:square"><li>First</li><li>Second</li></ol>',BASE)
        self.assertEqual(value['text'],'▪ First\n▪ Second')
        self.assertTrue(value['lists'][0]['marker_format_qualified'])
        self.assertNotIn('1.',value['text'])
        self.assertEqual(normalize('<ul type="circle"><li>Circle</li></ul>',BASE)['text'],'◦ Circle')
        self.assertEqual(normalize('<ol style="list-style-type:none"><li>Unmarked</li></ol>',BASE)['text'],'Unmarked')

    def test_standard_counter_semantics_and_nested_lists(self):
        value=normalize('<ol reversed start="5" type="A"><li>Five<ol start="2"><li>Inner</li></ol></li><li value="2">Two</li></ol>',BASE)
        self.assertEqual(value['text'],'E. Five\n2. Inner\nB. Two')
        self.assertEqual([v['counter_value'] for v in value['lists'][0]['items']],[5,2])

    def test_per_item_custom_format_and_invalid_counter_never_invent_marker(self):
        for markup in ['<ol><li class="special">Text</li></ol>','<ol start="bogus"><li>Text</li></ol>','<ol><li value="no">Text</li></ol>','<ol style="list-style:custom"><li>Text</li></ol>','<ul type="invented"><li>Text</li></ul>','<ol><li type="A">Text</li></ol>']:
            value=normalize(markup,BASE)
            self.assertFalse(value['lists'][0]['marker_format_qualified'])
            self.assertEqual(value['text'],'Text')

    def test_image_styles_keep_placeholder_without_metadata_payload(self):
        value=normalize('<ol style="list-style-image:url(data:image/png;base64,SECRET_PIXELS)"><li>Caption</li></ol>',BASE)
        self.assertEqual(value['text'],'[IMAGE]\nCaption')
        self.assertNotIn('SECRET_PIXELS',json.dumps(value))
        self.assertNotIn('<img',value['html'])
        self.assertFalse(value['lists'][0]['marker_format_qualified'])

    def test_custom_marker_keeps_publication_unqualified(self):
        node={'id':'r','path':'/r','docId':'94','text':'Heading','li_attr':{'dataTag':'section','tag':'h2'},'children':[{'id':'b','path':'/r/b','docId':'94','ref':{'parent':'r'},'li_attr':{'dataTag':'BodyM'},'text':'<ol class="value-paren"><li>Text</li></ol>'}]}
        record=native_records([node],{'document_id':'94','source_url':BASE},'/r')[0][0]
        self.assertEqual(record['disposition'],'source_unqualified')
        self.assertIn('list marker',record['source_qualification_errors'][0])
        self.assertEqual(record['body_block_ids'],['b'])

    def test_actual_full_miami_root_retains_source_classes_and_item_order(self):
        fixture=Path(__file__).resolve().parents[1]/'fixtures'
        meta=json.loads((fixture/'miami-list-boundaries-provenance.json').read_text())
        with zipfile.ZipFile(fixture/'miami-list-boundaries.zip') as archive:
            raw=archive.read('native.json')
        self.assertEqual(digest(raw),meta['files']['native.json']['sha256'])
        tree=json.loads(raw);records,_=native_records(tree,meta['config'],meta['source_root']['root']['path'])
        nodes={}
        def walk(n):
            nodes[n['id']]=n
            for c in n.get('children',[]):walk(c)
        walk(tree[0]);classed=0
        for rec in records:
            markup=''.join(nodes[b]['text'] for b in rec['body_block_ids'])
            lists=BeautifulSoup(markup,'html.parser').find_all(['ol','ul'])
            self.assertEqual(len(rec['lists']),len(lists))
            sanitized=BeautifulSoup(rec['html'],'html.parser').find_all(['ol','ul'])
            self.assertEqual(len(sanitized),len(lists))
            for source,out,row in zip(lists,sanitized,rec['lists']):
                self.assertEqual(source.get('class',[]),out.get('class',[]))
                self.assertEqual([li.get_text() for li in source.find_all('li',recursive=False)],[li.get_text() for li in out.find_all('li',recursive=False)])
                if source.get('class'):
                    classed+=1;self.assertFalse(row['marker_format_qualified'])
        self.assertGreater(classed,0)

class ObservedStylesheetTests(unittest.TestCase):
    def test_selection_is_only_observed_first_party_stylesheet(self):
        self.assertEqual(response_role(BASE+'/build/css/gridics.css?tmudor','stylesheet'),'stylesheet')
        for url,kind in [('https://external.invalid/gridics.css','stylesheet'),(BASE+'/image.png','image'),('http://codehub.gridics.com/gridics.css','stylesheet')]:
            self.assertIsNone(response_role(url,kind))

    def test_actual_observed_stylesheet_locators_without_fetching(self):
        fixture=Path(__file__).resolve().parents[1]/'fixtures'
        raw=(fixture/'miami-observed-stylesheet-document.html').read_bytes()
        meta=json.loads((fixture/'miami-observed-stylesheet-document-provenance.json').read_text())
        self.assertEqual(digest(raw),meta['sha256'])
        soup=BeautifulSoup(raw,'html.parser')
        hrefs=[link['href'] for link in soup.select('link[rel="stylesheet"][href]')]
        self.assertIn('/build/css/gridics.css?tmudor',hrefs)
        from urllib.parse import urljoin
        with patch('socket.socket',side_effect=AssertionError('NETWORK')):
            for href in hrefs:
                url=urljoin('https://codehub.gridics.com/us/fl/miami-comp',href)
                if url.startswith('https://codehub.gridics.com/'):
                    self.assertEqual(response_role(url,'stylesheet'),'stylesheet')

    def test_image_mime_is_rejected_without_reading_body(self):
        response=Mock(headers={'content-type':'image/png'});response.body.side_effect=AssertionError('IMAGE BODY READ')
        raw,reason=read_nonimage_response(response)
        self.assertIsNone(raw);response.body.assert_not_called()

    def test_mislabeled_image_has_no_persistable_body(self):
        response=Mock(headers={'content-type':'text/css'});response.body.return_value=b'\x89PNG\r\n\x1a\nbytes'
        self.assertIsNone(read_nonimage_response(response)[0])

    def test_original_css_kept_without_resource_traversal(self):
        raw=b'ol.square {list-style-type:square} .logo {background:url(image.png)}'
        response=Mock(headers={'content-type':'text/css'});response.body.return_value=raw
        with patch('socket.socket',side_effect=AssertionError('NETWORK')):
            self.assertEqual(read_nonimage_response(response),(raw,None))
        response.body.assert_called_once()

    def test_css_receipt_phase_url_hash_and_owner_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp);raw=b'ol.custom{list-style-type:square}'
            (path/'css.bin').write_bytes(raw)
            receipt={'path':'css.bin','sha256':digest(raw),'bytes':len(raw),'status':200,'url':'https://codehub.gridics.com/build/css/gridics.css?tmudor','content_type':'text/css; charset=utf-8','phase':'start','epoch':'one','at':'2026-10-17T20:00:00+00:00','resource_type':'stylesheet','response_role':'stylesheet','source_document_url':BASE+'#/root'}
            phases=[{'phase':'start','roots_response':{'epoch':'one'}},{'phase':'end','roots_response':{'epoch':'two'}}]
            report=stylesheet_evidence(path,[receipt],phases,{'source_url':BASE})
            self.assertTrue(report[0]['source_document_bound']);self.assertFalse(report[0]['marker_rules_interpreted'])
            self.assertEqual(report[0]['image_assets_imported'],0)
            for update in [{'epoch':'wrong'},{'url':'https://external.invalid/a.css'},{'sha256':'bad'},{'resource_type':'image'},{'content_type':'image/png'}]:
                with self.assertRaises(Invalid):stylesheet_evidence(path,[dict(receipt,**update)],phases,{'source_url':BASE})
            self.assertFalse(stylesheet_evidence(path,[dict(receipt,source_document_url=None)],phases,{'source_url':BASE})[0]['source_document_bound'])

if __name__=='__main__':unittest.main()
