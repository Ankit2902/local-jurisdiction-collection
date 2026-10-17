#!/usr/bin/env python3
"""Restore large evidence files from hash-verified repository release archives.

Uses only Python's standard library. Private release downloads use the existing
Git credential helper. --from-archive permits an entirely offline restoration.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
API = 'https://api.github.com/repos/OliverFlint-98/local-jurisdiction-collection'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def valid(path, item):
    return path.is_file() and path.stat().st_size == item['bytes'] and sha(path) == item['sha256']

def inside(name):
    p = (ROOT / name).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError('Manifest path escapes repository')
    return p

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old = urllib.parse.urlsplit(req.full_url)
        new = urllib.parse.urlsplit(newurl)
        if new.scheme != 'https':
            raise RuntimeError('Refusing a non-HTTPS evidence redirect')
        result = super().redirect_request(req, fp, code, msg, headers, newurl)
        if result and (old.scheme, old.hostname, old.port or 443) != (new.scheme, new.hostname, new.port or 443):
            result.remove_header('Authorization')
        return result

def token():
    # Never print credentials or persist them to the repository.
    result = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                            text=True, capture_output=True, cwd=ROOT, env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    if result.returncode or not fields.get('password'):
        raise RuntimeError('GitHub credentials unavailable. Sign in through your Git credential helper, or use --from-archive with a downloaded release ZIP.')
    return fields['password']

def download(item, dest):
    headers = {'Authorization': 'Bearer ' + token(), 'Accept': 'application/vnd.github+json',
               'User-Agent': 'local-jurisdiction-evidence'}
    opener = urllib.request.build_opener(SafeRedirect())
    url = API + '/releases/tags/' + urllib.parse.quote(item['release_tag'], safe='')
    with opener.open(urllib.request.Request(url, headers=headers), timeout=60) as response:
        release = json.load(response)
    matches = [a for a in release['assets'] if a['name'] == item['asset_name']]
    if len(matches) != 1:
        raise RuntimeError('Expected release archive is missing or ambiguous: ' + item['asset_name'])
    asset = matches[0]
    if asset['size'] != item['bytes']:
        raise RuntimeError('Release asset size differs from delivery manifest')
    expected_digest = 'sha256:' + item['sha256']
    if asset.get('digest') and asset['digest'] != expected_digest:
        raise RuntimeError('Release asset digest differs from delivery manifest')
    headers['Accept'] = 'application/octet-stream'
    with opener.open(urllib.request.Request(API + '/releases/assets/' + str(asset['id']), headers=headers), timeout=120) as response, dest.open('wb') as out:
        shutil.copyfileobj(response, out, 1024 * 1024)

def restore(item, source=None):
    archive = inside(item['path'])
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not valid(archive, item):
        if archive.exists():
            raise RuntimeError('Existing archive has unexpected bytes; move it aside before retrying: ' + str(archive))
        temp = archive.with_name(archive.name + '.partial')
        try:
            if source:
                if not valid(source, item):
                    raise RuntimeError('Supplied archive failed its size/SHA-256 check')
                shutil.copyfile(source, temp)
            else:
                print('Downloading ' + item['asset_name'], flush=True)
                download(item, temp)
            if not valid(temp, item):
                raise RuntimeError('Downloaded archive failed its size/SHA-256 check')
            temp.replace(archive)
        finally:
            if temp.exists():
                temp.unlink()
    restored = 0
    with zipfile.ZipFile(archive) as z:
        for entry in item['restore_files']:
            dest = inside(entry['path'])
            if valid(dest, entry):
                continue
            if dest.exists():
                raise RuntimeError('Refusing to overwrite changed evidence: ' + entry['path'])
            member = entry['archive_member']
            if z.getinfo(member).file_size != entry['bytes']:
                raise RuntimeError('Archive member size mismatch: ' + member)
            dest.parent.mkdir(parents=True, exist_ok=True)
            temp = dest.with_name(dest.name + '.partial')
            try:
                with z.open(member) as inp, temp.open('wb') as out:
                    shutil.copyfileobj(inp, out, 1024 * 1024)
                if not valid(temp, entry):
                    raise RuntimeError('Archive member hash mismatch: ' + member)
                temp.replace(dest)
            finally:
                if temp.exists():
                    temp.unlink()
            restored += 1
    return {'package': item['package'], 'restored_files': restored, 'archive_sha256_verified': True}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', help='Restrict to one named package')
    parser.add_argument('--from-archive', type=Path, help='Use a local ZIP without network; requires --package')
    args = parser.parse_args()
    if args.from_archive and not args.package:
        parser.error('--from-archive requires --package')
    items = json.loads((ROOT / 'RELEASE-ASSETS.json').read_text())['archives']
    selected = [x for x in items if not args.package or x['package'] == args.package]
    if not selected:
        parser.error('Unknown package')
    print(json.dumps([restore(x, args.from_archive) for x in selected], indent=2))

if __name__ == '__main__':
    main()
