"""Complete source-bound Open Law XML include closure; no transport/pixels."""
import collections,copy,hashlib,html,io,pathlib,posixpath,re,xml.etree.ElementTree as ET,zipfile
from bs4 import BeautifulSoup
XI='{http://www.w3.org/2001/XInclude}include'
STRUCT={'library','document','collection','container','section'};META={'meta','heading','prefix','num'}
def local(n):return n.tag.rsplit('}',1)[-1]
def childtext(n,name):return ' '.join(''.join(next((x for x in n if local(x)==name),ET.Element('empty')).itertext()).split())
def ref(document,href):
 if not href or ':' in href or href.startswith('/') or '#' in href or '?' in href:raise ValueError('Only observed repository-relative XML includes supported')
 value=posixpath.normpath(posixpath.join(posixpath.dirname(document),href))
 if value=='..' or value.startswith('../'):raise ValueError('XInclude escapes repository')
 return value

def markup(n):
 name=local(n)
 if n.tag==XI:raise ValueError('Nested body XInclude needs explicit inline ownership qualification')
 if name in ['image','img','svg']:return '<img '+('id="'+html.escape(n.get('id',''),quote=True)+'" ' if n.get('id') else '')+'src="'+html.escape(n.get('src',n.get('href','')),quote=True)+'"/>'
 tag={'text':'p','para':'div','num':'span','heading':'strong','annotations':'div','annotation':'p','cite':'a','note':'aside','footnote':'aside','italic':'em','bold':'strong'}.get(name,name if name in {'table','thead','tbody','tfoot','tr','td','th','sup','sub','ol','ul','li','p','span','br'} else 'div')
 attrs=''.join(' '+k+'="'+html.escape(v,quote=True)+'"' for k,v in n.attrib.items() if k in {'rowspan','colspan','start','value','type','href','id'})
 content=html.escape(n.text or '')
 for c in n:content+=markup(c)+(' ' if local(c)=='num' else '')+html.escape(c.tail or '')
 if name=='annotation' and not content.strip():content=html.escape(' '.join(n.get(k,'') for k in ['type','doc','path']))
 return '<'+tag+attrs+'>'+content+'</'+tag+'>'

def parse(data,config,item):
 from model import sha,semantics,clean,redact_image_metadata
 z=zipfile.ZipFile(io.BytesIO(data));seen=set();members=[];blobs={};total=0
 for info in z.infolist():
  path=pathlib.PurePosixPath(info.filename)
  if info.filename in seen or path.is_absolute() or '..'in path.parts or '\\'in info.filename or info.flag_bits&1 or (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Unsafe/duplicate/encrypted XML ZIP member')
  seen.add(info.filename);total+=info.file_size
  if total>config.get('max_uncompressed_bytes',600_000_000):raise ValueError('XML archive expansion limit')
  if info.is_dir():continue
  b=z.read(info);parts=info.filename.split('/',1)
  if len(parts)!=2:raise ValueError('XML archive top-level membership invalid')
  p=parts[1];blobs[p]=b;members.append({'path':info.filename,'repository_path':p,'bytes':len(b),'sha256':sha(b),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),'crc':info.CRC})
 expected={v['path']:v['sha']for v in item['git_tree']['tree']if v['type']=='blob'}
 if item['git_tree'].get('truncated') or set(expected)!=set(blobs) or any(expected[m['repository_path']]!=m['git_blob_sha1']for m in members):raise ValueError('Complete pinned Git tree/ZIP blob membership or hash mismatch')
 def read(path):
  if path not in blobs:raise ValueError('Missing XInclude member '+path)
  b=blobs[path]
  if b'<!DOCTYPE'in b.upper() or b'<!ENTITY'in b.upper():raise ValueError('DTD/entity XML unsupported')
  return ET.fromstring(b)
 library=read(config['archive_start']);source_roots={ref(config['archive_start'],x.get('href',''))for x in library.iter(XI)};roots=config['xml_publication_roots']
 if not roots or any(p not in source_roots for p in roots):raise ValueError('Selected XML publication root absent from actual library include inventory')
 records=[];owners=[];edges=[];visited=set();assets=[];prefixes=[posixpath.dirname(p)+'/' for p in roots];member_lookup={m['repository_path']:m for m in members}
 def visit_file(path,trail,stack):
  if path in stack:raise ValueError('XInclude cycle: '+' -> '.join(stack+[path]))
  if path in visited:return
  visited.add(path);root=read(path);source='https://raw.githubusercontent.com/'+config['repository']+'/'+item['source_commit']+'/'+path;raw_ref=item['raw_ref']+'!'+member_lookup[path]['path'];digest=sha(blobs[path]);document_id=path
  def visit(n,indices,ancestry):
   label=' '.join(v for v in [childtext(n,'prefix'),childtext(n,'num'),childtext(n,'heading')]if v);node_id=path+'::xml-child-indices:'+('/'.join(map(str,indices))or'root');body=[];fragment=0;has_own=False
   def flush():
    nonlocal fragment,has_own,body
    fragment+=1;semantic=semantics(BeautifulSoup(''.join(body),'html.parser'),source);body=[]
    if not semantic['text']:return
    has_own=True;ident=node_id+'::owned:'+str(fragment);record=dict(semantic,id=ident,heading=label or path,path=ancestry,source_url=source,unit='legal_section'if local(n)=='section' else 'container_owned_body',document_id=document_id,raw_ref=raw_ref,raw_sha256=digest,jurisdiction=config['jurisdiction'],state=config['state'],publication=config['publication'],source_commit=item['source_commit'],source_locator={'xml_child_indices':indices,'owned_fragment':fragment},source_attributes=dict(n.attrib));records.append(record);owners.append({'id':ident,'member':member_lookup[path]['path'],'disposition':'included','record_id':ident,'member_sha256':digest});assets.extend(dict(a,owner=ident)for a in record['assets'])
   if (n.text or '').strip():body.append(html.escape(n.text))
   for index,c in enumerate(n):
    name=local(c)
    if c.tag==XI:
     flush();target=ref(path,c.get('href',''));edge={'from':path,'source_locator':indices+[index],'href':c.get('href'),'target':target,'exists_in_archive':target in blobs,'disposition':'included'};edges.append(edge)
     if not any(target.startswith(prefix) for prefix in prefixes):raise ValueError('Selected publication includes outside qualified family '+target)
     visit_file(target,ancestry+[label]if label else ancestry,stack+[path])
    elif name in STRUCT:flush();visit(c,indices+[index],ancestry+[label]if label else ancestry)
    elif name not in META:body.append(markup(c))
    if (c.tail or '').strip():body.append(html.escape(c.tail))
   flush()
   if not has_own:owners.append({'id':node_id,'member':member_lookup[path]['path'],'disposition':'excluded','reason':'Metadata/structural XML node without owned substantive body','source_heading':label})
  visit(root,[],trail)
 for root in roots:visit_file(root,[config['publication']],[])
 selected={p for p in blobs if p.endswith('.xml')and any(p.startswith(prefix)for prefix in prefixes)};unvisited=sorted(selected-visited)
 ledger={'members':members,'owners':owners,'assets':assets,'canonical_member_count':len(selected),'alternate_aggregate_members_excluded':0,'missing_internal_nav_targets':unvisited,'archive_crc_verified':True,'git_tree_verified':True,'source_commit':item['source_commit'],'xml_include_edges':edges,'visited_xml_members':sorted(visited),'unvisited_selected_xml_members':unvisited,'library_family_inventory':[{'target':p,'selected':p in roots}for p in sorted(source_roots)],'ownership':'Every metadata/own-body/structural/include position is processed in source order. Parent content before/after includes remains distinct owned fragments; child bodies are not copied into parents.'}
 return redact_image_metadata(records),redact_image_metadata(ledger)
