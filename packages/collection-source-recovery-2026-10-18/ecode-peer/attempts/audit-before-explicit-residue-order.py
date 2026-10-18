"""Independent original-source traversal vs frozen corrected IR (no producer import)."""
import sys
sys.dont_write_bytecode=True
import collections,copy,hashlib,json,re,time
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup,Comment,ProcessingInstruction,Declaration,NavigableString
ROOT=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');SOURCE=ROOT/'outputs/collection-readiness-post-91f6c59-2026-10-17/ecode/albany-image-context-replay-v2';TARGET=ROOT/'outputs/collection-readiness-post716cfcb-2026-10-17/ecode-recovery-audit-v1/albany-derived-v2';OUT=Path(__file__).resolve().parent
ID=re.compile(r'^([0-9]+)_content$');IMAGE=re.compile(r'\.(png|jpe?g|gif|svg|webp|avif|bmp|ico|tiff?)([?#]|$)',re.I)
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compact(s):return ''.join(x for x in s if not x.isspace())
def text(e):return ''.join(str(x) for x in e.descendants if isinstance(x,NavigableString) and not isinstance(x,(Comment,ProcessingInstruction,Declaration)))
def image_only(e):
 count=0
 # Actual source census proves only222 img +218ordinary image hyperlinks.
 for img in list(e.find_all('img')):assert not img.get('alt');img.replace_with(NavigableString('[IMAGE]'));count+=1
 for anchor in e.find_all('a'):
  if IMAGE.search(anchor.get('href','')):anchor.attrs.pop('href',None);anchor.append(NavigableString('[IMAGE]'));count+=1
 return count
def cells(e):
 ts=e.find_all('table');out=[]
 for table in ts:
  parent=table.find_parent('table');parent_index=ts.index(parent) if parent in ts else None;rows=[]
  for tr in table.find_all('tr'):
   if tr.find_parent('table') is table:rows.append([{'tag':c.name,'rowspan':str(c.get('rowspan','1')),'colspan':str(c.get('colspan','1')),'scope':c.get('scope'),'headers':c.get('headers'),'text':compact(text(c))} for c in tr.find_all(['td','th'],recursive=False)])
  out.append({'parent_table_index':parent_index,'rows':rows})
 return out
def note_nodes(e):return [x for x in e.find_all(True) if set(x.get('class',[]))&{'history','footnote','footnotes','note'}]
def legal_features(e,canonical=False):
 out=[]
 for x in e.find_all(True):
  classes=set(x.get('class',[]))
  if canonical and x.name not in ['div','section']:classes=set()
  if x.name in ['ol','ul','li','dl','dt','dd','dfn'] or classes&{'litem','litem_content','litem_number','defitem','defitem_content','defitem_number','definition','deftext','deflevel'}:
   out.append({'tag':x.name,'classes':sorted(classes&{'litem','litem_content','litem_number','defitem','defitem_content','defitem_number','definition','deftext','deflevel'}),'start':x.get('start'),'type':x.get('type'),'value':x.get('value'),'text':compact(text(x))})
 return out
start=time.time();cp=json.loads((SOURCE/'checkpoint.json').read_text());newcp=json.loads((TARGET/'checkpoint.json').read_text());records=[json.loads(x) for x in (TARGET/'records.jsonl').read_text().split('\n') if x];by={r['id']:r for r in records};oldby={r['id']:r for r in [json.loads(x) for x in (SOURCE/'records.jsonl').read_text().split('\n') if x]};disps={x['id']:x for x in json.loads((TARGET/'dispositions.json').read_text())};raw_hashes={a['path']:a['sha256'] for a in cp['artifacts']};assert raw_hashes=={a['path']:a['sha256'] for a in newcp['artifacts']}
errors=[];witness=[];outside=[];seen=set();counts=collections.Counter();changed=[]
for a in cp['artifacts']:
 if a['status']!=200:continue
 assert sh(SOURCE/a['path'])==a['sha256'];s=BeautifulSoup((SOURCE/a['path']).read_bytes(),'html.parser');code=s.find(id='codeContent');assert code
 roots=[e for e in code.find_all(True) if ID.fullmatch(e.get('id','')) and 'content' in e.get('class',[])]
 # Independent unowned source-text accounting; headers/TOC/date/UI are separately classified.
 for node in code.descendants:
  if not isinstance(node,NavigableString) or isinstance(node,(Comment,ProcessingInstruction,Declaration)) or not str(node).strip():continue
  ancestors=list(node.parents)
  if any(ID.fullmatch(p.get('id','')) and 'content' in p.get('class',[]) for p in ancestors if getattr(p,'attrs',None) is not None):continue
  kind=None
  for p in ancestors:
   if getattr(p,'attrs',None) is None:continue
   if p.get('id')=='toc':kind='publisher_TOC';break
   if p.get('id')=='displayDate':kind='publisher_currency';break
   if 'contentTitle' in p.get('class',[]):kind='publisher_heading';break
   if p.name in ['script','style','button','input'] or set(p.get('class',[]))&{'actions','selection-control'}:kind='UI_or_nonoperative_script_style';break
  if kind is None:outside.append({'path':a['path'],'text':str(node)[:250],'parent_tag':node.parent.name,'parent_id':node.parent.get('id'),'classes':node.parent.get('class',[])})
  else:counts['outside_classified:'+kind]+=1
 for original in roots:
  ident=ID.fullmatch(original['id'])[1];assert ident not in seen;seen.add(ident);own=copy.deepcopy(original)
  nested=[e for e in own.find_all(True) if ID.fullmatch(e.get('id','')) and 'content' in e.get('class',[])]
  counts['separate_owned_body_descendants']+=len(nested)
  for e in nested:e.decompose()
  # Source UI controls only, never non-GUID .content legal wrappers.
  for e in list(own.find_all(True)):
   if e.parent is not None and(e.name in ['script','style','button','input'] or set(e.get('class',[]))&{'actions','selection-control'}):e.decompose()
  raw_ids=[e['id'] for e in [own]+own.find_all(True) if e.get('id')];markers=image_only(own);source_chars=compact(text(own));r=by.get(ident)
  if r is None:
   if source_chars or own.find('table') or markers:errors.append({'id':ident,'field':'unemitted_original_body','chars':len(source_chars),'markers':markers})
   if disps[ident]['classification'] not in ['structural_empty','reserved_or_repealed_empty']:errors.append({'id':ident,'field':'empty_source_disposition'})
   counts['source_empty_body_dispositions']+=1;continue
  normalized=BeautifulSoup(r['semantic_html'],'html.parser');rich=BeautifulSoup(r['content_html'],'html.parser');normalized_text=compact(text(normalized));counts['acquired_owners']+=1
  if source_chars!=normalized_text:errors.append({'id':ident,'field':'original_legal_text_and_IMAGE_sequence','source_chars':len(source_chars),'output_chars':len(normalized_text)})
  st,nt=cells(own),cells(normalized)
  if st!=nt:errors.append({'id':ident,'field':'original_table_text_tag_spans_scope_headers_parent'})
  source_notes=[compact(text(x)) for x in note_nodes(own)];rich_notes=[compact(text(x)) for x in note_nodes(rich)];semantic_notes=[compact(text(x)) for x in note_nodes(normalized)]
  if source_notes!=rich_notes or source_notes!=semantic_notes or source_notes!=[compact(text(BeautifulSoup(x,'html.parser'))) for x in r['notes_html']]:errors.append({'id':ident,'field':'original_notes_history_text_order'})
  sf,rf=legal_features(own),legal_features(rich)
  if sf!=rf:errors.append({'id':ident,'field':'original_definition_list_role_class_and_number_attributes_in_rich_IR'})
  if legal_features(own,True)!=legal_features(normalized,True):errors.append({'id':ident,'field':'original_canonical_list_structural_tags_order_number_attributes'})
  def anchors(e,source=False):
   return [(urljoin(r['source_url'],x['href']),compact(text(x))) for x in e.find_all('a',href=True) if x['href'] and not IMAGE.search(x['href']) and not x['href'].endswith('#image-omitted')]
  if anchors(own)!=anchors(normalized):errors.append({'id':ident,'field':'original_legal_anchor_targets_labels_order'})
  rich_ids=[e['id'] for e in rich.find_all(True) if e.get('id')]
  if raw_ids!=rich_ids:errors.append({'id':ident,'field':'original_source_ID_occurrences','source':len(raw_ids),'output':len(rich_ids)})
  if markers!=r['image_placeholder_count'] or markers!=normalized_text.count('[IMAGE]'):errors.append({'id':ident,'field':'original_IMAGE_count'})
  counts['tables']+=len(st);counts['cells']+=sum(len(row) for t in st for row in t['rows']);counts['notes']+=len(source_notes);counts['source_ID_occurrences']+=len(raw_ids);counts['list_definition_structural_elements']+=len(sf);counts['IMAGE_positions']+=markers
  if compact(text(BeautifulSoup(oldby[ident]['semantic_html'],'html.parser')))!=source_chars:changed.append(ident)
  witness.append({'id':ident,'raw_path':a['path'],'raw_sha256':a['sha256'],'source_text_and_IMAGE_sequence_sha256':hashlib.sha256(source_chars.encode()).hexdigest(),'nonwhitespace_characters':len(source_chars),'tables':len(st),'notes':len(source_notes),'source_ID_occurrences':len(raw_ids),'IMAGE_positions':markers})
assert seen==set(disps)-{'AL0934'} and set(by)<seen
summary={'passed':not(errors or outside),'source_response_artifacts':len(cp['artifacts']),'successful_raw_HTML':400,'explicit_owned_GUID_bodies':len(seen),'counts':dict(counts),'old_IR_owners_that_fail_independent_source_text':len(changed),'historical_loss_owner_ids':changed,'unowned_unclassified_source_text':outside,'mismatches':errors,'raw_artifact_hashes_preserved':True,'corrected_records_sha256':sh(TARGET/'records.jsonl'),'corrected_frozen_manifest_sha256':sh(TARGET.parent/'DERIVATIVE-V2-MANIFEST.json'),'auditor_sha256':sh(Path(__file__)),'seconds':time.time()-start,'normalization_comparison':'Only literal whitespace characters removed for text conservation; punctuation/codepoints/order/images remain exact. Browser DOM cell whitespace audit is separate.','producer_imports_or_helpers':False,'canonical_class_scope':'Original list/definition CSS role classes preserved exactly in richcontent_html; canonical structural tags, number attributes, visible labels and links independently compared. Legacy semantic serializer omits CSS class on anchors, retaining their text/href and original role in richIR.','network_image_pixels_native_operations':0}
(OUT/'all-source-body-comparison.json').write_text(json.dumps(summary,indent=2)+'\n');(OUT/'all-source-body-witnesses.json').write_text(json.dumps(witness,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['historical_loss_owner_ids','mismatches','unowned_unclassified_source_text']},indent=2));print('MISMATCHES',errors[:10]);print('UNOWNED',outside[:10]);raise SystemExit(0 if summary['passed'] else 2)
