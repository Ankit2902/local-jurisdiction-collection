"""Exact original font/CID/position ligature reconciliation; no broad normalization."""
import copy,json
from pathlib import Path
from unittest.mock import patch
import pymupdf
import audit_pdf_tags
from pdf_tags import parse
from audit_pdf_tags import audit
def tests():
 data=(Path(__file__).parent/'fixtures/derived-f-f-font.pdf').read_bytes();document=parse(data);assert document['available_figure_text'][0]['original_glyph_text']=='Coffee';assert document['logical_text']=='[IMAGE]';report=audit(data,document);assert report['passed'] and report['source_encoding_resolved_native_variants']==1 and report['native_pages_strict_raw_unicode_equal']==0;variant=report['native_page_checks'][0]['source_encoding_variants'][0];assert variant['original_font_encoding']['source_glyph_name']=='/f_f' and variant['reader_font_CID_and_position']['source_cid']==31 and variant['native_glyph']['unicode']=='\ufb00' and variant['resolved_by_source_encoding'];results=[{'name':'original_Type1_Differences_f_f_CID31_native_ligature_same_font_and_position_retains_both_unicode_variants','passed':True}]
 original=audit_pdf_tags.native_variant_metadata
 def wrong_font(*a):return dict(original(*a),font_name='WrongFont')
 with patch.object(audit_pdf_tags,'native_variant_metadata',wrong_font):
  wrong=audit(data,document);assert not wrong['passed'] and wrong['source_encoding_resolved_native_variants']==0;results.append({'name':'different_native_reader_font_cannot_resolve_unicode_variant','passed':True})
 def moved(*a):
  value=original(*a);value['x']+=5;return value
 with patch.object(audit_pdf_tags,'native_variant_metadata',moved):
  wrong=audit(data,document);assert not wrong['passed'] and wrong['source_encoding_resolved_native_variants']==0;results.append({'name':'different_glyph_position_cannot_resolve_unicode_variant','passed':True})
 changed=copy.deepcopy(document);changed['available_figure_text'][0]['original_glyph_text']='Co\ufb00ee';assert not audit(data,changed)['passed'];results.append({'name':'native_ligature_does_not_replace_exact_source_unicode_label_ledger','passed':True})
 return {'schema_version':1,'kind':'Synthetic derived-font original-encoding binding faults; not whole-publication proof','passed':True,'count':len(results),'tests':results}
if __name__=='__main__':
 result=tests();Path(__file__).with_name('pdf-encoding-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
