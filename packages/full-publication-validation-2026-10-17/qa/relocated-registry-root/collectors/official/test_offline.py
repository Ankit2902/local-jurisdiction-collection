#!/usr/bin/env python3
"""Network-free source-backed parser/fault/resume qualification. Synthetic index/transport are explicit."""
import contextlib,copy,io,json,pathlib,shutil,tempfile,unittest,zipfile,warnings,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
import collect,model,transport,verify
BASE=pathlib.Path(__file__).resolve().parent
PDF=(BASE/'fixtures/portland-33-10.pdf').read_bytes()
ROOT='https://fixture.invalid/index';A='https://fixture.invalid/a.pdf';B='https://fixture.invalid/b.pdf'
INDEX=b'<main><a href="a.pdf">PublicationA</a><a href="b.pdf">PublicationB</a></main>'
def fake_fetch(url,max_bytes=160000000):
 data={ROOT:INDEX,A:PDF,B:PDF}[url];return data,{'url':url,'final_url':url,'status':200,'headers':{},'sha256':model.sha(data),'bytes':len(data),'transport':'explicit synthetic transport over retained realPDF fixture; no network'}
class Qualification(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name);self.config={'schema':1,'id':'fixture-native-set','jurisdiction':'Portland source-PDF test fixture','state':'OR','publication':'Synthetic two-file inventory over retained actual4-page PDF','source_url':ROOT,'mode':'pdf_set','transport':'http','inventory_selector':'main a[href]','include_url_regex':r'\.pdf$','coverage_level':'file_pages'};self.cf=self.root/'config.json';collect.save(self.cf,self.config)
 def tearDown(self):self.temp.cleanup()
 def run_collect(self,name,**kwargs):
  out=self.root/name
  with patch.object(transport,'fetch',fake_fetch),contextlib.redirect_stdout(io.StringIO()):code=collect.collect(self.cf,out,**kwargs)
  return out,code
 def clone(self,src,name):out=self.root/name;shutil.copytree(src,out);return out
 def rejected(self,out):
  try:r=verify.verify(out);self.assertFalse(r['requested_coverage_complete'])
  except (ValueError,FileNotFoundError,KeyError):pass
 def test_full_page_coverage_and_resume_equivalence(self):
  full,code=self.run_collect('full');self.assertEqual(code,0);r=verify.verify(full);self.assertTrue(r['pdf_page_extraction_complete']);self.assertFalse(r['legal_semantic_coverage_complete']);self.assertEqual(r['parsed_record_count'],8)
  interrupted,code=self.run_collect('resume',interrupt_after=1);self.assertEqual(code,3);self.rejected(interrupted)
  resumed,code=self.run_collect('resume',resume=True);self.assertEqual(code,0);verify.verify(resumed);self.assertEqual((full/'records.jsonl').read_bytes(),(resumed/'records.jsonl').read_bytes())
 def test_faults_missing_duplicate_corrupt_pagegap_wrongedition(self):
  full,_=self.run_collect('full');state=collect.load(full/'checkpoint.json');item=state['items'][0];file=model.sha(item['id'].encode())[:24]+'.json'
  for fault in ['missing','duplicate','corrupt','pagegap','edition','inventory','interruption']:
   out=self.clone(full,fault)
   if fault=='missing':(out/'items'/file).unlink()
   elif fault=='duplicate':
    p=out/'records.jsonl';p.write_bytes(p.read_bytes()+p.read_bytes().splitlines(keepends=True)[0])
   elif fault=='corrupt':
    d=collect.load(out/'items'/file);(out/d['item']['raw_ref']).write_bytes(b'corrupt')
   elif fault=='pagegap':
    p=out/'items'/file;d=collect.load(p);d['records'].pop(1);collect.save(p,d)
   elif fault=='edition':
    p=out/'config.json';c=collect.load(p);c['edition']='wrong edition';collect.save(p,c)
   elif fault=='inventory':
    s=collect.load(out/'checkpoint.json');s['items'].pop();collect.save(out/'inventory.json',s['items']);s['inventory_sha256']=model.sha(model.encoded(s['items']));collect.save(out/'checkpoint.json',s)
   else:
    s=collect.load(out/'checkpoint.json');s['completed']=False;collect.save(out/'checkpoint.json',s)
   self.rejected(out)
 def test_explicit_limit_never_complete(self):
  out,code=self.run_collect('limited',max_items=1);self.assertEqual(code,3);self.rejected(out)
 def test_source_drift_recomputed_not_trusted_boolean(self):
  out,_=self.run_collect('full');s=collect.load(out/'checkpoint.json');end=out/s['consistency']['raw_ref'];end.write_bytes(INDEX.replace(b'</main>',b'<a href="c.pdf">C</a></main>'))
  meta=end.with_suffix('.receipt.json');m=collect.load(meta);m['sha256']=model.sha(end.read_bytes());collect.save(meta,m);s['consistency']['consistent']=True;collect.save(out/'checkpoint.json',s);self.rejected(out)
 def test_resume_identity_mismatch_rejected(self):
  self.run_collect('partial',interrupt_after=1);self.config['publication']='Other publication';collect.save(self.cf,self.config)
  with self.assertRaises(ValueError):self.run_collect('partial',resume=True)
 def test_pdf_edition_mismatch_prevents_completion(self):
  self.config['edition_tokens']=['IMPOSSIBLE OTHER CITY2029'];collect.save(self.cf,self.config);out,code=self.run_collect('wrong');self.assertEqual(code,3);self.rejected(out)
 def test_actual_archive_canonical_closure_and_duplicates(self):
  c={'id':'source-article-fixture','jurisdiction':'Baltimore City','state':'MD','publication':'Retained ArticleI fixture subset','archive_prefix':'/us/md/cities/baltimore/charter/I','mode':'github_archive'};data=(BASE/'fixtures/baltimore-charter-I.zip').read_bytes();records,ledger=model.archive_records(data,c,'fixture.zip');self.assertEqual(len(records),19);self.assertFalse(ledger['missing_internal_nav_targets']);self.assertEqual(len({r['id'] for r in records}),len(records));self.assertEqual(ledger['alternate_aggregate_members_excluded'],1)
  original=zipfile.ZipFile(io.BytesIO(data));target=next(n for n in original.namelist() if n.endswith('/1/index.html'))
  for duplicate in [False,True]:
   stream=io.BytesIO()
   with warnings.catch_warnings(),zipfile.ZipFile(stream,'w') as z:
    warnings.simplefilter('ignore')
    for n in original.namelist():
     if duplicate or n!=target:z.writestr(n,original.read(n))
    if duplicate:z.writestr(target,original.read(target))
   if duplicate:
    with self.assertRaises(ValueError):model.archive_records(stream.getvalue(),c,'fixture.zip')
   else:self.assertTrue(model.archive_records(stream.getvalue(),c,'fixture.zip')[1]['missing_internal_nav_targets'])
 def test_contextual_external_reference_and_incorporated_attachment(self):
  config={'reference_rules':[{'url_regex':'state[.]example','context_regex':'Annotated Code','reason':'Independent state legal layer'}]};base={'url':'https://state.example/law.pdf','kind':'a','context':'See Annotated Code of Maryland'};self.assertFalse(model.classify_asset(base,config)['required']);base['context']='AppendixA is incorporated by reference; see Annotated Code';self.assertTrue(model.classify_asset(base,config)['required'])
 def test_rich_required_asset_forms_and_image_only_not_text(self):
  from bs4 import BeautifulSoup
  node=BeautifulSoup('<main><h1>Official legal map</h1><svg><image href="map.svg"/><use href="symbols.svg#district"/></svg><picture><source srcset="one.png1x, two.png2x"/><img src="fallback.png" srcset="one.png1x, two.png2x"/></picture><div style="background-image:url(official-map.png)"></div><style>.x{background:url(extra.svg)}</style><video src="video.mp4" poster="poster.png"></video></main>','html.parser').main;assets=model.source_assets(node,ROOT);urls={a['url'] for a in assets};self.assertIn('https://fixture.invalid/map.svg',urls);self.assertIn('https://fixture.invalid/symbols.svg#district',urls);self.assertIn('https://fixture.invalid/official-map.png',urls);self.assertIn('https://fixture.invalid/poster.png',urls);self.assertTrue(all('url' in a for a in assets));self.assertTrue(all(not a['required'] for a in model.semantics(node,ROOT)['assets'] if model.image_asset(a)))
  with self.assertRaises(ValueError):model.html_records(b'<main><h1>Official legal map long enough to pass a naive text length</h1></main>',{'id':'a','url':ROOT,'heading':'Map','raw_ref':'a.html'},{'mode':'html_single','content_selector':'main','legal_marker_regex':'Official legal map','jurisdiction':'Fixture','state':'ZZ','publication':'Map'})
 def test_extensionless_incorporation_and_nested_table_ownership(self):
  from bs4 import BeautifulSoup
  node=BeautifulSoup('<main><p>Official Map is incorporated by reference <a href="https://example.gov/document/123">Map</a></p><table><tr><td>Outer<table><tr><td>Inner</td></tr></table></td></tr></table></main>','html.parser').main
  assets=model.source_assets(node,ROOT);self.assertTrue(any(a['url']=='https://example.gov/document/123' and a['required'] for a in assets));tables=model.table_data(node);self.assertEqual(len(tables[0]['rows']),1);self.assertEqual(len(tables[1]['rows']),1);self.assertEqual(tables[1]['parent_table_index'],0)
 def test_user_image_policy_no_fetch_and_literal_placeholders(self):
  html=b'<main><h1>Qualified legal ordinance</h1><p>This operative legal text is long enough and independently qualified.</p><picture><source srcset="missing-image.png1x"/><img id="photo1" src="missing-image.png"/></picture><svg id="map1"><image href="other-image.svg"/></svg><div style="background-image:url(third-image.png)"></div></main>'
  self.config.update(mode='html_single',content_selector='main',legal_marker_regex='Qualified legal ordinance',coverage_level='publication_text');self.config.pop('include_url_regex');collect.save(self.cf,self.config);called=[]
  def fake(url,max_bytes=160000000):
   called.append(url)
   if url!=ROOT:raise AssertionError('Image fetch forbidden: '+url)
   return html,{'url':url,'final_url':url,'status':200,'headers':{},'sha256':model.sha(html),'bytes':len(html)}
  with patch.object(transport,'fetch',fake),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(collect.collect(self.cf,self.root/'noimages'),0)
  report=verify.verify(self.root/'noimages');self.assertTrue(all(url==ROOT for url in called));self.assertEqual(report['required_assets_count'],0);self.assertGreater(report['policy_omitted_image_count'],0);self.assertGreaterEqual(report['image_placeholder_count'],3);rows=[json.loads(x) for x in (self.root/'noimages/records.jsonl').read_text().splitlines()];self.assertIn('[IMAGE]',rows[0]['text']);self.assertNotIn('<img',rows[0]['html']);self.assertNotIn('<svg',rows[0]['html']);self.assertFalse(any(a['required'] for a in rows[0]['assets']))
 def test_same_bytes_wrong_source_cache_swap_rejected(self):
  out,_=self.run_collect('full');state=collect.load(out/'checkpoint.json');first,second=state['items'];p=out/'items'/(model.sha(first['id'].encode())[:24]+'.json');record=collect.load(p);record['item']['raw_ref']=second['raw_ref'];data=(out/second['raw_ref']).read_bytes();record['raw_sha256']=model.sha(data);record['records'],record['dispositions']=collect.parse_item(data,record['item'],self.config);collect.save(p,record);self.rejected(out)
 def test_zip_crc_corruption_is_rejected(self):
  data=(BASE/'fixtures/baltimore-charter-I.zip').read_bytes();z=zipfile.ZipFile(io.BytesIO(data));entry=z.infolist()[0];offset=entry.header_offset+30+len(entry.filename.encode())+len(entry.extra);corrupt=bytearray(data);corrupt[offset+10]^=64
  config={'id':'fixture','jurisdiction':'Baltimore City','state':'MD','publication':'ArticleI fixture','archive_prefix':'/us/md/cities/baltimore/charter/I'}
  with self.assertRaises(Exception):model.archive_records(bytes(corrupt),config,'corrupt.zip')
 def test_current_milwaukee_six_file_inventory_not_historic_alternates(self):
  c=collect.load(BASE/'configs/milwaukee-publications.json');raw=(BASE/'fixtures/milwaukee-index-links.html').read_bytes()
  with patch.object(collect,'fetch_raw',return_value=(raw,{},'fixture.html')):items,_=collect.discover(self.root,c)
  self.assertEqual(len(items),6);self.assertTrue(any('/Salary/2026-' in x['url'] for x in items));self.assertTrue(any('/Positions/2026-' in x['url'] for x in items));self.assertFalse(any('2021' in x['url'] for x in items));self.assertEqual(sum('Master-' in x['url'] for x in items),4)
if __name__=='__main__':unittest.main(verbosity=2)
