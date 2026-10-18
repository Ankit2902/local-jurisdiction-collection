"""Audit original-source entrypoint qualification against retained publisher bytes."""
import hashlib
import json
from urllib.parse import urljoin, urlsplit
import zipfile

from bs4 import BeautifulSoup


def audit(here, catalog):
    errors = []
    def check(ok, message):
        if not ok:
            errors.append(message)
    selected = {p['id']: p for p in catalog['publications']
                if p.get('adapter_family') == 'originals'}
    required = {'original-flagstaff-az-primary', 'original-king-county-wa-primary'}
    check(set(selected) == required, 'Exact two source-qualified original adapters required')
    try:
        manifest = json.loads((here / 'original-adapter-source-evidence-manifest.json').read_text())
        archive = here / 'original-adapter-source-evidence.zip'
        check(hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['archive_sha256'],
              'Original adapter evidence archive changed')
        with zipfile.ZipFile(archive) as z:
            check(set(z.namelist()) == {x['member'] for x in manifest['files']},
                  'Original adapter evidence archive entry mismatch')
            raw = {x['member']: z.read(x['member']) for x in manifest['files']}
            for item in manifest['files']:
                value = raw[item['member']]
                check(len(value) == item['bytes'] and hashlib.sha256(value).hexdigest() == item['sha256'],
                      'Original adapter raw evidence changed: ' + item['member'])
        frames = json.loads(raw['flagstaff/opening-frames.json'])
        by_name = {f['name']: f for f in frames}
        pub = selected['original-flagstaff-az-primary']
        check(pub['source_url'] == by_name['']['url'], 'Flagstaff original root changed')
        root = BeautifulSoup(raw['flagstaff/' + by_name['']['path']], 'html.parser')
        check(root.title is not None and 'Flagstaff' in root.title.get_text(), 'Flagstaff root identity')
        observed = {f.get('name'): urljoin(pub['source_url'], f['src']) for f in root.select('frame[src]')}
        for name in ('toc', 'doc'):
            frame = by_name[name]
            value = raw['flagstaff/' + frame['path']]
            check(hashlib.sha256(value).hexdigest() == frame['sha256'], 'Flagstaff frame hash: ' + name)
            route = urlsplit(frame['url'])
            # The observed browser adds exactly the current-HTML selector and
            # the main-content anchor to the literal root frame paths.
            check(route._replace(query='', fragment='').geturl() == observed.get(name)
                  and route.query == ('archive=html' if name == 'toc' else '')
                  and route.fragment == ('mainContent' if name == 'doc' else ''),
                  'Flagstaff frame differs from observed current root route: ' + name)
        toc = BeautifulSoup(raw['flagstaff/' + by_name['toc']['path']], 'html.parser')
        check(bool(toc.select('a[href]')) and 'Flagstaff' in toc.get_text(), 'Flagstaff observed TOC')
        pub = selected['original-king-county-wa-primary']
        receipt = json.loads(raw['king/index-receipt.json'])
        check(receipt['source_url'] == pub['source_url'] == receipt['final_url'] and receipt['status'] == 200,
              'King County observed source route/status')
        check(hashlib.sha256(raw['king/index-start.html']).hexdigest() == receipt['sha256'],
              'King County index receipt/raw mismatch')
        index = BeautifulSoup(raw['king/index-start.html'], 'html.parser')
        check(index.title is not None and 'King County Code' in index.title.get_text(), 'King County index identity')
        links = [urljoin(pub['source_url'], a['href']) for a in index.select('a[href]')]
        for extension in ('.htm', '.docx'):
            check(sum(urlsplit(u).path.lower().endswith(extension) for u in links) == 35,
                  'King County exact source-listed format inventory: ' + extension)
        for pub in selected.values():
            check(pub['publisher'] == 'official', 'Original adapter changed official-source access gate')
            proof = pub.get('qualification_evidence', {})
            check(proof.get('kind') == 'original-adapter-source-profile'
                  and proof.get('source_bundle') == archive.name
                  and proof.get('source_manifest') == 'original-adapter-source-evidence-manifest.json',
                  'Original adapter source qualification binding missing')
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as exc:
        errors.append('Original adapter source evidence unavailable: ' + str(exc))
    return errors
