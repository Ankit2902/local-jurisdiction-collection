import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import discover
from inspect_pdf import inspect
from qualify_charter import parse
class Response:
    def __init__(self,status=200,data=b'body',headers=None):self.status_code=status;self.data=data;self.headers=headers or {};self.url='https://city.example/source';self.history=[]
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_content(self,n):yield self.data
class DiscoveryTests(unittest.TestCase):
    def test_redirect_retained_without_follow(self):
        with tempfile.TemporaryDirectory() as d,patch('discover.requests.get',return_value=Response(302,b'',{'Location':'https://ecode360.com/AA1000'})) as request:
            r=discover.get('https://city.example/source',Path(d)/'source');self.assertEqual(r['status'],'failed');self.assertIn('not followed',r['error']);self.assertFalse(request.call_args.kwargs['allow_redirects']);self.assertEqual(request.call_count,1)
    def test_empty_200_is_failure(self):
        with tempfile.TemporaryDirectory() as d,patch('discover.requests.get',return_value=Response(200,b'')):
            r=discover.get('https://city.example/source',Path(d)/'source');self.assertEqual(r['status'],'failed');self.assertIn('Empty HTTP200',r['error'])
    def test_publisher_probes_disabled(self):
        with self.assertRaisesRegex(ValueError,'disabled'):discover.get('https://ecode360.com/AA1000','unused')
    def test_html_error_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'false.pdf';p.write_bytes(b'<html>denied</html>')
            with self.assertRaisesRegex(ValueError,'not original PDF'):inspect(p)
    def test_byte_limit_rejected(self):
        with tempfile.TemporaryDirectory() as d,patch('discover.requests.get',return_value=Response(200,b'toolarge')):
            r=discover.get('https://city.example/source',Path(d)/'source',3);self.assertEqual(r['status'],'failed');self.assertIn('byte limit',r['error'])
    def test_charter_source_inventory_and_no_operative_omission(self):
        root=Path(__file__).resolve().parent;data=(root/'discovery-current/emeryville-ca/1.html').read_bytes();rows,nodes,prov=parse(data)
        self.assertEqual([r['section_number'] for r in rows],['100','200']);self.assertEqual(len(nodes),8);self.assertEqual(sum(n['disposition']=='included_sample' for n in nodes),2);self.assertEqual(len(prov),2)
        modified=data.replace(b'<p><strong>Section 100.',b'<p>Additional operative content</p><p><strong>Section 100.',1)
        with self.assertRaisesRegex(ValueError,'Unprofiled operative'):parse(modified)
    def test_received_pdf_counts_and_ocr_status(self):
        root=Path(__file__).resolve().parent
        if not (root/'downloads/santa-clara-current-charter.pdf').exists():self.skipTest('retained live sample absent')
        r=inspect(root/'downloads/santa-clara-current-charter.pdf');self.assertEqual(r['pages'],29);self.assertEqual(r['text_status'],'ocr_required')
        r=inspect(root/'downloads/emeryville-title8.pdf');self.assertEqual(r['pages'],41);self.assertIn('22-013',r['selected_pages'][0]['text'])
if __name__=='__main__':unittest.main()
