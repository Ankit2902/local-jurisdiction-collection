"""Original-font metadata-only search and finite CID/native probes. Never operative text."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,io,json,re,sys
from unittest.mock import patch,PropertyMock
import pdfplumber,pypdfium2 as pdfium,pypdfium2.raw as raw
from pdfminer.pdftypes import PDFStream
from pypdf import PdfReader
from pypdf.generic import IndirectObject,EncodedStreamObject
from pypdf._page import PageObject
from fontTools.ttLib import TTFont
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'prior-proof'))
from font_proof import derive,fonts,load_font,face,names,glyph_bytes,decoder_from_original
SOURCE_SHA='877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102'
PRIOR_MANIFEST='2d29388868e879debedbb3a8f56731f4849dea1ca42d3fd77dd74ec96857f53e'
SELECTED=[9,38,107,169,170]
SHA=lambda x:hashlib.sha256(x).hexdigest()
def read(p):return json.loads(p.read_text())
def canon(v):return json.loads(json.dumps(v,sort_keys=True))
def original_bytes(v):return bytes(v) if isinstance(v,bytes) else v.original_bytes if isinstance(v,str) else None

def explicit_cmap(font):
 """Only actual cmap records. Synthesized fontTools glyph names are not evidence."""
 entries=[]
 if 'cmap'not in font:return entries
 for cm in font['cmap'].tables:
  for code,glyph in sorted(cm.cmap.items()):
   if cm.isUnicode():uni=code;authority='Original explicit Unicode cmap'
   elif (cm.platformID,cm.platEncID)==(1,0) and 0<=code<=255:
    uni=ord(bytes([code]).decode('mac_roman'));authority='Original explicit Macintosh cmap with declared standard MacRoman code semantics'
   else:continue
   entries.append({'source_code':code,'unicode':uni,'gid':font.getGlyphID(glyph),'platform':cm.platformID,'encoding':cm.platEncID,'format':cm.format,'authority':authority})
 return entries

def metadata(reader):
 resources=fonts(reader);xref_fonts={};descriptors={};errors=[];allrefs={(g,i) for g,table in reader.xref.items() for i in table if i>0};allrefs|={(0,i) for i in reader.xref_objStm}
 for generation,i in sorted(allrefs):
  try:o=reader.get_object(IndirectObject(i,generation,reader))
  except Exception as e:errors.append({'object':i,'generation':generation,'error_type':type(e).__name__});continue
  if not isinstance(o,dict):continue
  if o.get('/Type')=='/Font':xref_fonts[i]=o
  if o.get('/Type')=='/FontDescriptor':descriptors[i]=o
 programs={};census=[]
 for i,f in sorted(xref_fonts.items()):
  desc=f['/DescendantFonts'][0].get_object() if '/DescendantFonts'in f else f;fd=desc.get('/FontDescriptor',{});tounicode=f['/ToUnicode'].get_data() if '/ToUnicode'in f else None
  info={'font_object':i,'resource_referenced':i in resources,'subtype':str(f.get('/Subtype')),'base_font':str(f.get('/BaseFont')),'face':face(f.get('/BaseFont')),'encoding':str(f.get('/Encoding')),'CIDToGIDMap':str(desc.get('/CIDToGIDMap')),'ToUnicode_present':tounicode is not None,'ToUnicode_sha256':SHA(tounicode) if tounicode is not None else None,'font_program_embedded':any(k in fd for k in ['/FontFile','/FontFile2','/FontFile3']),'font_program_kinds':[k for k in ['/FontFile','/FontFile2','/FontFile3'] if k in fd]}
  if '/FontFile2'in fd:
   t,_,_,sha=load_font(f);programs[i]=t
   info.update({'font_program_sha256':sha,'font_names':names(t),'revision':t['head'].fontRevision,'units_per_em':t['head'].unitsPerEm,'glyph_count':t['maxp'].numGlyphs,'font_table_tags':list(t.keys()),'cmap_records':[{'platform':c.platformID,'encoding':c.platEncID,'format':c.format,'entries':len(c.cmap),'unicode':c.isUnicode()} for c in t['cmap'].tables] if 'cmap'in t else [],'post_format':t['post'].formatType if 'post'in t else None,'post_explicit_glyph_names_available':'post'in t and t['post'].formatType!=3.0,'explicit_semantic_cmap_entries':explicit_cmap(t)})
  census.append(info)
 return resources,xref_fonts,programs,census,{'xref_object_metadata_examined':len(allrefs),'resource_font_objects':sorted(resources),'xref_font_objects':sorted(xref_fonts),'xref_font_descriptor_objects':sorted(descriptors),'metadata_errors':errors}

def search(resources,programs,census,prior):
 by={m['font_object']:m for m in census};result=[]
 for pair in prior['pairs']:
  target=pair['target_font_object'];a=programs[target];f=resources[target];old={e['cid']:e['unicode'] for e in pair['accepted']};witnesses=[];accepted=defaultdict(list)
  for wid,b in programs.items():
   if wid==target or not by[wid]['explicit_semantic_cmap_entries']:continue
   identity=(face(f['/BaseFont'])==by[wid]['face'] and names(a)==names(b) and a['head'].fontRevision==b['head'].fontRevision and a['head'].unitsPerEm==b['head'].unitsPerEm and a['maxp'].numGlyphs==b['maxp'].numGlyphs)
   evidence={'font_object':wid,'declared_same_face_version_units_and_glyph_count':identity,'face':by[wid]['face'],'explicit_cmap_entries':len(by[wid]['explicit_semantic_cmap_entries']),'post_format':by[wid]['post_format'],'accepted':[],'rejected':[]}
   if identity:
    meanings=defaultdict(set);authorities=defaultdict(list)
    for e in by[wid]['explicit_semantic_cmap_entries']:meanings[e['gid']].add(e['unicode']);authorities[e['gid']].append(e)
    for gid,unis in sorted(meanings.items()):
     ra=glyph_bytes(a,gid);rb=glyph_bytes(b,gid);ma=a['hmtx'].metrics[a.getGlyphName(gid)];mb=b['hmtx'].metrics[b.getGlyphName(gid)];reasons=[]
     if len(unis)!=1:reasons.append('Nonunique explicit Unicode witness')
     if ra!=rb:reasons.append('Exact original raw glyf bytes differ/missing')
     if ma!=mb:reasons.append('Original source advance/LSB metrics differ')
     if not ra and unis!={32}:reasons.append('Empty glyph has no unique original U+0020 witness')
     if any(z and int.from_bytes(z[:2],'big',signed=True)<0 for z in [ra,rb]):reasons.append('Unestablished composite closure')
     r={'cid':gid,'unicode_codepoints':sorted(unis),'target_glyf_sha256':SHA(ra),'witness_glyf_sha256':SHA(rb),'target_metrics':list(ma),'witness_metrics':list(mb),'original_cmap_authorities':authorities[gid]}
     if reasons:r['rejection_reasons']=reasons;evidence['rejected'].append(r)
     else:r['unicode']=chr(next(iter(unis)));evidence['accepted'].append(r);accepted[gid].append(r['unicode'])
   else:evidence['rejection_reason']='Different declared original font face/version; cross-font glyph/width guessing prohibited'
   witnesses.append(evidence)
  mapping={cid:vals[0] for cid,vals in accepted.items() if len(set(vals))==1};assert all(mapping.get(cid)==u for cid,u in old.items()),'Prior exact original mappings must remain supported'
  result.append({'target_font_object':target,'known_mapping_count':len(old),'all_metadata_supported_mapping_count':len(mapping),'new_source_supported_mappings':[{'cid':cid,'unicode':u} for cid,u in mapping.items() if cid not in old],'all_source_mapping':{str(cid):u for cid,u in sorted(mapping.items())},'witnesses':witnesses,'target_ToUnicode_cmap_post_absent':all(not by[target].get(k) for k in ['ToUnicode_present','cmap_records','post_format'])})
 return result

def unresolved_inventory(ledger,searches,programs,census):
 unresolved=defaultdict(list);by={m['font_object']:m for m in census};mapping={s['target_font_object']:{int(cid):u for cid,u in s['all_source_mapping'].items()} for s in searches}
 for row in ledger:
  for unit in row['units']:
   if not unit['qualified']:unresolved[(row['source_font_object'],unit['cid'])].append({'physical_page':row['physical_page'],'operator_index':row['page_content_operator_index_zero_based'],'string_operand_index':row['string_operand_index_zero_based'],'source_byte_offset':unit['source_byte_offset'],'source_operand_sha256':row['source_operand_sha256']})
 out=[]
 for (font,cid),positions in sorted(unresolved.items()):
  t=programs[font];g=glyph_bytes(t,cid);metric=t['hmtx'].metrics[t.getGlyphName(cid)];same=[s for s in next(s for s in searches if s['target_font_object']==font)['witnesses'] if s['declared_same_face_version_units_and_glyph_count']]
  out.append({'source_font_object':font,'cid':cid,'GID':cid,'source_CIDToGIDMap':'Identity','occurrences':len(positions),'physical_pages':sorted({x['physical_page'] for x in positions}),'first_source_position':positions[0],'all_source_positions':positions,'target_raw_glyf_sha256':SHA(g),'target_glyf_bytes':len(g),'target_contour_kind':'composite' if g and int.from_bytes(g[:2],'big',signed=True)<0 else 'simple_or_empty','target_advance_lsb':list(metric),'fontTools_display_name_not_source_glyph_name':t.getGlyphName(cid),'source_semantic_glyph_name_available':False,'same_face_witness_font_objects':[m['font_object'] for m in same],'explicit_same_face_cmap_witnesses_for_CID':[e for m in same for e in by[m['font_object']]['explicit_semantic_cmap_entries'] if e['gid']==cid],'Unicode':mapping[font].get(cid),'qualified':cid in mapping[font],'reason':'No explicit original same-face Unicode/MacRoman cmap or glyph-name witness for this GID. Target lacks ToUnicode/cmap/post; witness post format3 has no names. CID integer, generated glyphNNNN name, width alone, other font face and legal/alphabet context are not Unicode authority.'})
 return out

def finite_probes(reader,source,ledger,prior):
 decode=decoder_from_original(source,prior);actual=[];native=[];font_names={str(f.get('/BaseFont')).removeprefix('/'):i for i,f in fonts(reader).items() if i in [620,628]};doc=pdfium.PdfDocument(source)
 try:
  with pdfplumber.open(io.BytesIO(source)) as pdf:
   for n in SELECTED:
    page=reader.pages[n-1];refs=page.get('/Resources',{}).get('/Font',{});current=None;stack=[];selected=[];forms=[]
    for oi,(operands,op) in enumerate(page.get_contents().operations):
     if op==b'q':stack.append(current)
     elif op==b'Q':current=stack.pop() if stack else None
     elif op==b'Tf':current=refs.get(str(operands[0])).idnum
     elif op==b'Do':forms.append(str(operands[0]))
     elif op in [b'Tj',b'TJ',b"'",b'"'] and current in [620,628]:
      values=operands[0] if op==b'TJ' else [operands[-1]]
      for si,value in enumerate(values):
       rawbytes=original_bytes(value)
       if rawbytes is None:continue
       units=decode(rawbytes,current);selected.append({'all_units_qualified':all(u['qualified'] for u in units),'diagnostic_only':True,'native_source_sha256':SOURCE_SHA,'operator':op.decode(),'page_content_operator_index_zero_based':oi,'physical_page':n,'source_font_object':current,'source_operand_sha256':SHA(rawbytes),'source_text_substituted':False,'string_operand_index_zero_based':si,'units':units})
    expected=[row for row in ledger if row['physical_page']==n];assert selected==expected,'Finite original text-operator positions/CID units drift from retained ledger';assert not forms,'Finite untraversed XObject invocation requires explicit new scope';actual.extend(selected)
    pp=pdf.pages[n-1].dedupe_chars(tolerance=.5);chars=[c for c in pp.chars if c['fontname']in font_names];np=doc[n-1];tp=np.get_textpage()
    try:
     ng=[]
     for ni in range(tp.count_chars()):
      if raw.FPDFText_IsGenerated(tp,ni):continue
      code=int(raw.FPDFText_GetUnicode(tp,ni));b=list(map(float,tp.get_charbox(ni)));ng.append({'index':ni,'raw_native_codepoint':code,'bbox':b,'source_center':[(b[0]+b[2])/2,float(pp.height)-(b[1]+b[3])/2]})
     probes=[]
     for ci,c in enumerate(chars):
      match=re.fullmatch(r'\(cid:(\d+)\)',c['text']);assert match,'Unexpected independent extractor Unicode in target font; do not overwrite original semantics';cid=int(match.group(1));hits=[x for x in ng if c['x0']<=x['source_center'][0]<=c['x1'] and c['top']<=x['source_center'][1]<=c['bottom']];exact=[x for x in hits if x['raw_native_codepoint']==cid]
      probes.append({'glyph_ordinal':ci+1,'source_font_object':font_names[c['fontname']],'cid':cid,'pdfminer_source_text':c['text'],'source_bbox':[float(c[k]) for k in ['x0','top','x1','bottom']],'native_geometry_candidates':hits,'native_raw_CID_passthrough_matches':exact,'native_output_is_not_Unicode_witness':True,'prior_mapping_diagnostic_unicode':decode(cid.to_bytes(2,'big'),font_names[c['fontname']])[0]['unicode']})
     native.append({'physical_page':n,'source_target_glyphs':len(chars),'native_target_CID_passthrough_geometry_matches':sum(bool(x['native_raw_CID_passthrough_matches']) for x in probes),'native_target_geometry_unresolved':sum(not x['native_raw_CID_passthrough_matches'] for x in probes),'image_objects_metadata_only':len(pp.images),'native_page_stream_sha256':SHA(tp.get_text_range().encode()),'probes':probes,'page_text_rewritten':False})
    finally:tp.close();np.close()
 finally:doc.close()
 return actual,native

def study():
 source=(HERE/'source/legacy-upoc.pdf').read_bytes();assert SHA(source)==SOURCE_SHA,'Only exact original legacy PDF accepted';m=read(HERE/'prior-proof/MANIFEST.json');assert SHA((HERE/'prior-proof/MANIFEST.json').read_bytes())==PRIOR_MANIFEST;assert all(SHA((HERE/'prior-proof'/name).read_bytes())==h for name,h in m['files'].items());ledger=[json.loads(l) for l in (HERE/'prior-proof/source-CID-recovery-ledger.jsonl').read_text().splitlines()];counts=Counter(u['qualified'] for row in ledger for u in row['units']);assert len(ledger)==814 and counts=={True:3382,False:4447};calls=[];miner_get=PDFStream.get_data;pdf_get=EncodedStreamObject.get_data
 def no(*a,**kw):calls.append('forbidden');raise AssertionError('No network/image/render/OCR')
 def mg(s):
  if getattr(s.attrs.get('Subtype'),'name',None)=='Image':return no()
  return miner_get(s)
 def pg(s,*a,**kw):
  if s.get('/Subtype')=='/Image':return no()
  return pdf_get(s,*a,**kw)
 with patch('socket.socket',side_effect=no),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=no),patch.object(pdfium.PdfPage,'render',side_effect=no),patch.object(pdfium.PdfPage,'get_objects',side_effect=no),patch.object(pdfium.PdfImage,'get_bitmap',side_effect=no),patch.object(pdfium.PdfImage,'extract',side_effect=no),patch.object(PDFStream,'get_data',mg),patch.object(EncodedStreamObject,'get_data',pg):
  prior=derive(source);assert canon(prior)==read(HERE/'prior-proof/font-proof.json');reader=PdfReader(io.BytesIO(source),strict=True);resources,xrefs,programs,census,census_scope=metadata(reader)
  try:searched=search(resources,programs,census,prior);inventory=unresolved_inventory(ledger,searched,programs,census);operators,native=finite_probes(reader,source,ledger,prior)
  finally:
   for t in programs.values():t.close()
 assert not calls and SHA((HERE/'source/legacy-upoc.pdf').read_bytes())==SOURCE_SHA
 return {'schema_version':1,'native_source_sha256':SOURCE_SHA,'prior_proof_manifest_sha256':PRIOR_MANIFEST,'prior30mapping_proof_reproduces_exactly':True,'metadata_census_scope':census_scope,'font_metadata':census,'source_semantic_mapping_search':searched,'unresolved_CID_inventory':inventory,'finite_actual_operator_rows':operators,'finite_native_probes':native,'selected_body_pages':SELECTED,'source_known_occurrences_carried_from_retained_ledger':3382,'source_unresolved_occurrences_carried_from_retained_ledger':4447,'new_Unicode_mappings':sum(len(s['new_source_supported_mappings']) for s in searched),'full102page_content_reparse':False,'no_current_edition_or_installed_font_substitution':True,'no_source_PDF_or_legal_text_rewrite':True,'network_image_decode_extract_render_OCR_calls':calls,'scope':'Original embedded font/XRef metadata and finite5 original body pages only; no render/OCR/lexical/alphabet inference; precise source inventory, not operative text recovery'}
def main():
 result=study();out=HERE/'STUDY.json';assert not out.exists();out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n');summary={'passed':True,'source_sha256':SOURCE_SHA,'font_resource_count':len(result['metadata_census_scope']['resource_font_objects']),'xref_font_count':len(result['metadata_census_scope']['xref_font_objects']),'new_source_backed_Unicode_mappings':result['new_Unicode_mappings'],'known_mappings_preserved':30,'known_occurrences_retained':3382,'unresolved_distinct_font_CID_pairs':len(result['unresolved_CID_inventory']),'unresolved_occurrences_retained':sum(x['occurrences'] for x in result['unresolved_CID_inventory']),'finite_body_pages':SELECTED,'finite_actual_text_runs':len(result['finite_actual_operator_rows']),'native_CID_passthrough_geometry_matches':sum(x['native_target_CID_passthrough_geometry_matches'] for x in result['finite_native_probes']),'native_geometry_unresolved':sum(x['native_target_geometry_unresolved'] for x in result['finite_native_probes']),'font_metadata_errors':result['metadata_census_scope']['metadata_errors'],'native_output_not_used_as_Unicode_authority':True,'full102page_content_reparse':False,'image_network_render_OCR_calls':0,'study_sha256':SHA(out.read_bytes()),'study_program_sha256':SHA(Path(__file__).read_bytes())};(HERE/'SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=='__main__':main()
