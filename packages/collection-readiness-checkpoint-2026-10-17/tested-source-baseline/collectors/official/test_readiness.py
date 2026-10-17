#!/usr/bin/env python3
"""Compact readiness hardening tests: no network/images or old-package imports."""
import copy,hashlib,io,json,pathlib,sys,tempfile,unittest,zipfile
from unittest.mock import patch
from bs4 import BeautifulSoup
sys.dont_write_bytecode=True
import collect,model,openlaw_xml
BASE=pathlib.Path(__file__).resolve().parent
class Readiness(unittest.TestCase):
 def test_image_metadata_and_nested_cell_ownership(self):
  pixel='data:image/png;base64,UNIQUEPIXELPAYLOAD123456789'
  node=BeautifulSoup('<main><table><tr><td background="outer.png">Outer<table><tr><td style="background-image:url(inner.png)">Inner</td></tr></table></td></tr></table><source src="'+pixel+'"><object data="map.png"></object><a href="'+pixel+'" data-alt="'+pixel+'">'+pixel+'</a><input type="image" src="opaque"><iframe src="'+pixel+'"></iframe></main>','html.parser').main;result=model.semantics(node,'https://fixture.invalid/');encoded=json.dumps(result);self.assertNotIn('UNIQUEPIXELPAYLOAD123456789',encoded);self.assertNotIn('data:image/',encoded);s=BeautifulSoup(result['html'],'html.parser');self.assertIn('[IMAGE]',s.select('table table td')[0].get_text());self.assertFalse(s.select('[background],img,source,object,iframe,input[type=image]'));self.assertGreaterEqual(result['image_placeholder_count'],7);self.assertTrue(all(not a['required'] for a in result['assets'] if model.image_asset(a)))
 def test_portland_lettered_citation_prefix_and_container_notes(self):
  html=b'<main><div class="view-display-id-page_title_all"><div class="view-header">Title amended effective2026.</div></div><div class="node--embedded"><h2><a href="/code/14/a10">Chapter14A.10</a></h2><div class="field--name-field-prefix-note">Chapter note.</div></div><div class="node--embedded"><h3><a href="/code/14/a10/010">14A.10.010 Definitions.</a></h3><div class="field--name-field-prefix-note">Prefix note.</div><div class="field--name-field-section-body">Operative definition retained.</div><div class="field--name-field-suffix-note">Suffix note.</div></div><div class="node--embedded"><h3><a href="/code/14/a10/020">14A.10.020 Former tax.</a></h3><div class="field--name-field-prefix-note">Repealed by Ordinance192185.</div></div></main>'
  rows,_=model.html_records(html,{'id':'title14','url':'https://fixture.invalid/code/14/all','heading':'Title14','raw_ref':'fixture.html'},{'mode':'portland_titles','publication':'CityCode','jurisdiction':'Portland','state':'OR'});section=next(x for x in rows if x['id']=='14A.10.010');self.assertEqual(section['text'],'Prefix note. Operative definition retained. Suffix note.');self.assertEqual(next(x for x in rows if x['id']=='14A.10.020')['unit'],'legal_status');self.assertEqual(sum(r['unit']=='container_owned_body'for r in rows),2)
 def test_cache_import_only_parser_delta_and_native_download_binding(self):
  with tempfile.TemporaryDirectory()as td:
   root=pathlib.Path(td);src=root/'src';(src/'raw').mkdir(parents=True);c={'id':'fixture','mode':'pdf','source_url':'https://fixture.invalid/a.pdf'};collect.save(src/'config.json',c);collect.save(src/'checkpoint.json',{'scripts':{}});name='item:https://fixture.invalid/a.pdf';key=model.sha(name.encode())[:20];raw=src/'raw'/(key+'.bin');raw.write_bytes(b'good source bytes');meta={'request_name':name,'url':c['source_url'],'download_url':'https://fixture.invalid/wrong.pdf','status':200,'sha256':model.sha(raw.read_bytes())};collect.save(raw.with_suffix('.receipt.json'),meta);out=root/'new';(out/'raw').mkdir(parents=True);collect.seed_cache(src,out,{**c,'pdf_normalization':'coordinate-v1'});report=collect.load(out/'cache-import.json');self.assertFalse(report['imported']);self.assertEqual(len(report['skipped']),1)
   with self.assertRaises(ValueError):collect.seed_cache(src,out,{**c,'source_url':'https://fixture.invalid/other.pdf'})
 def test_exact_qualified_html_attachment_identity_and_nested_refusal(self):
  url='https://fixture.invalid/statute?id=9';rule={'url':url,'format':'html','content_selector':'#law','identity_tokens':['Article Tax Property','Section9-304'],'remove_selectors':['button']};c={'attachment_qualifications':[rule]};body=b'<div id="law"><button>Next</button>Article Tax Property Section9-304. This is actual operative State law text and the body is long enough to establish substantive content.</div>';result=model.qualify_attachment(body,url,c);self.assertNotIn('Next',result['normalized']['text'])
  with self.assertRaises(ValueError):model.qualify_attachment(body.replace(b'Section9-304',b'Section9-305'),url,c)
  with self.assertRaises(ValueError):model.qualify_attachment(body.replace(b'</div>',b' Appendix incorporated by reference <a href="other.pdf">Attachment</a></div>'),url,c)
 def test_openlaw_complete_mixed_parent_include_ownership_and_faults(self):
  files={'index.xml':b'<library xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="code/index.xml"/></library>','code/index.xml':b'<document xmlns:xi="http://www.w3.org/2001/XInclude"><heading>Whole Code</heading><text>Before child.</text><xi:include href="one.xml"/><text>After child.</text></document>','code/one.xml':b'<section xmlns="https://open.law/schemas/library"><num>1.01</num><heading>Operative provision</heading><text>Child substantive body.</text></section>'}
  def fixture(values):
   stream=io.BytesIO()
   with zipfile.ZipFile(stream,'w')as z:
    for path,data in values.items():z.writestr('observed-root/'+path,data)
   tree={'tree':[{'type':'blob','path':p,'sha':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}for p,b in values.items()],'truncated':False};return stream.getvalue(),tree
  data,tree=fixture(files);c={'repository':'fixture/law-xml','archive_start':'index.xml','xml_publication_roots':['code/index.xml'],'publication':'Code','jurisdiction':'Fixture','state':'ZZ'};item={'id':'archive','url':'https://fixture.invalid/code.zip','raw_ref':'archive.zip','git_tree':tree,'source_commit':'a'*40};rows,ledger=openlaw_xml.parse(data,c,item);self.assertEqual([x['text']for x in rows],['Before child.','Child substantive body.','After child.']);self.assertFalse(ledger['unvisited_selected_xml_members']);self.assertEqual(len(ledger['xml_include_edges']),1)
  for mutation in ['missing','cycle','corrupttree']:
   altered=dict(files)
   if mutation=='missing':altered.pop('code/one.xml')
   if mutation=='cycle':altered['code/one.xml']=b'<document xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="index.xml"/></document>'
   bad,bt=fixture(altered)
   if mutation=='corrupttree':bt['tree'][0]['sha']='0'*40
   with self.assertRaises(ValueError):openlaw_xml.parse(bad,c,{**item,'git_tree':bt})
if __name__=='__main__':unittest.main(verbosity=2)
