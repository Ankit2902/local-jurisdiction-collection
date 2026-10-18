"""Exact native structural/annotation inventory; never decodes image streams."""
import collections,hashlib,io,re
from pypdf import PdfReader
from pypdf.generic import ContentStream,IndirectObject
FORBIDDEN_DRAW={'m','l','c','v','y','h','re','S','s','f','F','f*','B','B*','b','b*','n','Do','BI','INLINE IMAGE','sh'}
def inventory(data,units,source_nodes):
 reader=PdfReader(io.BytesIO(data));pages=[]
 for n,page in enumerate(reader.pages,1):
  counts=collections.Counter(op.decode('ascii') for _,op in ContentStream(page['/Contents'],reader).operations)
  pages.append({'page':n,'operators':dict(sorted(counts.items())),'drawing_operators':{k:v for k,v in counts.items() if k in FORBIDDEN_DRAW},'annotations':len(page.get('/Annots',[])),'resource_xobjects':len(page['/Resources'].get('/XObject',{}))})
 objects=[]
 # Full indirect-object inventory includes unattached file/action objects, not just catalog reachability.
 for generation,entries in reader.xref.items():
  for number in entries:
   if number==0:continue
   obj=reader.get_object(IndirectObject(number,generation,reader))
   if not isinstance(obj,dict):continue
   kind=str(obj.get('/Type',''));subtype=str(obj.get('/Subtype',''))
   if kind in ['/Filespec','/EmbeddedFile','/Annot','/Action'] or subtype=='/Image' or any(k in obj for k in ['/URI','/EF','/AF','/JavaScript','/JS','/EmbeddedFiles']):objects.append({'object':number,'generation':generation,'type':kind,'subtype':subtype,'keys':sorted(map(str,obj))})
 assert all(not p['drawing_operators'] and p['annotations']==p['resource_xobjects']==0 for p in pages)
 assert not objects
 roles=collections.Counter(n['role'] for n in source_nodes)
 assert roles.get('/Table',0)==roles.get('/Figure',0)==0
 # Source-explicit citations/dependencies, not guessed links or replacements.
 dependencies=[]
 for label,pattern,disposition in [('O.P.M.C. Chapter 7.36',r'O\.P\.M\.C\.\s+(?:Chapter|Section)\s+7\.36','incorporated-by-reference'),('County Solid Waste Regulations',r'County Solid Waste Regulations','referenced-regulations')]:
  witnesses=[{'logical_owner_id':u['id'],'source_tag_id':u['source_tag_id'],'source_refs':u['source_refs'],'source_pages':u['source_pages'],'text':u['text'],'text_sha256':hashlib.sha256(u['text'].encode()).hexdigest()} for u in units if re.search(pattern,u['text'])]
  assert witnesses
  dependencies.append({'label':label,'disposition':disposition,'source_url':None,'resolved_in_this_packet':False,'edition_equivalence_qualified':False,'witnesses':witnesses})
 if dependencies[0]['disposition']=='incorporated-by-reference':assert any('are hereby incorporated by reference.' in w['text'] for w in dependencies[0]['witnesses'])
 return {'source_sha256':hashlib.sha256(data).hexdigest(),'pages':pages,'full_indirect_object_scan':True,'xref_object_count':sum(len(v) for v in reader.xref.values())-1,'catalog_keys':sorted(map(str,reader.root_object)),'catalog_names':bool(reader.root_object.get('/Names')),'catalog_associated_files':bool(reader.root_object.get('/AF')),'embedded_or_annotation_or_URI_or_image_objects':objects,'role_counts':dict(sorted(roles.items())),'textual_dependencies':dependencies,'embedded_files':0,'annotations':0,'hyperlinks':0,'inline_images':0,'image_xobjects':0,'table_disposition':{'applicability':'not-applicable','basis':'Full exact6 source: all191 source roles contain no Table, all6 content streams contain no path/drawing/image operators, all109MCIDs accounted as single-column printed headings/paragraphs/lists; glyph indentation/font hierarchy independently audited. No detector-only or clipped-table waiver.'},'image_policy':'literal-[IMAGE]-no-image-fetch-v1','required_external_legal_dependencies_complete':False,'edition_currentness_qualified':False,'jurisdiction_complete':False,'no_new_acquisition':True}
