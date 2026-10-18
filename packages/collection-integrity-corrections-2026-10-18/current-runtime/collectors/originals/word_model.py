"""Native Word structural importer. Never reads/extracts image ZIP members or external images."""
import io,re,zipfile,xml.etree.ElementTree as ET
from pathlib import PurePosixPath
from source_common import sha,clean
from model import redact_image_metadata,legal_image_text
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';R='http://schemas.openxmlformats.org/officeDocument/2006/relationships';A='http://schemas.openxmlformats.org/drawingml/2006/main';NS={'w':W,'r':R,'a':A}
def local(tag):return tag.rsplit('}',1)[-1]
def ordered_text(node):
 out=[];images=[];notes=[]
 def walk(el,path):
  name=local(el.tag)
  if name=='AlternateContent':
   chosen=next((x for x in el if local(x.tag)=='Choice'),None)
   if chosen is None:chosen=next((x for x in el if local(x.tag)=='Fallback'),None)
   if chosen is None:raise ValueError('Empty Word alternate content')
   walk(chosen,path+'/selected-'+local(chosen.tag));return
  if name in ['drawing','pict','object']:
   out.append('[IMAGE]');images.append({'xml_path':path,'source_sha256':sha(ET.tostring(el)),'placeholder':'[IMAGE]','source_embedded_text_nodes':[legal_image_text(x.text or '') for x in el.iter() if local(x.tag) in ['t','delText'] and x.text],'source_descriptions':redact_image_metadata([{k:v for k,v in x.attrib.items() if local(k) in ['descr','title','name','alt']} for x in el.iter() if any(local(k) in ['descr','title','name','alt'] for k in x.attrib)],attribute_boundary=True),'relationship_ids':sorted(set(v for x in el.iter() for k,v in x.attrib.items() if k in ['{'+R+'}embed','{'+R+'}link','{'+R+'}id']))});return
  if name in ['t','delText']:
   original=el.text or '';safe=legal_image_text(original);out.append(safe)
   if safe!=original:images.extend({'xml_path':path,'source_sha256':sha(ET.tostring(el)),'placeholder':'[IMAGE]','kind':'quoted_inline_image_data','relationship_ids':[]} for _ in range(safe.count('[IMAGE]')-original.count('[IMAGE]')))
   return
  if name in ['tab','br','cr']:out.append(' ');return
  if name=='commentReference':raise ValueError('Native Word review-comment reference requires explicit source qualification')
  if name in ['footnoteReference','endnoteReference']:
   nid=el.attrib.get('{'+W+'}id');out.append('[NOTE '+str(nid)+']');notes.append({'kind':name,'source_id':nid,'xml_path':path});return
  if name=='noBreakHyphen':out.append('\u2011');return
  if name=='softHyphen':out.append('\u00ad');return
  if name=='sym':
   value=el.attrib.get('{'+W+'}char','');font=el.attrib.get('{'+W+'}font','').lower()
   try:code=int(value,16)
   except ValueError:code=-1
   out.append(chr(code) if font in ['courier new','arial','times new roman','calibri','cambria'] and 32<=code<=126 else '[SYMBOL '+value+']');return
  for i,ch in enumerate(el):walk(ch,path+'/'+local(ch.tag)+'['+str(i)+']')
  if name=='p':out.append(' ')
 walk(node,'/'+local(node.tag));return clean(''.join(out)),images,notes

def inspect(raw):
 if not raw or not raw.startswith(b'PK'):raise ValueError('Native Word must be a nonempty ZIP/DOCX')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  names=z.namelist()
  if len(names)!=len(set(names)):raise ValueError('Duplicate native ZIP member')
  if any(n.startswith('/') or '..' in PurePosixPath(n).parts for n in names):raise ValueError('Unsafe native ZIP member path')
  required=['[Content_Types].xml','word/document.xml']
  if any(n not in names for n in required):raise ValueError('Required native Word structure absent')
  # ZipFile.read verifies CRC for these exact XML members; image members are NEVER read.
  members_read=[]
  def xml(name):
   if not name.endswith(('.xml','.rels')):raise ValueError('Only structural XML may be opened')
   data=z.read(name);members_read.append(name);return ET.fromstring(data)
  xml('[Content_Types].xml');tree=xml('word/document.xml');body=tree.find('w:body',NS)
  if body is None:raise ValueError('Native Word body absent')
  rels=[];objects={};contexts={}
  parents={c:p for p in tree.iter() for c in p}
  for element in tree.iter():
   rid=element.attrib.get('{'+R+'}id')
   if not rid:continue
   if local(element.tag)=='OLEObject':objects[rid]={'program_id':element.attrib.get('ProgID',''),'source_object_sha256':sha(ET.tostring(element))}
   parent=element
   while parent in parents and local(parent.tag)!='p':parent=parents[parent]
   if local(parent.tag)=='p':contexts[rid]=ordered_text(parent)[0]
  if 'word/_rels/document.xml.rels' in names:
   for rel in xml('word/_rels/document.xml.rels'):
    target=rel.attrib.get('Target','');kind=rel.attrib.get('Type','').rsplit('/',1)[-1];rid=rel.attrib.get('Id');object_info=objects.get(rid,{});picture_object=object_info.get('program_id','').lower() in ['pbrush','word.picture.8'];image=picture_object or kind=='image' or bool(re.search(r'\.(png|jpe?g|gif|svg|emf|wmf|tiff?|bmp|webp)$',target,re.I))
    context=contexts.get(rid,'');required_doc=kind=='hyperlink' and (bool(re.search(r'\.(pdf|docx?|rtf|xlsx?|csv|zip)(?:$|[?#])',target,re.I)) or bool(re.search(r'incorporat|adopted? by reference|attachment|appendix',context,re.I)))
    status='policy_omitted_image' if image else 'unresolved_nonimage_dependency' if required_doc else 'retained_structural_xml' if target.endswith(('.xml','.rels')) and rel.attrib.get('TargetMode')!='External' else 'external_hyperlink_reference' if kind=='hyperlink' else 'unresolved_nonimage_dependency'
    required=not image and (required_doc or kind not in ['hyperlink','styles','stylesWithEffects','settings','webSettings','fontTable','theme','numbering','footnotes','endnotes','customXml','glossaryDocument'])
    rels.append(redact_image_metadata({'id':rid,'kind':kind,'target':target,'external':rel.attrib.get('TargetMode')=='External','status':status,'required':required,'source_context':context,'source_object':object_info,'classification':'explicit_native_picture_object' if picture_object else 'source_relationship'}))
  units=[];images=[];notes=[]
  for i,child in enumerate(body):
   kind=local(child.tag)
   if kind in ['sectPr','bookmarkStart','bookmarkEnd','proofErr','permStart','permEnd']:
    units.append({'source_ordinal':i,'kind':'source_marker','source_xml_sha256':sha(ET.tostring(child)),'source_id':child.attrib.get('{'+W+'}name') or child.attrib.get('{'+W+'}id'),'text':'','tables':[],'image_placeholders':[],'note_references':[]});continue
   if kind not in ['p','tbl']:raise ValueError('Unprofiled native Word body kind '+kind)
   text,im,nt=ordered_text(child);images.extend(im);notes.extend(nt);tables=[]
   for table in ([child] if kind=='tbl' else [])+list(child.findall('.//w:tbl',NS)):
    rows=[]
    for row in table.findall('w:tr',NS):
     cells=[]
     for cell in row.findall('w:tc',NS):
      ct,ci,cn=ordered_text(cell);span=cell.find('w:tcPr/w:gridSpan',NS);merge=cell.find('w:tcPr/w:vMerge',NS);cells.append({'text':ct,'colspan':span.attrib.get('{'+W+'}val','1') if span is not None else '1','vertical_merge':merge.attrib.get('{'+W+'}val','continue') if merge is not None else None})
     rows.append(cells)
    tables.append({'rows':rows})
   units.append({'source_ordinal':i,'kind':'table' if kind=='tbl' else 'paragraph','source_xml_sha256':sha(ET.tostring(child)),'source_id':child.attrib.get('{http://schemas.microsoft.com/office/word/2010/wordml}paraId'),'text':text,'tables':tables,'image_placeholders':im,'note_references':nt})
  note_bodies=[];note_tracked_changes=0
  for member,tag in [('word/footnotes.xml','footnote'),('word/endnotes.xml','endnote')]:
   if member not in names:continue
   for node in xml(member).findall('w:'+tag,NS):
    nid=node.attrib.get('{'+W+'}id');typ=node.attrib.get('{'+W+'}type')
    if typ in ['separator','continuationSeparator']:continue
    if node.find('.//w:tbl',NS) is not None:raise ValueError('Native note table requires explicit table qualification: '+member)
    note_tracked_changes+=sum(1 for e in node.iter() if local(e.tag) in ['del','ins'])
    text,im,nt=ordered_text(node);images.extend(im);note_bodies.append({'source_xml_sha256':sha(ET.tostring(node)),'source_part':member,'kind':tag,'source_id':nid,'text':text,'image_placeholders':im,'note_references':nt})
  # Header/footer parts are actual source relationships, not inferred filenames.
  # Preserve cached text/field instructions separately from current body currency.
  owned_ancillary=set()
  for rel in list(rels):
   if rel['kind'] not in ['header','footer']:continue
   target=rel['target']
   if rel['external']:rel.update(status='unresolved_nonimage_dependency',required=True);continue
   member=target.lstrip('/') if target.startswith('/') else str(PurePosixPath('word')/target)
   if '..' in PurePosixPath(member).parts or member not in names:rel.update(status='unresolved_nonimage_dependency',required=True);continue
   if member in owned_ancillary:rel['status']='retained_structural_xml';continue
   owned_ancillary.add(member);node=xml(member)
   if local(node.tag) not in ['hdr','ftr']:raise ValueError('Unprofiled native header/footer root '+member)
   if node.find('.//w:tbl',NS) is not None:raise ValueError('Native ancillary table requires explicit table qualification: '+member)
   note_tracked_changes+=sum(1 for e in node.iter() if local(e.tag) in ['del','ins'])
   text,im,nt=ordered_text(node);images.extend(im);note_bodies.append({'kind':'source_'+rel['kind'],'source_id':member,'source_xml_sha256':sha(ET.tostring(node)),'source_part':member,'source_part_role':'Original native ancillary cached header/footer; not a publication currency/effective-date assertion','text':text,'field_instructions':redact_image_metadata([e.text or '' for e in node.iter() if local(e.tag)=='instrText'],attribute_boundary=True),'image_placeholders':im,'note_references':nt});rel['status']='retained_structural_xml'
   part_rels=str(PurePosixPath(member).parent/'_rels'/(PurePosixPath(member).name+'.rels'))
   if part_rels in names:
    for extra in xml(part_rels):
     kind=extra.attrib.get('Type','').rsplit('/',1)[-1];target=extra.attrib.get('Target','');is_image=kind=='image' or bool(re.search(r'\.(png|jpe?g|gif|svg|emf|wmf|tiff?|bmp|webp)$',target,re.I))
     rels.append(redact_image_metadata({'id':extra.attrib.get('Id'),'source_part':member,'kind':kind,'target':target,'external':extra.attrib.get('TargetMode')=='External','status':'policy_omitted_image' if is_image else 'unresolved_nonimage_dependency','required':not is_image,'source_context':text}))
  for member in ['word/footnotes.xml','word/endnotes.xml']:
   if member not in members_read:continue
   part_rels=str(PurePosixPath(member).parent/'_rels'/(PurePosixPath(member).name+'.rels'))
   if part_rels not in names:continue
   for extra in xml(part_rels):
    kind=extra.attrib.get('Type','').rsplit('/',1)[-1];target=extra.attrib.get('Target','');is_image=kind=='image' or bool(re.search(r'\.(png|jpe?g|gif|svg|emf|wmf|tiff?|bmp|webp)$',target,re.I))
    ordinary_hyperlink=kind=='hyperlink' and not re.search(r'\.(pdf|docx?|rtf|xlsx?|zip)(?:$|[?#])',target,re.I)
    rels.append(redact_image_metadata({'id':extra.attrib.get('Id'),'source_part':member,'kind':kind,'target':target,'external':extra.attrib.get('TargetMode')=='External','status':'policy_omitted_image' if is_image else 'external_hyperlink_reference' if ordinary_hyperlink else 'unresolved_nonimage_dependency','required':not is_image and not ordinary_hyperlink}))
  if len(note_bodies)!=len({(n['kind'],n['source_id']) for n in note_bodies}):raise ValueError('Duplicate native source note/ancillary identity')
  for rel in rels:
   if rel['status']=='retained_structural_xml':
    member=rel['target'].lstrip('/') if rel['target'].startswith('/') else str(PurePosixPath('word')/rel['target'])
    if member not in members_read:rel['status']='unresolved_nonimage_dependency' if rel['required'] else 'retained_native_package_structural_reference'
  note_ids={(n['kind']+'Reference',n['source_id']) for n in note_bodies};missing_notes=[n for n in notes if (n['kind'],n['source_id']) not in note_ids]
  full=' '.join(x['text'] for x in units);updated=[u['text'] for u in units if u['text'].upper().startswith('UPDATED')]
  return {'schema':'word-structural-image-policy-1','native_sha256':sha(raw),'units':units,'notes':note_bodies,'tables':sum(len(x['tables']) for x in units),'image_placeholder_count':len(images),'body_image_placeholders':sum(len(u['image_placeholders']) for u in units),'note_ancillary_image_placeholders':sum(len(u['image_placeholders']) for u in note_bodies),'updated_markers':updated,'relationships':rels,'missing_notes':missing_notes,'tracked_change_elements':note_tracked_changes+sum(1 for e in tree.iter() if local(e.tag) in ['del','ins']),'members_read':members_read,'image_members_never_read':True,'image_member_names_omitted':sum(bool(re.search(r'^word/media/',n)) for n in names),'images_extracted':False,'text':full,'raw_visible_t_text':' '.join(x.text or '' for x in tree.findall('.//w:t',NS))}
