"""Source-bound, metadata-only public PDF availability probe; no response bodies."""
import datetime
import fcntl
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlsplit
import requests

BASE = Path(__file__).resolve().parents[3]
SOURCE = BASE / 'outputs/collection-readiness-2026-10-17/gridics/cupertino-portable-v4-replay/references.jsonl'
OUT = Path(__file__).with_name('cupertino-pdf-heads-v1')
GATE = Path.home() / '.local/state/local-jurisdiction-collection/gridics'

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def save(path, obj):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2) + '\n')
    tmp.replace(path)

def main():
    raw = SOURCE.read_bytes()
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    selected = [r for r in rows if urlsplit(r['url']).hostname == 'codehub.gridics.com' and urlsplit(r['url']).path.lower().endswith('.pdf')]
    assert len(selected) == 16
    OUT.mkdir(exist_ok=False)
    (OUT / 'executed-probe.py').write_bytes(Path(__file__).read_bytes())
    save(OUT / 'source.json', {'source': str(SOURCE), 'sha256': hashlib.sha256(raw).hexdigest(), 'selected_references': selected, 'image_downloads': 0, 'response_bodies_requested': False})
    GATE.mkdir(parents=True, exist_ok=True)
    results = []
    for ref in selected:
        with (GATE / 'lock').open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if (GATE / 'STOP.json').exists():
                save(OUT / 'results.json', {'status': 'existing_publisher_stop', 'results': results})
                return 2
            state = json.loads((GATE / 'state.json').read_text()) if (GATE / 'state.json').exists() else {}
            time.sleep(max(0, state.get('last', 0) + 4.0 - time.time()))
            event = {'reference': ref, 'method': 'HEAD', 'started_at': stamp(), 'redirects_followed': False, 'body_bytes_saved': 0}
            save(GATE / 'state.json', {'last': time.time(), 'url': ref['url']})
            try:
                with requests.head(ref['url'], allow_redirects=False, timeout=90, stream=True) as response:
                    event.update(status=response.status_code, headers=dict(response.headers))
                    if response.status_code in {401, 403, 429}:
                        save(GATE / 'STOP.json', {'url': ref['url'], 'status': response.status_code, 'at': stamp(), 'method': 'HEAD'})
            except requests.RequestException as error:
                event['error'] = str(error)
            finally:
                event['finished_at'] = stamp()
                save(GATE / 'state.json', {'last': time.time(), 'url': ref['url']})
                results.append(event)
                save(OUT / 'results.json', {'status': 'probing', 'results': results})
            if (GATE / 'STOP.json').exists():
                save(OUT / 'results.json', {'status': 'publisher_stop_observed', 'results': results})
                return 2
    save(OUT / 'results.json', {'status': 'terminal', 'results': results, 'pdf_head_200': sum(r.get('status') == 200 and 'application/pdf' in r.get('headers', {}).get('Content-Type', '').lower() for r in results), 'publication_complete': False})
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
