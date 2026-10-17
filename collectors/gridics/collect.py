"""Full native Gridics publication acquisition in ordinary headed Chrome."""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import time
from urllib.parse import urlsplit, parse_qs
from .model import Invalid, analyze, checked, digest, read, save

HERE = Path(__file__).resolve().parent
GATE = Path.home()/'.local/state/local-jurisdiction-collection/gridics'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sources():
    return {p.name:digest(p.read_bytes()) for p in sorted(HERE.glob('*.py'))}


def write_outputs(output, config, analyzed=None):
    records, refs, coverage = analyzed if analyzed is not None else analyze(output, config)
    for name, rows in [('records.jsonl',records),('references.jsonl',refs)]:
        (output/name).write_text(''.join(json_line(r)+'\n' for r in rows))
    save(output/'coverage.json',coverage)
    return coverage


def json_line(value):
    # Unicode line separators are legal within JSON strings, but many JSONL
    # readers split on them. Escape them while preserving the decoded value.
    line=json.dumps(value,ensure_ascii=False)
    for char in ('\x85','\u2028','\u2029'):
        line=line.replace(char,'\\u'+format(ord(char),'04x'))
    return line


def verify(output, config):
    manifest = read(output/'acquisition.json')
    if manifest['config'] != config:
        raise Invalid('Output publication identity/configuration mismatch')
    validate_executed_sources(output,manifest)
    records, refs, coverage = analyze(output,config)
    for name,rows in [('records.jsonl',records),('references.jsonl',refs)]:
        actual = [json.loads(line) for line in (output/name).read_text().split('\n') if line]
        if actual != rows:
            raise Invalid('Normalized output differs from source replay: '+name)
    if read(output/'coverage.json') != coverage:
        raise Invalid('Coverage differs from source replay')
    return coverage


def validate_executed_sources(output,manifest):
    for name,sha in manifest['collector_sources'].items():
        if Path(name).name!=name or digest((output/'executed-source'/name).read_bytes())!=sha:
            raise Invalid('Executed acquisition source differs from retained binding')
    for name,sha in manifest.get('normalization_sources',{}).items():
        if Path(name).name!=name or digest((output/'normalization-source'/name).read_bytes())!=sha:
            raise Invalid('Executed normalization source differs from retained binding')


def replay(source,output,config):
    source_snapshot={p.name:p.read_bytes() for p in HERE.glob('*.py')}
    source=source.resolve()
    if output.exists() or output.is_relative_to(source):
        raise Invalid('Replay needs a fresh output outside source evidence')
    manifest=read(source/'acquisition.json')
    if manifest['config']!=config:
        raise Invalid('Replay source configuration mismatch')
    validate_executed_sources(source,manifest)
    # Analyze all source receipts before copying. Semantic gaps may remain, but
    # broken source bindings are never repaired by re-labeling a copy.
    analyzed=analyze(source,config)
    if any((HERE/name).read_bytes()!=raw for name,raw in source_snapshot.items()):
        raise Invalid('Normalizer source changed during replay; retain old evidence and rerun stable code')
    shutil.copytree(source,output)
    lineage={'source':str(source),'network_requests':0,'old_acquisition_manifest':manifest,'source_files':{str(p.relative_to(source)):digest(p.read_bytes()) for p in source.rglob('*') if p.is_file()}}
    save(output/'replay-lineage.json',lineage)
    norm=output/'normalization-source'
    norm.mkdir(exist_ok=True)
    for name,raw in source_snapshot.items():
        (norm/name).write_bytes(raw)
    manifest.update(normalization_sources={name:digest(raw) for name,raw in source_snapshot.items()},normalization_at=now(),normalization_kind='offline_retained_source_derivative')
    save(output/'acquisition.json',manifest)
    return write_outputs(output,config,analyzed)


def acquire(output, config, resume):
    from playwright.sync_api import sync_playwright
    output.mkdir(parents=True,exist_ok=True)
    manifest_path = output/'acquisition.json'
    binding = {'config':config,'collector_sources':sources()}
    if manifest_path.exists():
        manifest = read(manifest_path)
        if not resume or any(manifest.get(k)!=v for k,v in binding.items()):
            raise Invalid('Existing output needs --resume and identical code/configuration')
    elif any(output.iterdir()):
        raise Invalid('Refusing nonempty unowned output')
    else:
        manifest = dict(binding,schema_version=1,started_at=now(),status='acquiring',separate_image_downloads=0)
        save(manifest_path,manifest)
        (output/'executed-source').mkdir()
        for p in HERE.glob('*.py'):
            (output/'executed-source'/p.name).write_bytes(p.read_bytes())
    GATE.mkdir(parents=True,exist_ok=True)
    stop = GATE/'STOP.json'
    if stop.exists():
        raise Invalid('Persistent publisher access stop: '+stop.read_text())
    base = config['source_url'].split('#')[0]
    if urlsplit(base).hostname != 'codehub.gridics.com':
        raise Invalid('Unsupported publisher source')
    events = read(output/'events.json') if (output/'events.json').exists() else []
    responses = read(output/'responses.json') if (output/'responses.json').exists() else []
    epoch = str(time.time_ns())
    phase = None
    failures = []
    def persist():
        save(output/'responses.json',responses)
        save(output/'events.json',events)
    def route(r):
        request=r.request
        host=urlsplit(request.url).hostname
        if request.resource_type in {'image','font','media'} or host not in {'codehub.gridics.com','cdn.jsdelivr.net','ajax.googleapis.com'}:
            events.append({'url':request.url,'action':'aborted','kind':request.resource_type,'phase':phase,'at':now()})
            r.abort()
            return
        if host=='codehub.gridics.com' and request.resource_type in {'document','xhr','fetch'}:
            with (GATE/'lock').open('a+') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX)
                if stop.exists():
                    r.abort()
                    return
                state=read(GATE/'state.json') if (GATE/'state.json').exists() else {}
                time.sleep(max(0,state.get('last',0)+3.5-time.time()))
                save(GATE/'state.json',{'last':time.time(),'url':request.url})
                events.append({'url':request.url,'action':'continued','kind':request.resource_type,'phase':phase,'epoch':epoch,'at':now()})
        r.continue_()
    def response(r):
        if urlsplit(r.url).hostname!='codehub.gridics.com' or r.request.resource_type not in {'document','xhr','fetch'}:
            return
        if r.status in {401,403,429}:
            save(stop,{'url':r.url,'status':r.status,'at':now()})
        try:
            content_type=r.headers.get('content-type','')
            if content_type.strip().lower().startswith('image/'):
                events.append({'url':r.url,'action':'image_body_not_saved','phase':phase})
                return
            raw=r.body()
            if raw.startswith((b'\x89PNG',b'\xff\xd8\xff',b'GIF87a',b'GIF89a')) or raw[:4]==b'RIFF' and raw[8:12]==b'WEBP':
                events.append({'url':r.url,'action':'image_body_not_saved','phase':phase})
                return
            path='response-'+str(len(responses)).zfill(5)+'.bin'
            (output/path).write_bytes(raw)
            responses.append({'url':r.url,'status':r.status,'method':r.request.method,'request_data':r.request.post_data,'content_type':content_type,'path':path,'sha256':digest(raw),'bytes':len(raw),'phase':phase,'epoch':epoch,'at':now()})
            persist()
        except Exception as error:
            failures.append({'url':r.url,'error':str(error),'phase':phase})
    def await_response(page,predicate):
        end=time.monotonic()+120
        while time.monotonic()<end:
            if stop.exists():
                raise Invalid('Publisher access stop retained')
            matches=[r for r in responses if r.get('epoch')==epoch and r.get('phase')==phase and r.get('status')==200 and predicate(r)]
            if matches:
                return matches[-1]
            page.wait_for_timeout(250)
        raise Invalid('Missing fresh native response; no opening receipt may substitute for closing witness')
    with (output/'run.lock').open('a+') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise Invalid('Another collector owns this output')
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(channel='chrome',headless=False)
                manifest['browser_version']=browser.version
                for phase in ['start','end']:
                    checkpoint=output/(phase+'-checkpoint.json')
                    previous=read(checkpoint) if checkpoint.exists() else None
                    if previous and previous.get('phase_complete'):
                        # End-to-end verify will rehash every retained receipt.
                        continue
                    context=browser.new_context(service_workers='block')
                    context.route('**/*',route)
                    page=context.new_page()
                    page.on('response',response)
                    page.goto(config['source_url'],wait_until='domcontentloaded',timeout=120000)
                    page.locator('div.section[data-path]').first.wait_for(timeout=120000)
                    if config['identity_term'].casefold() not in page.title().casefold():
                        raise Invalid('Rendered publisher identity mismatch')
                    root_response=await_response(page,lambda r: parse_qs(urlsplit(r['url']).query).get('topLevel')==['1'])
                    if '/codehub/'+str(config['document_id']) not in urlsplit(root_response['url']).path:
                        raise Invalid('Native document ID mismatch')
                    roots=json.loads(checked(output,root_response))
                    if not roots or any(r.get('docId')!=str(config['document_id']) for r in roots):
                        raise Invalid('Wrong or empty source root inventory')
                    if previous:
                        if json.loads(checked(output,previous['roots_response']))!=roots:
                            raise Invalid('Publication inventory changed during interrupted phase; use new output')
                        for row in previous['roots']:
                            checked(output,row['tree_response'])
                        # Preserve the interrupted attempt, then restart this phase
                        # under one fresh inventory/context/epoch. Never splice
                        # unrelated session receipts into a closing witness.
                        save(output/(phase+'-interrupted-'+epoch+'.json'),previous)
                        rows=[]
                    else:
                        rows=[]
                    for root in roots[len(rows):]:
                        path=root['path']
                        url=base+'#'+path
                        if page.url!=url:
                            page.goto(url,wait_until='domcontentloaded',timeout=120000)
                        source=page.locator('div.section[data-path="'+path+'"]')
                        source.wait_for(timeout=120000)
                        tree_response=await_response(page,lambda r: parse_qs(urlsplit(r['url']).query).get('tree')==['1'] and parse_qs(urlsplit(r['url']).query).get('pathes[]') in ([path],[path.lstrip('/')]))
                        dom=source.evaluate('(n)=>n.outerHTML')
                        name=phase+'-'+root['id']+'.html'
                        (output/name).write_text(dom)
                        rows.append({'root':root,'url':url,'tree_response':tree_response,'dom_path':name,'dom_sha256':digest(dom.encode())})
                        save(checkpoint,{'phase':phase,'roots_response':root_response,'roots':rows,'phase_complete':False})
                        print(json.dumps({'phase':phase,'root':root['text'],'collected':len(rows),'total':len(roots)}),flush=True)
                    save(checkpoint,{'phase':phase,'roots_response':root_response,'roots':rows,'phase_complete':True})
                    context.close()
                browser.close()
            manifest.update(status='acquired',finished_at=now(),response_errors=failures)
            save(manifest_path,manifest)
            return write_outputs(output,config)
        except Exception as error:
            manifest.update(status='interrupted',error=str(error),updated_at=now(),response_errors=failures)
            save(manifest_path,manifest)
            raise
        finally:
            persist()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['collect','verify','replay'])
    parser.add_argument('--config',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--source',help='Existing evidence for offline replay into a fresh derivative')
    args=parser.parse_args()
    try:
        config=read(args.config)
        out=Path(args.out).resolve()
        if args.action=='replay':
            if not args.source:
                raise Invalid('Replay requires --source')
            coverage=replay(Path(args.source),out,config)
        else:
            coverage=acquire(out,config,args.resume) if args.action=='collect' else verify(out,config)
        print(json.dumps(coverage,indent=2))
        return 0 if coverage['complete'] else 2
    except Exception as error:
        print(json.dumps({'complete':False,'error':str(error)}),file=sys.stderr)
        return 2


if __name__=='__main__':
    sys.exit(main())
