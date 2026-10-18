"""Reconstruct follow-up configuration scope from portable original witnesses."""
import hashlib,json,zipfile
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def audit(here,catalog):
    errors=[]
    def check(ok,why):
        if not ok:errors.append(why)
    manifests=here/'followup-source-evidence-manifest.json'
    if not manifests.exists():return ['Follow-up source evidence manifest missing']
    manifest=json.loads(manifests.read_text());archive=here/'followup-source-evidence.zip';sha=lambda b:hashlib.sha256(b).hexdigest()
    check(sha(archive.read_bytes())==manifest['archive_sha256'],'Follow-up source archive hash mismatch')
    publications={p['id']:p for p in catalog['publications']}
    with zipfile.ZipFile(archive) as z:
        check(set(z.namelist())=={r['member'] for r in manifest['files']},'Follow-up source archive exact entries')
        for row in manifest['files']:check(sha(z.read(row['member']))==row['sha256'] and len(z.read(row['member']))==row['bytes'],'Follow-up source witness corrupted '+row['member'])
        document=z.read('native/current-documents.html');receipt=json.loads(z.read('native/current-documents.receipt.json'))
        check(receipt['http_status']==200 and receipt['sha256']==sha(document),'Current native publication list raw receipt mismatch')
        anchors={urljoin(receipt['url'],a['href']):' '.join(a.stripped_strings) for a in BeautifulSoup(document,'html.parser').select('a[href]')}
        native_ids={name.split('/')[1] for name in z.namelist() if name.startswith('native/82-')}
        overrides=json.loads((here/'followup-qualified-configs.json').read_text())['publications']
        check(native_ids==set(overrides),'Exact six source-qualified native configuration entries')
        for ident in native_ids:
            p=publications.get(ident,{});cfgbytes=z.read('native/'+ident+'/config.json');cfg=json.loads(cfgbytes);original=json.loads(z.read('native/'+ident+'/native-receipt.json'));actual=here.parents[1]/p.get('adapter_config_path','missing')
            check(actual.is_file() and actual.read_bytes()==cfgbytes,'Current native config differs from qualified witness '+ident)
            check(p.get('source_url')==cfg['url'] and cfg['url'] in anchors and p.get('adapter_mode')=='native_document' and p.get('runnable'),'Native exact source/config dispatch binding '+ident)
            check(original['http_status']==200 and original['url']==cfg['url'] and original['sha256']==cfg['expected_sha256'],'Native original file hash/source pin '+ident)
            check(not p.get('full_live_verified'),'Native configuration promoted to full legal proof '+ident)
        cfgbytes=z.read('miami-comprehensive/config.json');cfg=json.loads(cfgbytes);identity=json.loads(z.read('miami-comprehensive/identity.json'));receipts=json.loads(z.read('miami-comprehensive/responses.json'));inventory=identity['inventory'];raw=z.read('miami-comprehensive/'+inventory['path']);book=publications.get('29-gridics-comprehensive-plan-94',{})
        check(inventory in receipts and inventory['status']==200 and sha(raw)==inventory['sha256'] and inventory['url'].startswith('https://codehub.gridics.com/api/v1/codehub/94?') and len(json.loads(raw))==49 and all(n['docId']=='94' for n in json.loads(raw)),'Miami separate full native inventory source binding')
        check(identity['title'] in z.read('miami-comprehensive/rendered.html').decode() and book.get('title')==identity['title'] and book.get('source_url')==cfg['source_url'] and book.get('target_id')=='29','Miami separate source publication/config identity')
        actual=here.parents[1]/book.get('adapter_config_path','missing');check(actual.is_file() and actual.read_bytes()==cfgbytes,'Miami current configuration differs from qualified source witness')
        check(book.get('role')=='secondary' and book.get('required_for_jurisdiction') and not book.get('full_live_verified'),'Miami scope or false full verification')
    return errors
