"""Actual publisher-shape footnote ownership and omission faults; no network."""
import copy,json,sys,socket
from pathlib import Path
from unittest.mock import patch
from model import native_records
from audit_native import audit
from bs4 import BeautifulSoup

def fixture():
 html='''<html><body><div><div id="rid-A" class="toc-destination Section">Section A</div><div id="rid-A-body">The rule applies<a name="text--1"></a><a class="lk-folk-popup" href="#foot--1">1</a>.</div><p>Notes</p><table class="footnote"><tbody><tr><td class="marker"><a name="foot--1"></a><a class="lk-folk-popup" href="#text--1"><span class="cs-folk-footnote">1</span></a></td><td class="foot-text"><p>Available source note.</p></td></tr></tbody></table></div><div><div id="rid-B" class="toc-destination Section">Section B</div><div id="rid-B-body">Another rule applies.</div></div></body></html>'''
 inv={'nodes':[{'document_id':x,'internal_id':i,'heading':'Section '+x,'path':['Section '+x],'parent_id':None,'has_children':False} for i,x in enumerate(['A','B'],1)]};return html,inv

def tests():
 html,inv=fixture();records=native_records(html.encode(),inv,{},'https://example.invalid/','fixture');a=records[0];checks=[]
 assert len(a['native_auxiliary_fragments'])==2 and a['tables']==[[[{'tag':'td','text':'1','rowspan':1,'colspan':1},{'tag':'td','text':'Available source note.','rowspan':1,'colspan':1}]]];assert a['text'].count('Available source note.')==1 and not records[1].get('native_auxiliary_fragments');assert audit(html.encode(),records)['passed'];checks.append({'name':'typed_source_footnote_heading_table_owned_once_by_reciprocal_section_anchors_and_independently_audited','passed':True})
 for name,change in [('arbitrary_unowned_operative_text',lambda s:s.body.append(BeautifulSoup('<p>Unowned legal rule.</p>','html.parser'))),('missing_reciprocal_inline_target',lambda s:s.find('a',attrs={'name':'text--1'}).decompose()),('unbound_marker_name',lambda s:s.find('a',attrs={'name':'foot--1'}).__setitem__('name','wrong')),('marker_backlink_wrong',lambda s:s.select_one('table a.lk-folk-popup').__setitem__('href','#text--2')),('note_heading_missing',lambda s:s.find('p',string='Notes').decompose()),('auxiliary_rich_block_duplication',lambda s:s.select_one('td.foot-text').append(BeautifulSoup('<div id="rid-extra">Duplicate body.</div>','html.parser'))),('multiple_inventory_section_owners',lambda s:s.select_one('table').parent.append(BeautifulSoup('<div id="rid-B" class="toc-destination">Section B duplicate</div>','html.parser')))]:
  soup=BeautifulSoup(html,'html.parser');change(soup)
  try:native_records(str(soup).encode(),inv,{},'https://example.invalid/','fixture')
  except AssertionError:checks.append({'name':name+'_fails_closed','passed':True});continue
  raise AssertionError('Fault accepted: '+name)
 dropped=copy.deepcopy(records);dropped[0]['native_auxiliary_fragments'].clear();assert not audit(html.encode(),dropped)['passed'];checks.append({'name':'independent_raw_table_audit_rejects_omitted_auxiliary_ownership_evidence','passed':True})
 altered=copy.deepcopy(records);altered[0]['tables'][0][0][1]['text']='Altered legal note.';assert not audit(html.encode(),altered)['passed'];checks.append({'name':'independent_raw_table_audit_rejects_changed_note_text','passed':True})
 image_html=html.replace('Available source note.','Available source note.<img src="DATA:IMAGE/PNG;base64,QUJD\nUEFZTE9BRF9NVVNUX05PVF9TVVJWSVZF" data-label="graphic">')
 with patch.object(socket.socket,'connect',side_effect=AssertionError('No transport')),patch('PIL.Image.open',side_effect=AssertionError('No image decoder')):
  image_records=native_records(image_html.encode(),inv,{},'https://example.invalid/','fixture')
 serialized=json.dumps(image_records);assert '[IMAGE]' in image_records[0]['tables'][0][0][1]['text'] and 'data:image' not in serialized.lower() and 'UEFZTE9BRF9NVVNUX05PVF9TVVJWSVZF' not in serialized;assert all(a['disposition']!='required-asset' for r in image_records for a in r['assets']);checks.append({'name':'auxiliary_note_image_literal_placeholder_no_payload_no_transport_or_decode','passed':True})
 return {'passed':True,'count':len(checks),'tests':checks}
if __name__=='__main__':
 result=tests();Path(__file__).with_name('native-note-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
