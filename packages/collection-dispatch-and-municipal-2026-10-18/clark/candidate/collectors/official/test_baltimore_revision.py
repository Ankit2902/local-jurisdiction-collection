import io,pathlib,zipfile,unittest
from bs4 import BeautifulSoup
import model
B=pathlib.Path(__file__).resolve().parent
class ArchiveRevision(unittest.TestCase):
 def test_hidden_comments_and_scripts_are_not_legal_text(self):
  soup=BeautifulSoup('<p>Actual<!-- hidden editorial --> legal <span>te</span><b>xt</b>.</p><script>not operative</script>','html.parser');self.assertEqual(model.dom_text(soup),'Actual legal text.')
 def test_noncanonical_attachment_headings_and_body_are_owned(self):
  member='root/us/md/cities/baltimore/code/building-codes/II/attachments/C/index.html';out=io.BytesIO()
  with zipfile.ZipFile(out,'w') as z:z.writestr(member,(B/'fixtures/baltimore-irc-attachment-c.html').read_bytes())
  rows,proof=model.archive_records(out.getvalue(),{'jurisdiction':'Baltimore City','state':'MD','publication':'Fixture'},'fixture.zip');self.assertEqual(len(rows),1);row=rows[0]
  self.assertEqual(len(row['embedded_source_headings']),2);self.assertIn('Shade cloth or plastic film structures',row['text']);self.assertIn('Section C101.',row['text']);self.assertEqual(proof['owners'][0]['disposition'],'included')
 def test_inline_superscripts_and_blocks_keep_real_dom_boundaries(self):
  soup=BeautifulSoup('<table><tr><td>1<sup>st</sup> offense</td><td><p>Classrooms ≤10,000 ft<sup>3</sup></p><p>Next requirement</p></td></tr></table>','html.parser');r=model.semantics(soup,'https://fixture.gov/')
  self.assertEqual(r['tables'][0]['rows'][0][0]['text'],'1st offense');self.assertEqual(r['tables'][0]['rows'][0][1]['text'],'Classrooms ≤10,000 ft3 Next requirement');self.assertIn('1st offense',r['text'])
if __name__=='__main__':unittest.main(verbosity=2)
