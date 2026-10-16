"""Offline failure-path regressions for live orchestration safeguards."""
import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from archive_includes import ArchiveIncludes,safe_reference,assert_metadata_only_index
from e2e import drift_check,verify_capture,docx_text
from common import sha
class E2ETests(unittest.TestCase):
    def archive(self,root,files):
        commit='a'*40;p=root/'archive.zip';tree={'tree':[]}
        with zipfile.ZipFile(p,'w') as z:
            for name,data in files.items():
                z.writestr('law-xml-'+commit+'/'+name,data);tree['tree'].append({'type':'blob','path':name,'sha':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
        return p,tree,commit
    def test_bounded_include_closure_and_exclusion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,t,c=self.archive(root,{'index.xml':b'<document xmlns:xi="http://www.w3.org/2001/XInclude"><heading>Code</heading><meta><effective>unknown</effective></meta><xi:include href="title/1.xml"/><xi:include href="title/2.xml"/></document>','title/1.xml':b'<container><text>one</text></container>','title/2.xml':b'<container><text>two</text></container>'})
            a=ArchiveIncludes(p,t,c);r=a.resolve('index.xml',{'index.xml','title/1.xml'});self.assertEqual([x['path'] for x in r['units']],['title/1.xml']);self.assertEqual(r['include_edges'][1]['disposition'],'excluded_validation_scope');self.assertEqual(a.verified_members,3)
    def test_mixed_parent_content_rejected_not_lost(self):
        r=ET.fromstring('<document xmlns:xi="http://www.w3.org/2001/XInclude"><text>Operative parent law</text><xi:include href="1.xml"/></document>')
        with self.assertRaisesRegex(ValueError,'Mixed own-body'):assert_metadata_only_index(r)
    def test_cycle_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p,t,c=self.archive(Path(d),{'index.xml':b'<document xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="index.xml"/></document>'})
            with self.assertRaisesRegex(ValueError,'cycle'):ArchiveIncludes(p,t,c).resolve('index.xml',{'index.xml'})
    def test_git_blob_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            p,t,c=self.archive(Path(d),{'index.xml':b'<document/>'});t['tree'][0]['sha']='f'*40
            with self.assertRaisesRegex(ValueError,'Git blob mismatch'):ArchiveIncludes(p,t,c)
    def test_unsafe_include(self):
        for ref in ['../../outside.xml','https://example.org/a.xml','/absolute.xml','a.xml#part']:
            with self.assertRaises(ValueError):safe_reference('title/index.xml',ref)
    def test_missing_selected_include(self):
        with tempfile.TemporaryDirectory() as d:
            p,t,c=self.archive(Path(d),{'index.xml':b'<document xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="missing.xml"/></document>'})
            with self.assertRaisesRegex(ValueError,'Selected include missing'):ArchiveIncludes(p,t,c).resolve('index.xml',{'index.xml','missing.xml'})
    def test_latest_drift_rejected(self):
        self.assertTrue(drift_check({'version':1},{'Id':'a'},{'version':1},{'Id':'a'})['tree_json_equal'])
        with self.assertRaisesRegex(ValueError,'drift'):drift_check({'version':1},{'Id':'a'},{'version':2},{'Id':'a'})
        with self.assertRaisesRegex(ValueError,'drift'):drift_check({'version':1},{'Id':'a'},{'version':1},{'Id':'b'})
    def test_word_runs_joined_before_paragraphs(self):
        import io
        content=b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>1.16.</w:t></w:r><w:r><w:t>0110</w:t></w:r></w:p><w:p><w:r><w:t>UPDATED: January 10, 2023</w:t></w:r></w:p></w:body></w:document>'
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:z.writestr('word/document.xml',content)
        self.assertEqual(docx_text(stream.getvalue()),'1.16.0110\nUPDATED: January 10, 2023')
    def test_tampered_capture_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'capture.html';p.write_bytes(b'original');Path(str(p)+'.capture.json').write_text(json.dumps({'sha256':sha(b'original'),'bytes':8}));verify_capture(p);p.write_bytes(b'modified')
            with self.assertRaisesRegex(ValueError,'receipt mismatch'):verify_capture(p)
if __name__=='__main__':unittest.main()
