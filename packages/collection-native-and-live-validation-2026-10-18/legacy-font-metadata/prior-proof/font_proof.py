"""Isolated finite original-PDF font-table identity proof; never renders glyphs.

No alphabet shift, installed-font lookup, other-edition text, contour recognition,
image API or lexical guess supplies a Unicode character. Only an explicit cmap
from another embedded instance of the SAME font face/version in this exact PDF
can witness a CID's identical GID, raw glyf bytes and advance/LSB metrics.
"""
import collections,hashlib,io,json,re
from fontTools.ttLib import TTFont
from pypdf import PdfReader
SOURCE_SHA256='877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102'
PAIRS=((620,623),(628,626))
def digest(b):return hashlib.sha256(b).hexdigest()
def face(name):return re.sub(r'^/?[A-Z]{6}\+','',str(name)).removeprefix('/')
def names(font):
 return sorted({(n.nameID,face(n.toUnicode())) for n in font['name'].names if n.nameID in [1,2,3,4,5,6]})
def fonts(reader):
 result={}
 for page in reader.pages:
  for _,ref in page.get('/Resources',{}).get('/Font',{}).items():result[ref.idnum]=ref.get_object()
 return result
def load_font(font):
 descendant=font['/DescendantFonts'][0].get_object() if '/DescendantFonts' in font else font
 descriptor=descendant['/FontDescriptor'];stream=descriptor['/FontFile2'];data=stream.get_data();return TTFont(io.BytesIO(data)),descendant,descriptor,digest(data)
def glyph_bytes(font,gid):
 offsets=font['loca'].locations;return font.reader['glyf'][offsets[gid]:offsets[gid+1]]
def derive(data):
 if digest(data)!=SOURCE_SHA256:raise ValueError('Exact original native source SHA required; no other edition accepted')
 reader=PdfReader(io.BytesIO(data),strict=True);resources=fonts(reader);proof=[]
 for bad_id,good_id in PAIRS:
  bad,good=resources[bad_id],resources[good_id];a,desc,fd,a_sha=load_font(bad);b,gd,gfd,b_sha=load_font(good)
  try:
   assert bad['/Subtype']=='/Type0' and bad['/Encoding']=='/Identity-H' and desc['/CIDToGIDMap']=='/Identity'
   assert '/ToUnicode' not in bad and 'cmap' not in a and 'post' not in a,'Recovery cannot override existing original encoding semantics'
   assert good['/Subtype']=='/TrueType' and good['/Encoding']=='/WinAnsiEncoding'
   assert face(bad['/BaseFont'])==face(good['/BaseFont']) and names(a)==names(b),'Different declared embedded font face/version'
   assert a['head'].fontRevision==b['head'].fontRevision and a['head'].unitsPerEm==b['head'].unitsPerEm and a['maxp'].numGlyphs==b['maxp'].numGlyphs
   unicode_by_gid=collections.defaultdict(set)
   for cm in b['cmap'].tables:
    if cm.isUnicode():
     for uni,glyph in cm.cmap.items():unicode_by_gid[b.getGlyphID(glyph)].add(uni)
   accepted=[];rejected=[]
   for gid,unicodes in sorted(unicode_by_gid.items()):
    ra,rb=glyph_bytes(a,gid),glyph_bytes(b,gid);ma=a['hmtx'].metrics[a.getGlyphName(gid)];mb=b['hmtx'].metrics[b.getGlyphName(gid)]
    reasons=[]
    if len(unicodes)!=1:reasons.append('Unicode cmap aliases are not unique')
    if ra!=rb:reasons.append('Raw embedded glyf bytes differ or missing in target subset')
    if ma!=mb:reasons.append('Source advance/LSB metrics differ')
    if not ra and unicodes!={32}:reasons.append('Empty glyph is not uniquely witnessed U+0020 space')
    if (ra and int.from_bytes(ra[:2],'big',signed=True)<0) or (rb and int.from_bytes(rb[:2],'big',signed=True)<0):reasons.append('Composite glyph needs separately established component closure; refused here')
    entry={'cid':gid,'gid':gid,'unicode_codepoints':sorted(unicodes),'target_glyf_sha256':digest(ra),'witness_glyf_sha256':digest(rb),'target_glyf_bytes':len(ra),'witness_glyf_bytes':len(rb),'target_advance_lsb':list(ma),'witness_advance_lsb':list(mb)}
    if reasons:entry['rejection_reasons']=reasons;rejected.append(entry)
    else:entry['unicode']=chr(next(iter(unicodes)));accepted.append(entry)
   proof.append({'target_font_object':bad_id,'witness_font_object':good_id,'font_face':face(bad['/BaseFont']),'source_font_program_sha256':a_sha,'witness_font_program_sha256':b_sha,'source_has_ToUnicode':False,'source_has_cmap':False,'source_has_post':False,'same_font_revision':a['head'].fontRevision,'same_units_per_em':a['head'].unitsPerEm,'same_full_glyph_count':a['maxp'].numGlyphs,'witness_cmap_table_sha256':digest(b.reader['cmap']),'normalized_source_font_names':names(a),'accepted':accepted,'rejected':rejected})
  finally:a.close();b.close()
 return {'schema_version':1,'native_source_sha256':SOURCE_SHA256,'proof_method':'Exact same-original-PDF face/version, CIDToGIDMap Identity, unique explicit Unicode cmap witness, identical GID raw glyf bytes and hmtx metrics. No visual recognition or alphabet/lexical inference.','pairs':proof,'publication_complete':False,'full_font_Unicode_recovered':False}
def validate(data,proof):
 if derive(data)!=proof:raise ValueError('Finite font proof mismatch; source or mapping changed')
 return proof
def decoder_from_original(data,proof=None):
 """Validate source and finite mappings before exposing diagnostic decoding.
 The returned closure copies only validated CID/Unicode values; later mutation
 of a caller's proof dictionary cannot change a decoding decision.
 """
 actual=derive(data) if proof is None else validate(data,proof)
 maps={p['target_font_object']:{e['cid']:e['unicode'] for e in p['accepted']} for p in actual['pairs']}
 def decode(raw,font_object):
  if len(raw)%2:raise ValueError('Identity-H source byte sequence must have even length')
  if font_object not in maps:raise ValueError('Unqualified font object')
  mapping=maps[font_object];units=[]
  for i in range(0,len(raw),2):
   cid=int.from_bytes(raw[i:i+2],'big');units.append({'source_byte_offset':i,'cid':cid,'unicode':mapping.get(cid),'qualified':cid in mapping})
  return units
 return decode
