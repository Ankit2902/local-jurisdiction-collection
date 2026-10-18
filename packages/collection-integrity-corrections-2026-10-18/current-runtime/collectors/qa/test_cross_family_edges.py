"""Independent synthetic source-ownership probes. No live-law completeness claims."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from bs4 import BeautifulSoup
from collectors.ecode import adapters as ec
from collectors.encodeplus import model as ep
def load(name,folder):
 path=ROOT/'collectors'/folder;sys.path.insert(0,str(path));spec=importlib.util.spec_from_file_location(name,path/'model.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);sys.path.pop(0);return m
al=load('qa_al_model','american-legal');off=load('qa_official_model','official')
BASE='https://example.invalid/code/'
HTML='<p>Operative rule.</p><svg><image href="map.png"/><use xlink:href="symbol.svg#shape"/></svg><picture><source srcset="small.png 1x, large.png 2x"/></picture><p style="background-image:url(background.svg)"></p>'
EXPECTED={BASE+x for x in ['map.png','symbol.svg','small.png','large.png','background.svg']}
def urls(rows):return {r['url'].split('#')[0] for r in rows if r.get('required',r.get('disposition')=='required-asset')}
def ecode_page(body,kind='section'):
 return ('<html><head><title>Fixture Code</title></head><body data-cust-id="ZZ9000" data-guid="101" data-code-id="fixture" data-current-code-id="fixture" data-code-date="2099" data-customer-name="Fixture NV" data-customer=\'{"state":"NV"}\'><h1 id="pageTitle">Section 1</h1><div id="codeContent"><div id="101_title" data-guid="101" data-code-content-type="'+kind+'" data-full-title="Section 1"></div><div id="101_content" class="content">'+body+'</div></div></body></html>').encode()
class Tests(unittest.TestCase):
 def test_image_reference_metadata_and_nonimage_requirement_all_four(self):
  parsers={'american-legal':lambda:al.refs(HTML,BASE)[0],'ecode':lambda:ec.asset_refs(HTML,BASE,'1'),'official':lambda:off.semantics(BeautifulSoup(HTML,'html.parser'),BASE)['assets']}
  for family,parse in parsers.items():
   with self.subTest(family=family):
    rows=parse();self.assertTrue(EXPECTED<={r['url'].split('#')[0] for r in rows},sorted(EXPECTED-{r['url'].split('#')[0] for r in rows}));self.assertFalse(urls(rows),'Image references must be deliberately omitted, not required downloads')
 def test_ecode_heading_only_operative_unresolved(self):
  raw=ecode_page('<h2>Section 1</h2>');parsed=ec.parse_ecode(raw,'https://ecode360.com/101',ec.identity(raw,'https://ecode360.com/101','ecode360'));self.assertFalse(any(d['classification']=='owned_content' for d in parsed['dispositions']))
 def test_ecode_unowned_visual_fails(self):
  raw=ecode_page('<p>Operative legal requirement.</p>').replace(b'</div></body>',b'<svg><image href="unowned.png"/></svg></div></body>')
  with self.assertRaises(Exception):ec.parse_ecode(raw,'https://ecode360.com/101',ec.identity(raw,'https://ecode360.com/101','ecode360'))
 def test_municipal_unowned_visual_fails(self):
  base='https://fixture.municipal.codes/Code';raw=b'<html><head><title>Fixture City Code</title></head><body><p data-disclaimer="Fixture Code current through 2099">Currency</p><main><article class="type-Section" id="s1" data-history="/Code/1/history"><header>Section 1</header><p>Operative provision applies.</p></article><svg><image href="unowned.png"/></svg></main></body></html>'
  with self.assertRaises(Exception):ec.parse_municipal(raw,base+'/1',base,ec.identity(raw,base,'municipal.codes',base))
 def test_al_heading_only_not_operative(self):
  item={'document_id':'A','internal_id':1,'heading':'Section 1','path':['Section 1'],'parent_id':None,'has_children':False};row=al.html_record({'doc_id':'A','id':1,'html':'<h2 id="rid-A">Section 1</h2>'},item,{},BASE,'fixture');self.assertEqual(row['content_classification'],'unqualified-heading-only')
 def test_al_native_middle_branch_omission_rejected(self):
  inv={'nodes':[{'document_id':x,'internal_id':i,'heading':'Section '+x,'path':[x],'parent_id':None,'has_children':False} for i,x in enumerate(['A','MIDDLE','Z'])]};body='<html><body>'+''.join('<h2 class="toc-destination" id="rid-'+x+'">Section '+x+'</h2><p id="rid-'+x+'-body">Operative requirement applies.</p>' for x in ['A','Z'])+'</body></html>'
  with self.assertRaisesRegex(AssertionError,'omits independent TOC'):al.native_records(body.encode(),inv,{},BASE,'fixture')
 def test_official_heading_only_single_document_rejected(self):
  cfg={'mode':'html_single','id':'fixture','jurisdiction':'Fixture','state':'NV','publication':'Fixture code','content_selector':'main','legal_marker_regex':'§'};item={'id':'fixture','heading':'Fixture','url':BASE,'raw_ref':'raw/fixture.html'};raw='<html><main><h2>§ 1. Long heading describing a substantive local legal subject</h2></main></html>'
  with self.assertRaises(ValueError):off.html_records(raw.encode(),item,cfg)
if __name__=='__main__':unittest.main(verbosity=2)
