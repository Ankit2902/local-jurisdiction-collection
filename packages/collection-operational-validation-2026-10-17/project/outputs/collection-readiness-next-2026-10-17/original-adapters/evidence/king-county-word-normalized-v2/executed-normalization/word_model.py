"""Native Word structural importer. Never reads/extracts image ZIP members or external images."""
import io,re,zipfile,xml.etree.ElementTree as ET
from pathlib import PurePosixPath
from source_common import sha,clean
from model import redact_image_metadata
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
   out.append('[IMAGE]');images.append({'xml_path':path,'source_sha256':sha(ET.tostring(el)),'placeholder':'[IMAGE]','relationship_ids':sorted(set(v for x in el.iter() for k,v in x.attrib.items() if k in ['{'+R+'}embed','{'+R+'}link','{'+R+'}id']))});return
  if name in ['t','delText']:out.append(el.text or '');return
  if name in ['tab','br','cr']:out.append(' ');return
  if name in ['footnoteReference','endnoteReference']:
   nid=el.attrib.get('{'+W+'}id');out.append('[NOTE '+str(nid)+']');notes.append({'kind':name,'source_id':nid,'xml_path':path});return
  if name=='sym':out.append('[SYMBOL '+el.attrib.get('{'+W+'}char','UNKNOWN')+']');return
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
  rels=[]
  if 'word/_rels/document.xml.rels' in names:
   for rel in xml('word/_rels/document.xml.rels'):
    target=rel.attrib.get('Target','');kind=rel.attrib.get('Type','').rsplit('/',1)[-1];image=kind=='image' or bool(re.search(r'\.(png|jpe?g|gif|svg|emf|wmf|tiff?|bmp|webp)$',target,re.I))
    rels.append(redact_image_metadata({'id':rel.attrib.get('Id'),'kind':kind,'target':target,'external':rel.attrib.get('TargetMode')=='External','status':'policy_omitted_image' if image else 'retained_structural_xml' if target.endswith(('.xml','.rels')) and rel.attrib.get('TargetMode')!='External' else 'external_hyperlink_reference' if kind=='hyperlink' else 'unresolved_nonimage_dependency','required':not image and kind not in ['hyperlink','styles','stylesWithEffects','settings','webSettings','fontTable','theme','numbering','footnotes','endnotes','customXml','glossaryDocument']}))
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
  note_bodies=[]
  for member,tag in [('word/footnotes.xml','footnote'),('word/endnotes.xml','endnote')]:
   if member not in names:continue
   for node in xml(member).findall('w:'+tag,NS):
    nid=node.attrib.get('{'+W+'}id');typ=node.attrib.get('{'+W+'}type')
    if typ in ['separator','continuationSeparator']:continue
    text,im,nt=ordered_text(node);images.extend(im);note_bodies.append({'kind':tag,'source_id':nid,'text':text,'image_placeholders':im,'note_references':nt})
  note_ids={(n['kind']+'Reference',n['source_id']) for n in note_bodies};missing_notes=[n for n in notes if (n['kind'],n['source_id']) not in note_ids]
  full=' '.join(x['text'] for x in units);updated=[u['text'] for u in units if u['text'].upper().startswith('UPDATED')]
  return {'schema':'word-structural-image-policy-1','native_sha256':sha(raw),'units':units,'notes':note_bodies,'tables':sum(len(x['tables']) for x in units),'image_placeholder_count':len(images),'updated_markers':updated,'relationships':rels,'missing_notes':missing_notes,'tracked_change_elements':sum(1 for e in tree.iter() if local(e.tag) in ['del','ins']),'members_read':members_read,'image_members_never_read':True,'image_member_names_omitted':sum(bool(re.search(r'^word/media/',n)) for n in names),'images_extracted':False,'text':full,'raw_visible_t_text':' '.join(x.text or '' for x in tree.findall('.//w:t',NS))}
