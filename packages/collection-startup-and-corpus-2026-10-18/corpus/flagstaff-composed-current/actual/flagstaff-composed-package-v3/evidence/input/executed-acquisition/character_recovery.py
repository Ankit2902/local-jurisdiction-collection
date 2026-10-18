"""Finite source-hash/XML/context-bound character recovery, with original literals retained."""
import copy,functools,re,unicodedata
from pathlib import Path
from bs4 import NavigableString
from source_common import load,sha
from model import dom_text
@functools.lru_cache(maxsize=1)
def profiles():return load(Path(__file__).parent/'source_character_dispositions.json')
def valid_character(char):
 if len(char)!=1 or unicodedata.category(char) in ['Co','Cc','Cs','Cn']:raise ValueError('Private/control/unassigned source character cannot be semantically promoted')
 return char

def recover_word(document_id,native_sha256,unit):
 found=[p for p in profiles()['word'] if p['source_document_id']==document_id and p['source_native_sha256']==native_sha256 and p['word_source_ordinal']==unit['source_ordinal']]
 if not found:return unit
 if len(found)!=1:raise ValueError('Duplicate finite Word character profile')
 entry=found[0]
 if unit['source_xml_sha256']!=entry['source_xml_sha256'] or unit['text']!=entry['original_word_literal']:raise ValueError('Registered native character profile XML/literal binding mismatch')
 mapping={};counts={}
 for event in entry['recoveries']:
  if not event['qualified'] or len(event['candidates'])!=1:raise ValueError('Unqualified character profile event')
  candidate=event['candidates'][0];char=valid_character(candidate['pdf_character']);code=event['original_word_code']
  if ord(char) not in candidate['font']['explicit_unicode_values'] or not candidate['font']['to_unicode_sha256']:raise ValueError('Source PDF explicit ToUnicode binding absent')
  if code in mapping and mapping[code]!=char:raise ValueError('Mixed per-unit glyph mapping is unsupported')
  mapping[code]=char;counts[code]=counts.get(code,0)+1
 for code,count in counts.items():
  if unit['text'].count('[SYMBOL '+code+']')!=count:raise ValueError('Native source symbol occurrence count differs')
 result=copy.deepcopy(unit);result['original_symbol_text']=unit['text'];result['source_character_recovery']={k:entry[k] for k in ['source_native_sha256','source_xml_sha256','source_pdf_sha256','source_pdf_url','source_html_owner_section']};result['source_character_recovery']['events']=entry['recoveries']
 def replace(text):
  for code,char in mapping.items():text=text.replace('[SYMBOL '+code+']',char)
  return text
 result['text']=replace(result['text'])
 for table in result['tables']:
  for row in table['rows']:
   for cell in row:cell['text']=replace(cell['text'])
 return result

def recover_html(document_id,html_sha256,body,units):
 events=[];unit_ids={id(b):i for i,b in enumerate(units)};tables=body.find_all('table')
 entries=[p for p in profiles()['html'] if p['source_document_id']==document_id and p['source_html_sha256']==html_sha256]
 for entry in entries:
  if 'html_block_index' in entry:target=units[entry['html_block_index']]
  else:
   table=tables[entry['table_index']];rows=[r for r in table.find_all('tr') if r.find_parent('table') is table];target=rows[entry['row_index']].find_all(['td','th'],recursive=False)[entry['cell_index']]
  if sha(str(target).encode())!=entry['source_fragment_sha256']:raise ValueError('Registered HTML character profile fragment binding mismatch')
  nodes=[n for n in [target]+target.find_all(True) if re.search(r'font-family\s*:[^;]*Symbol\b',str(n.get('style','')),re.I) or str(n.get('face','')).lower()=='symbol']
  if len(nodes)!=len(entry['replacements']):raise ValueError('Registered HTML source font span count differs')
  owner=target
  while owner is not None and id(owner) not in unit_ids:owner=owner.parent
  if owner is None:raise ValueError('Character recovery has no source block owner')
  for node,replacement in zip(nodes,entry['replacements']):
   value=valid_character(replacement['recovered_literal'])
   if sha(str(node).encode())!=replacement['source_span_sha256'] or dom_text(node)!=replacement['original_literal'] or any(not isinstance(c,NavigableString) for c in node.contents):raise ValueError('Registered HTML source font literal mismatch')
   original_attributes=dict(node.attrs);original_text=node.get_text();safe=original_text.replace(replacement['original_literal'],value)
   node.clear();node.append(NavigableString(safe))
   if node.get('style'):
    style=';'.join(p for p in node['style'].split(';') if not re.match(r'\s*font-family\s*:',p,re.I))
    if style.strip():node['style']=style
    else:del node['style']
   if str(node.get('face','')).lower()=='symbol':del node['face']
   node['data-source-character-recovery']=entry['source_xml_sha256']
   events.append({'block_index':unit_ids[id(owner)],'source_original_font_attributes':original_attributes,'source_html_sha256':html_sha256,'source_fragment_sha256':entry['source_fragment_sha256'],'source_native_sha256':entry['source_native_sha256'],'source_xml_sha256':entry['source_xml_sha256'],'source_pdf_sha256':entry['source_pdf_sha256'],**replacement})
 return events
