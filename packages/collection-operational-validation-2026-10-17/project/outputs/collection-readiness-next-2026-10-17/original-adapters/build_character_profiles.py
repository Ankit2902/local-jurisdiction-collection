"""Build finite trusted source profiles from qualified source-PDF contexts, never global font mappings."""
import argparse,collections,re,unicodedata
from pathlib import Path
from bs4 import BeautifulSoup
from source_common import *
from model import dom_text

def run(report,out):
 path=Path(report);data=load(path);out=Path(out)
 if out.exists():raise ValueError('Fresh source-character profile required')
 word=[];html=[]
 for row in data['records']:
  rr=row['symbol_recoveries']
  if not rr or not all(r['qualified'] for r in rr):continue
  entry={k:row[k] for k in ['source_document_id','source_native_sha256','source_html_sha256','source_xml_sha256','word_source_ordinal','source_pdf_sha256','source_pdf_url','source_html_owner_record_id','source_html_owner_section','original_word_literal']};entry['recoveries']=rr;word.append(entry)
  outer=row['html_literal_pairs'][0];fragments=[outer] if 'html_block_index' in outer else outer['pairs'];pos=0
  for part in fragments:
   fragment=part['source_html_fragment'];bs=BeautifulSoup(fragment,'html.parser');nodes=[n for n in bs.find_all(True) if re.search(r'font-family\s*:[^;]*Symbol\b',str(n.get('style','')),re.I) or str(n.get('face','')).lower()=='symbol'];variants=part['variants'];needed=rr[pos:pos+len(variants)]
   if len(nodes)!=len(variants) or len(needed)!=len(variants):raise ValueError('Known HTML font span/context ownership mismatch')
   replacements=[]
   for node,var,qualified in zip(nodes,variants,needed):
    c=qualified['candidates'][0];value=c['pdf_character']
    if dom_text(node)!=var['published_html_character'] or var['word_char_hex']!=qualified['original_word_code']:raise ValueError('Original HTML/Word literal binding mismatch')
    if len(value)!=1 or unicodedata.category(value) in ['Co','Cc','Cs','Cn'] or ord(value) not in c['font']['explicit_unicode_values']:raise ValueError('Unqualified/private Unicode destination')
    replacements.append({'source_span_sha256':sha(str(node).encode()),'original_literal':var['published_html_character'],'recovered_literal':value,'original_word_code':qualified['original_word_code'],'source_pdf_page':c['page'],'source_pdf_context':c['context'],'source_pdf_context_sha256':c['context_sha256'],'source_font_cmap_sha256':c['font']['to_unicode_sha256'],'source_font_base':c['font']['base_font']})
   locator={k:part[k] for k in ['html_block_index','table_index','row_index','cell_index'] if k in part};html.append({'source_document_id':row['source_document_id'],'source_html_sha256':row['source_html_sha256'],'source_fragment_sha256':part.get('html_block_sha256',part.get('html_cell_sha256')),**locator,'source_native_sha256':row['source_native_sha256'],'source_xml_sha256':row['source_xml_sha256'],'source_pdf_sha256':row['source_pdf_sha256'],'replacements':replacements});pos+=len(variants)
  if pos!=len(rr):raise ValueError('Incomplete finite symbol profile')
 result={'schema':'king-finite-source-character-profiles-1','source_recovery_report_sha256':sha(path.read_bytes()),'scope':'Exact original source hashes/XML/context only. No source-font-name global substitution. Private-use/control/unassigned symbols remain unqualified.','qualified_characters':sum(len(w['recoveries']) for w in word),'unqualified_source_symbols':data['unqualified_symbols'],'word':word,'html':html};save(out,result);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--report',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.report,a.out);print(r['qualified_characters'],len(r['word']),len(r['html']))
