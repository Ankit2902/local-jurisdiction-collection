import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import king_normalize as kn,king_acquire as ka,king_native as native
from test_original_adapters import fixture,word
from source_common import *
from flagstaff_root import root_inventory,URL
class FinalConsistency(unittest.TestCase):
 def charter(self,extra):
  return kn.parse(('<html><body><p>CHARTER</p><h1>ARTICLE 2</h1><p><b>220 Parent.</b></p>'+extra+'</body></html>').encode(),{'id':'charter','url':'https://example.invalid/charter','heading':'Charter','kind':'charter','updated':'10/17/2026'})
 def test_published_child_qualifies_structural_parent(self):
  rr,r=self.charter('<p><b>220.10 Child.</b> Legal body.</p>');parent=next(r for r in rr if r['number']=='220');self.assertEqual(parent['body_qualification'],'source_structural_parent_with_published_children');self.assertEqual(len(parent['source_child_section_ids']),1);self.assertNotIn('Legal body',parent['full_text']);self.assertFalse(r['heading_only_unresolved'])
 def test_unrelated_next_section_does_not_qualify_parent(self):
  rr,r=self.charter('<p><b>230 Other.</b> Body.</p><p><b>220.10 Later.</b> Body.</p>');self.assertEqual(len(r['heading_only_unresolved']),1)
 def test_legacy_font_glyph_semantics_remain_explicit(self):
  rr,a=kn.parse(b'<html><body><p>Title 1</p><p><b>1.01.010 Test.</b> 70<span style="font-family:Symbol">&#176;</span>F.</p></body></html>',{'id':'t','url':'https://example.invalid/title','heading':'Title 1: Test','kind':'title','updated':'10/17/2026'})
  self.assertEqual(a['unresolved_legacy_font_runs'],1);self.assertFalse(rr[-1]['legacy_font_literal_runs'][0]['glyph_semantics_qualified'])
 def test_symbol_pair_requires_exact_all_surrounding_text(self):
  from king_symbol_audit import matching
  self.assertEqual(matching('70[SYMBOL F0B0] F','70° F')[0]['html_unicode'],'U+00B0');self.assertIsNone(matching('70[SYMBOL F0B0] F','71° F'));self.assertIsNone(matching('70[SYMBOL F0B0] F','70XX F'))
 def test_exact_source_empty_disposition_cannot_waive_changed_bytes(self):
  rr,r=kn.parse(b'<html><body><p>CHARTER</p><p><b>650.40 Transitional Provisions.</b></p><p><b>670 Recall.</b> Body.</p></body></html>',{'id':'x','url':'https://aqua.kingcounty.gov/council/clerk/code/03_Charter.htm','heading':'Charter','kind':'charter','updated':'1/10/2024'});self.assertEqual(len(r['heading_only_unresolved']),1)
 def roots(self,extra=''):
  return ('<div id="divmuni">'+''.join(f'<p><input name="code" value="{i}"><a href="../html/F{i}.html" id="r{i}">Title {i}</a></p>' for i in range(10))+extra+'</div>').encode()
 def test_multiline_pixel_metadata_boundary_preserves_visible_legal_text(self):
  from model import semantics,redact_image_metadata
  from bs4 import BeautifulSoup
  payload='DATA:IMAGE/PNG;base64,QUJD\nUElYRUxTX0NPTlRJTlVBVElPTl9NVVNUX05PVF9TVVJWSVZF'
  node=BeautifulSoup('<p data-image-metadata="'+payload+'">Before <b>legal caption</b> after.</p>','html.parser').p
  result=semantics(node,'https://example.invalid/code');serialized=json.dumps(result)
  self.assertNotIn('UElYRUx',serialized);self.assertNotIn('QUJD',serialized);self.assertEqual(result['text'],'Before legal caption after.');self.assertIn('[IMAGE]',result['html']);self.assertIn(sha(payload.encode()),result['html'])
  metadata=redact_image_metadata({'source_image_metadata':payload});self.assertEqual(metadata['source_image_metadata'],'[IMAGE]');self.assertNotIn('UElYRUx',json.dumps(metadata))
 def test_quoted_legal_image_data_keeps_surrounding_prose(self):
  from model import legal_image_text,semantics
  from bs4 import BeautifulSoup
  text='Before "DATA:IMAGE/PNG;base64,QUJD\nUElYRUxT" after legal caption.'
  self.assertEqual(legal_image_text(text),'Before "[IMAGE]" after legal caption.')
  result=semantics(BeautifulSoup('<p>'+text+'</p>','html.parser').p,'https://example.invalid/code');self.assertEqual(result['text'],'Before "[IMAGE]" after legal caption.');self.assertNotIn('UElYRUxT',json.dumps(result))
 def test_unquoted_legal_image_data_fails_without_deleting_prose(self):
  from model import semantics,redact_image_metadata
  from bs4 import BeautifulSoup
  text='Before DATA:IMAGE/PNG;base64,QUJD\nUElYRUxT after legal caption.'
  with self.assertRaisesRegex(ValueError,'Unqualified unquoted'):semantics(BeautifulSoup('<p>'+text+'</p>','html.parser').p,'https://example.invalid/code')
  with self.assertRaises(ValueError):redact_image_metadata({'text':text})
 def test_word_unquoted_image_data_fails_and_quoted_preserves_caption(self):
  from word_model import ordered_text
  import xml.etree.ElementTree as E
  for text,qualified in [('Before DATA:IMAGE/PNG;base64,QUJD\nUElYRUxT after.',False),('Before "DATA:IMAGE/PNG;base64,QUJD\nUElYRUxT" after.',True)]:
   node=E.fromstring('<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:r><w:t>'+text+'</w:t></w:r></w:p>')
   if qualified:
    value,images,_=ordered_text(node);self.assertEqual(value,'Before "[IMAGE]" after.');self.assertEqual(len(images),1)
   else:
    with self.assertRaises(ValueError):ordered_text(node)
 def test_image_alternate_caption_metadata_is_retained_without_payload(self):
  from model import semantics
  from bs4 import BeautifulSoup
  result=semantics(BeautifulSoup('<p>Caption<img src="map.png" alt="Published map label"></p>','html.parser').p,'https://example.invalid/code');self.assertEqual(result['assets'][0]['source_descriptive_attributes']['alt'],'Published map label');self.assertEqual(result['text'],'Caption[IMAGE]')
 def test_normalization_revision_is_captured_before_source_and_drift_rejected(self):
  import source_common as common
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'module.py').write_text('original');out=root/'out';out.mkdir()
   with patch.object(common,'__file__',str(root/'source_common.py')):
    code=common.normalization_snapshot(out,['module.py']);(root/'module.py').write_text('changed')
    with self.assertRaisesRegex(ValueError,'revision changed'):common.verify_normalization_revision(code)
   self.assertEqual((out/'executed-normalization/module.py').read_text(),'original')
 def extended_word(self,extra_member,extra_xml,rel_kind='header'):
  import zipfile,io
  source=io.BytesIO(word(False));data=io.BytesIO()
  with zipfile.ZipFile(source) as zin,zipfile.ZipFile(data,'w') as out:
   for name in zin.namelist():
    raw=zin.read(name)
    if name=='word/_rels/document.xml.rels':raw=raw.replace(b'</Relationships>',('<Relationship Id="extra" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'+rel_kind+'" Target="'+extra_member+'"/></Relationships>').encode())
    out.writestr(name,raw)
   out.writestr('word/'+extra_member,extra_xml)
  return data.getvalue()
 def test_actual_kind_header_is_owned_and_not_edition_inferred(self):
  from word_model import inspect
  xml='<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>Cached legacy page label</w:t></w:r></w:p></w:hdr>';raw=self.extended_word('header1.xml',xml);r=inspect(raw);part=next(n for n in r['notes'] if n['kind']=='source_header');self.assertEqual(part['text'],'Cached legacy page label');self.assertTrue(part['source_xml_sha256']);self.assertIn('not a publication currency',part['source_part_role']);self.assertIn('word/header1.xml',r['members_read'])
 def test_unparsed_required_xml_is_not_called_retained_or_qualified(self):
  from word_model import inspect
  raw=self.extended_word('unknown.xml','<unparsed>Owned unknown legal document</unparsed>',rel_kind='unknownLegalPart');r=inspect(raw);rel=next(x for x in r['relationships'] if x['id']=='extra');self.assertEqual(rel['status'],'unresolved_nonimage_dependency');self.assertTrue(rel['required'])
 def test_unprofiled_note_table_fails_closed(self):
  from word_model import inspect
  xml='<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:footnote w:id="1"><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Operative cell</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:footnote></w:footnotes>';raw=self.extended_word('footnotes.xml',xml,rel_kind='footnotes')
  with self.assertRaisesRegex(ValueError,'note table'):inspect(raw)
 def test_note_tracked_changes_are_explicit(self):
  from word_model import inspect
  xml='<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:footnote w:id="1"><w:p><w:ins><w:r><w:t>Inserted source note</w:t></w:r></w:ins></w:p></w:footnote></w:footnotes>';r=inspect(self.extended_word('footnotes.xml',xml,rel_kind='footnotes'));self.assertEqual(r['tracked_change_elements'],1);self.assertTrue(r['notes'][0]['source_xml_sha256'])
 def test_finite_word_recovery_is_exact_source_bound(self):
  from character_recovery import profiles,recover_word
  entry=profiles()['word'][0];unit={'source_ordinal':entry['word_source_ordinal'],'source_xml_sha256':entry['source_xml_sha256'],'text':entry['original_word_literal'],'tables':[]};got=recover_word(entry['source_document_id'],entry['source_native_sha256'],unit);self.assertNotIn('[SYMBOL',got['text']);self.assertEqual(got['original_symbol_text'],unit['text']);self.assertEqual(recover_word(entry['source_document_id'],'wrong-edition',unit),unit)
  with self.assertRaisesRegex(ValueError,'XML/literal'):recover_word(entry['source_document_id'],entry['source_native_sha256'],dict(unit,source_xml_sha256='corrupt'))
 def test_private_glyph_cannot_be_promoted(self):
  from character_recovery import valid_character
  with self.assertRaises(ValueError):valid_character('\uf8e7')
 def test_finite_html_recovery_is_fragment_bound(self):
  import character_recovery as recovery
  from bs4 import BeautifulSoup
  body=BeautifulSoup('<body><p>1<span style="font-family:Symbol">²</span> thick.</p></body>','html.parser').body;span=body.span;target=body.p;profile={'word':[],'html':[{'source_document_id':'doc','source_html_sha256':'source','html_block_index':0,'source_fragment_sha256':sha(str(target).encode()),'source_native_sha256':'native','source_xml_sha256':'xml','source_pdf_sha256':'pdf','replacements':[{'source_span_sha256':sha(str(span).encode()),'original_literal':'²','recovered_literal':'″'}]}]}
  with patch.object(recovery,'profiles',return_value=profile):events=recovery.recover_html('doc','source',body,[target])
  self.assertEqual(len(events),1);self.assertEqual(body.get_text(),'1″ thick.');self.assertNotIn('font-family',str(body));self.assertIn('data-source-character-recovery',str(body))
 def test_word_textbox_labels_are_preserved_as_metadata_no_pixels(self):
  from word_model import ordered_text
  import xml.etree.ElementTree as E
  node=E.fromstring('<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:pict><w:txbxContent><w:p><w:r><w:t>Cached source label</w:t></w:r></w:p></w:txbxContent></w:pict></w:p>');text,images,_=ordered_text(node);self.assertEqual(text,'[IMAGE]');self.assertEqual(images[0]['source_embedded_text_nodes'],['Cached source label'])
 def test_missing_source_character_profile_is_operational_preflight_failure(self):
  from doctor import required_data
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);save(root/'configs.json',{'schema_version':1});save(root/'source_dispositions.json',{'schema':'king-source-dispositions-1'});errors=required_data(root);self.assertTrue(any('source_character_dispositions.json' in e for e in errors))
 def test_collect_preflight_failure_never_calls_transport(self):
  from collect import main
  with tempfile.TemporaryDirectory() as t,patch('doctor.run',return_value={'ready_to_attempt_collection':False,'mandatory_source_data_errors':['missing profile']}),patch.object(transport,'fetch',side_effect=AssertionError('publisher request')):
   with self.assertRaisesRegex(ValueError,'before transport'):main('original-king-county-wa',Path(t)/'fresh')
 def test_http200_challenge_causes_persisted_stop(self):
  from browser_safety import guard_html
  with tempfile.TemporaryDirectory() as t,patch.object(transport,'ROOT',Path(t)):
   url='https://example.invalid/code'
   with self.assertRaisesRegex(RuntimeError,'access stop'):guard_html(b'<title>Just a moment...</title>',url,200,{})
   with self.assertRaises(RuntimeError):transport.reserve(url)
 def test_ordinary_legal_access_denied_text_is_not_challenge(self):
  from browser_safety import guard_html
  with patch.object(transport,'stop',side_effect=AssertionError('false source stop')):guard_html(b'<title>City Code</title><p>Access denied by the clerk.</p>','https://example.invalid/code',200,{})
 def test_actual_native_root_has_source_anchors_before_js_checkboxes(self):
  raw=(Path(__file__).resolve().parents[1]/'fixtures/flagstaff-native-root.html').read_bytes();roots=root_inventory(raw);self.assertEqual(len(roots),18);self.assertEqual(roots[0]['label'],'CHARTER');self.assertEqual(roots[-1]['source_id'],'FlagstaffOT')
 def test_unknown_native_root_container_cannot_disappear(self):
  with self.assertRaises(ValueError):root_inventory(self.roots('<li><a id="new" href="../html/NEW.html">New title</a></li>'))
 def test_native_division_and_section_share_fragment_but_have_distinct_owners(self):
  from flagstaff_html_normalize import parse
  u=URL+'html/F.html';edges=[{'edge_id':'division','source_url':u+'#10.20.10','label':'Division 10-20.10: Purpose'},{'edge_id':'section','source_url':u+'#10.20.10','label':'10-20.10 Purpose'}];rr,a=parse(b'<div id="mainContent"><p class="Division"><a name="10.20.10"></a>Division 10-20.10:<br>Purpose</p><h3 class="Cite" id="10.20.10">10-20.10 Purpose</h3><p>Legal text.</p></div>',u,edges);self.assertEqual(a['matched_toc_edges'],2);self.assertEqual(len({m['record_id'] for m in a['mapping']}),2);self.assertFalse(a['missing_toc_edges'])
 def test_flagstaff_source_parent_keeps_child_text_separate(self):
  from flagstaff_html_normalize import parse
  u=URL+'html/F.html';rr,a=parse(b'<div id="mainContent"><h3 class="Cite" id="1.01">Parent</h3><h3 class="Cite" id="1.01.1">Child</h3><p>Legal child body.</p></div>',u,[]);self.assertFalse(a['heading_only_unresolved']);self.assertEqual(rr[0]['body_qualification'],'source_structural_parent_with_published_children');self.assertNotIn('Legal child body',rr[0]['full_text'])
 def test_reference_boundaries_do_not_waive_real_native_attachment(self):
  from flagstaff_html_normalize import independent_reference
  rules=load(Path(__file__).resolve().parents[1]/'configs.json')['targets']['original-flagstaff-az']['independent_reference_rules'];a={'kind':'a','source_attribute':'href','url':'https://www.codepublishing.com/cgi-bin/ars.pl?cite=42-5075','context':'A.R.S. Section42-5075; tangible property incorporated or fabricated.'};self.assertEqual(len(independent_reference(a,rules)),1)
  for url in ['https://www.codepublishing.com/AZ/Flagstaff/files/Appendix.pdf','https://example.invalid/appendix.pdf','https://www.codepublishing.com/cgi-bin/ars.pl?cite=42-5075&file=appendix.pdf']:
   self.assertFalse(independent_reference(dict(a,url=url),rules))
 def test_root_new_title_changes_inventory(self):
  a=root_inventory(self.roots());b=root_inventory(self.roots('<p><input name="code" value="11"><a href="../html/F11.html">Title 11</a></p>'));self.assertNotEqual(a,b);self.assertEqual(len(b),11)
 def test_duplicate_or_foreign_root_refused(self):
  for extra in ['<p><input name="code" value="x"><a href="../html/F1.html">Duplicate</a></p>','<p><input name="code" value="x"><a href="https://example.invalid/X.html">Other</a></p>']:
   with self.assertRaises(ValueError):root_inventory(self.roots(extra))
 def test_completed_html_resume_makes_no_request(self):
  with tempfile.TemporaryDirectory() as t:
   src=Path(t)/'source';s=fixture(src);s.update(code_fingerprint=source_snapshot(src,ka.FILES),opening_closing_inventory_equal=True,content_routes_acquired=10);save(src/'checkpoint.json',s)
   with patch.object(ka,'acquire',side_effect=AssertionError('network')):r=ka.collect(src,resume=True)
   self.assertTrue(r['opening_closing_inventory_equal'])
 def checked_ledger(self,mutator):
  from publication_source_verify import validate
  with tempfile.TemporaryDirectory() as t:
   src=Path(t)/'source';s=fixture(src)
   for i,a in enumerate(s['artifacts']):a.update(started_at=f'2026-10-17T12:00:{i*2:02d}+00:00',finished_at=f'2026-10-17T12:00:{i*2+1:02d}+00:00')
   mutator(s);save(src/'checkpoint.json',s);return validate('king',src)
 def test_source_ledger_real_sequence_is_required(self):
  self.assertTrue(self.checked_ledger(lambda s:None)['opening_body_closing_chronology_verified'])
 def test_source_opening_after_body_refused(self):
  with self.assertRaisesRegex(ValueError,'chronology'):self.checked_ledger(lambda s:s['artifacts'][0].update(started_at='2026-10-17T13:00:00+00:00',finished_at='2026-10-17T13:00:01+00:00'))
 def test_duplicate_opening_refused(self):
  with self.assertRaises(ValueError):self.checked_ledger(lambda s:s['artifacts'].append(dict(s['artifacts'][0])))
 def test_extra_foreign_body_route_refused(self):
  with self.assertRaises(ValueError):self.checked_ledger(lambda s:s['artifacts'].append(dict(s['artifacts'][1],source_url='https://example.invalid/extra',final_url='https://example.invalid/extra')))
 def test_native_resume_only_missing_then_completed_resume_no_request(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t)/'source';s=fixture(base)
   for d in s['inventory']:d['native_alternatives']=[{'url':d['url'][:-4]+'.docx','label':'Word'}]
   s['inventory_sha256']=sha(canon(s['inventory']));save(base/'checkpoint.json',s);dest=Path(t)/'native';calls=[]
   def fetch(url):
    calls.append(url);raw=b'index' if url==ka.URL else word(False);return raw,{'status':200,'source_url':url,'final_url':url,'sha256':sha(raw),'bytes':len(raw),'headers':{}}
   with patch.object(native,'inventory',return_value=s['inventory']),patch.object(transport,'fetch',side_effect=fetch):
    a=native.run(base,dest,max_items=1);self.assertFalse(a['errors']);self.assertEqual(sum(a['role']=='native-word' for a in a['artifacts']),1)
    first=s['inventory'][0]['native_alternatives'][0]['url'];b=native.run(base,dest,resume=True);self.assertFalse(b['errors']);self.assertEqual(calls.count(first),1)
   with patch.object(transport,'fetch',side_effect=AssertionError('network')):native.run(base,dest,resume=True)
 def test_native_resume_version_drift_before_request(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t)/'source';s=fixture(base);s['inventory_sha256']=sha(canon(s['inventory']));save(base/'checkpoint.json',s);dest=Path(t)/'native';dest.mkdir();save(dest/'checkpoint.json',{'source_url':ka.URL,'source_inventory_sha256':s['inventory_sha256'],'errors':[],'code_fingerprint':{'king_native.py':'wrong'},'artifacts':[]})
   with patch.object(transport,'fetch',side_effect=AssertionError('network')):
    with self.assertRaisesRegex(ValueError,'version drift'):native.run(base,dest,resume=True)
if __name__=='__main__':unittest.main()
