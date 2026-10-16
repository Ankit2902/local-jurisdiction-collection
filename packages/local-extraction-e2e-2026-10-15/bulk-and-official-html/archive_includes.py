"""Verify an official ZIP against a pinned Git tree; resolve only a declared XML subset."""
from __future__ import annotations
import hashlib,posixpath,zipfile,xml.etree.ElementTree as ET
from pathlib import Path,PurePosixPath
from common import sha
XI='{http://www.w3.org/2001/XInclude}include'
def assert_metadata_only_index(root):
    ignored={'heading','meta','prefix','num'}
    structural={'library','document','collection','container'}
    def visit(node):
        tag=node.tag.rsplit('}',1)[-1]
        if node.tag==XI or tag in ignored:return
        if tag not in structural or (node.text or '').strip():raise ValueError('Mixed own-body/include document needs explicit own-content profile')
        for child in node:
            visit(child)
            if (child.tail or '').strip():raise ValueError('Mixed own-body/include tail needs explicit own-content profile')
    visit(root)
    return True

def safe_reference(document,href):
    if not href or ':' in href or href.startswith('/') or '#' in href or '?' in href:
        raise ValueError('Only ordinary repository-relative XML includes are supported')
    target=posixpath.normpath(posixpath.join(posixpath.dirname(document),href))
    if target=='..' or target.startswith('../'):raise ValueError('Include escapes repository')
    return target

class ArchiveIncludes:
    def __init__(self,archive,tree,commit):
        self.archive=zipfile.ZipFile(archive);self.prefix='law-xml-'+commit+'/'
        expected={x['path']:x['sha'] for x in tree['tree'] if x['type']=='blob'}
        actual={n[len(self.prefix):]:n for n in self.archive.namelist() if n.startswith(self.prefix) and not n.endswith('/')}
        if set(expected)!=set(actual):raise ValueError('ZIP/Git tree file membership differs')
        self.members=actual
        for name,member in actual.items():
            data=self.archive.read(member)
            git_sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            if git_sha!=expected[name]:raise ValueError('Git blob mismatch for '+name)
        self.verified_members=len(actual)
    def read(self,path):
        if path not in self.members:raise ValueError('Missing repository member '+path)
        data=self.archive.read(self.members[path])
        if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():raise ValueError('DTD/entity XML not accepted')
        return data
    def resolve(self,start,selected_files):
        """Traverse observed include links; unselected branches get explicit scope dispositions.

        Parse units keep original file identity and XML locators. No invented merged file
        becomes a source. Cycles and missing includes in selected branches are fatal.
        """
        allowed=set(selected_files);edges=[];units=[];visited=set()
        def visit(path,trail):
            if path in trail:raise ValueError('XInclude cycle: '+' -> '.join(trail+[path]))
            if path in visited:return
            visited.add(path);data=self.read(path);root=ET.fromstring(data);includes=list(root.iter(XI))
            if not includes:units.append({'path':path,'sha256':sha(data),'root_tag':root.tag});return
            assert_metadata_only_index(root)
            for node in includes:
                target=safe_reference(path,node.get('href',''));exists=target in self.members
                edge={'from':path,'href':node.get('href'),'target':target,'exists_in_archive':exists,'disposition':'included_sample' if target in allowed else 'excluded_validation_scope'};edges.append(edge)
                if target in allowed:
                    if not exists:raise ValueError('Selected include missing '+target)
                    visit(target,trail+[path])
        visit(start,[])
        unused=allowed-visited
        if unused:raise ValueError('Declared selection is not reachable from observed includes: '+repr(sorted(unused)))
        return {'units':units,'include_edges':edges,'visited_files':sorted(visited)}
    def retain(self,paths,destination):
        destination=Path(destination);written=[]
        for name in sorted(paths):
            # read() uses exact archive membership; never ZipFile.extract.
            target=destination/Path(*PurePosixPath(name).parts);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(self.read(name));written.append(target)
        return written
