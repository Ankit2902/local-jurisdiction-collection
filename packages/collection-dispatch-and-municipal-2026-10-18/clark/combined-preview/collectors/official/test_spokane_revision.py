import unittest,pathlib,json,tempfile,hashlib
from spokane_bulk import parse,section_controls
C={'source_url':'https://my.spokanecity.org/smc/','publication':'Spokane Municipal Code','jurisdiction':'Spokane','state':'WA'}
I={'id':'nativebatch','url':C['source_url'],'raw_ref':'fixture','expected_sections':['01.01.010','01.01.020'],'heading_labels':{'Title':{},'Chapter':{}},'section_heading_labels':{'01.01.010':['Section 01.01.010 Adoption'],'01.01.020':['Section 01.01.020 Effect']}}
RAW=b'''<div id="hideRepealed"><a href="/smc/?Section=01.01.010">Section 01.01.010</a> Adoption<br><p>Operative text with <a href="/smc/?Section=01.01.020"><span>Section 01.01.020</span></a> and a citation, retained in its true body.</p><p><a href="/smc/?Section=01.01.020">Section 01.01.020</a> Effect<br>Second operative paragraph includes sufficient legal words.</p></div>'''
class Revision(unittest.TestCase):
 def test_closing_inventory_same_ids_changed_heading_is_not_consistent(self):
  from spokane_bulk import form,validate_chain
  from urllib.parse import urlencode
  def source(kind,value,label):return ('<form name="formSMC" method="post" action="/smc/"><table><tr><td><input name="'+kind+'" value="'+value+'"><a href="/smc/?'+kind+'='+value+'">'+label+'</a></td></tr></table></form>').encode()
  raw=[source('Title','01','Title 01 General'),source('Chapter','01.01','Chapter 01.01 Adoption'),source('Section','01.01.010','Section 01.01.010 Adoption')];phases=[];labels={}
  with tempfile.TemporaryDirectory() as tmp:
   out=pathlib.Path(tmp)
   for n,data in enumerate(raw):(out/(str(n)+'.bin')).write_bytes(data)
   for n,kind in enumerate(['Title','Chapter']):
    target,fields,disabled,heading=form(raw[n],C['source_url'],kind);labels[kind]=heading;phases.append({'selection_kind':kind,'form_source_ref':str(n)+'.bin','response_ref':str(n+1)+'.bin','target':target,'fields':fields,'disabled':disabled});(out/(str(n+1)+'.receipt.json')).write_text(json.dumps({'url':target,'post_fields':fields,'post_body_sha256':hashlib.sha256(urlencode([(k,v) for k,v in fields]).encode()).hexdigest()}))
   labels['Section']=form(raw[2],C['source_url'],'Section')[3];initial={'source_url':C['source_url'],'phases':phases,'heading_labels':labels,'expected_sections':['01.01.010'],'disabled_section_ids':[],'source_section_controls':section_controls(raw[2])[1]};self.assertTrue(validate_chain(out,phases,initial));(out/'2.bin').write_bytes(raw[2].replace(b'Adoption',b'Revised adoption'));self.assertFalse(validate_chain(out,phases,initial))
 def test_actual_retained_closing_pair_ignores_transport_bytes_but_detects_legal_drift(self):
  from collect import projection
  from bs4 import BeautifulSoup
  base=pathlib.Path(__file__).resolve().parent/'fixtures';context=json.loads((base/'spokane-title05a-context.json').read_text());start=(base/'spokane-title05a-start.html').read_bytes();end=(base/'spokane-title05a-end.html').read_bytes()
  self.assertNotEqual(start,end);a,_=parse(start,context['item'],context['config']);b,_=parse(end,context['item'],context['config']);self.assertEqual(projection(a),projection(b));self.assertEqual(len(a),31)
  soup=BeautifulSoup(end,'html.parser');node=soup.select_one('#hideRepealed');text=next(t for t in node.find_all(string=True) if 'shall' in str(t));text.replace_with(str(text).replace('shall','shall NOT',1));changed,_=parse(str(soup).encode(),context['item'],context['config']);self.assertNotEqual(projection(a),projection(changed))
 def test_native_heading_and_body_citation_have_distinct_ownership(self):
  rows,_=parse(RAW,I,C);self.assertEqual(len(rows),2);self.assertIn('Section 01.01.020',rows[0]['text']);self.assertEqual(rows[0]['links'][0]['text'],'Section 01.01.020');self.assertEqual(rows[1]['heading'],'Effect');self.assertTrue(rows[0]['source_text_conservation']['all_source_links_accounted_for'])
 def test_toc_title_mismatch_is_fatal(self):
  with self.assertRaisesRegex(ValueError,'differs from exact source TOC'):parse(RAW.replace(b' Effect<br>',b' Wrong title<br>'),I,C)
 def test_duplicate_source_controls_retain_occurrences_and_label_variants(self):
  raw=b'<form name="formSMC"><table><tr><td><input name="Section" value="01.01.010"><a href="/?Section=01.01.010">Section 01.01.010</a> First</td></tr><tr><td><input name="Section" value="01.01.010"><a href="/?Section=01.01.010">Section 01.01.010</a> Second</td></tr></table></form>'
  variants,occurrences,aliases=section_controls(raw);self.assertEqual(len(occurrences),2);self.assertEqual(len(aliases),1);self.assertEqual(len(variants['01.01.010']),2)
if __name__=='__main__':unittest.main(verbosity=2)
