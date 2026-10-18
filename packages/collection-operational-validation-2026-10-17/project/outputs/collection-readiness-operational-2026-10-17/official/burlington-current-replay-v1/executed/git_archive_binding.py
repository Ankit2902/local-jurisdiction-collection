"""Independent Git object reconstruction from an original ZIP; no extraction/network.

Git's independently retained commit tree hash commits to every name, mode and
blob recursively, including files unlinked by a publication's navigation.
"""
import hashlib,stat,zipfile
from pathlib import PurePosixPath

def object_id(kind, data):
 return hashlib.sha1(kind.encode()+b' '+str(len(data)).encode()+b'\0'+data).digest()

def root_tree(files):
 tree={}
 for path,mode,oid in files:
  parts=path.split('/');node=tree
  for part in parts[:-1]:
   if part in node and not isinstance(node[part],dict):raise ValueError('File/directory collision')
   node=node.setdefault(part,{})
  if parts[-1] in node:raise ValueError('Duplicate Git path')
  node[parts[-1]]=(mode,oid)
 def visit(node):
  entries=[]
  for name,value in node.items():
   mode,oid=('40000',visit(value)) if isinstance(value,dict) else value
   encoded=name.encode('utf-8');entries.append((encoded+(b'/' if mode=='40000' else b''),mode.encode()+b' '+encoded+b'\0'+oid))
  return object_id('tree',b''.join(data for key,data in sorted(entries)))
 return visit(tree).hex()

def inspect_archive(source):
 files=[];members=[];prefix=None;seen=set();directories=0
 with zipfile.ZipFile(source) as archive:
  for info in archive.infolist():
   path=PurePosixPath(info.filename)
   if path.is_absolute() or '..' in path.parts or '\\' in info.filename or info.filename in seen or info.flag_bits&1:raise ValueError('Unsafe/duplicate/encrypted source ZIP entry')
   seen.add(info.filename);first=info.filename.split('/')[0]+'/'
   if prefix is None:prefix=first
   if first!=prefix:raise ValueError('Multiple archive roots')
   if info.is_dir():directories+=1;continue
   relative=info.filename[len(prefix):]
   if not relative:raise ValueError('Root regular file lacks archive prefix')
   mode=info.external_attr>>16
   if stat.S_ISLNK(mode):git_mode='120000'
   elif mode and not stat.S_ISREG(mode):raise ValueError('Unsupported Git source file mode')
   else:git_mode='100755' if mode&0o111 else '100644'
   git_hash=hashlib.sha1(b'blob '+str(info.file_size).encode()+b'\0');digest=hashlib.sha256();size=0
   # Streaming reads validate ZIP CRC. Opaque bytes are hashed, never decoded,
   # rendered or saved as individual image/media/member files.
   with archive.open(info) as stream:
    while chunk:=stream.read(262144):git_hash.update(chunk);digest.update(chunk);size+=len(chunk)
   if size!=info.file_size:raise ValueError('Source ZIP length mismatch')
   oid=git_hash.digest();files.append((relative,git_mode,oid));members.append({'path':info.filename,'relative_path':relative,'git_mode':git_mode,'git_blob_sha1':oid.hex(),'sha256':digest.hexdigest(),'bytes':size,'crc32':info.CRC})
 return {'root':prefix,'file_count':len(files),'directory_entries':directories,'git_root_tree_sha1':root_tree(files),'members':members,'zip_crc_all_members_valid':True,'image_decoding_or_member_file_extraction':False}
