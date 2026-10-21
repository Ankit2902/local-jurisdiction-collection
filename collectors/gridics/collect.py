"""Full native Gridics publication acquisition in ordinary headed Chrome."""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from collectors.winboot import boot, ensure_fcntl
if __name__ == '__main__':
    boot('collectors.gridics.collect')
else:
    ensure_fcntl()
import fcntl
import argparse
import datetime
import json
import os
import shutil
import time
from urllib.parse import urlsplit, parse_qs, urlencode
from .model import Invalid, analyze, checked, digest, read, save
from .publisher import script_role, section_renderability, RENDERER_SHA256
from .image_content import is_image_content
from .source_response import response_role, read_nonimage_response

HERE = Path(__file__).resolve().parent
GATE = Path.home()/'.local/state/local-jurisdiction-collection/gridics'


def enforce_access_advisory():
    """Preserve the observed workflow stop in fresh installs, before I/O."""
    path = HERE.parent/'registry/access-advisories.json'
    try:
        catalog = read(path)
    except Exception as error:
        raise Invalid('Published access advisory catalog missing/unreadable; known Gridics PDF HEAD 403 stop remains. Use the complete package.') from error
    if catalog.get('schema_version') != 1 or not isinstance(catalog.get('advisories'),list):
        raise Invalid('Unsupported published access advisory catalog; known Gridics workflow stop remains')
    advisories = [a for a in catalog['advisories'] if a.get('family') == 'gridics' and a.get('operator_review_required') is True]
    if not advisories:
        raise Invalid('Known Gridics PDF HEAD 403 stop is absent from advisory catalog; no automatic release or retry')
    raise Invalid('Published Gridics workflow access stop requires operator review before browser startup: exact source-linked Cupertino PDF HEAD returned HTTP 403. Other publication routes after that event are untested. Offline verify/replay remain available; no automatic retry or clearing.')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sources():
    return {p.name:digest(p.read_bytes()) for p in sorted(HERE.glob('*.py'))}


def native_tree_url(source_url, document_id, root, revision):
    """Exact public client loadData route, source inventory ID + pinned revision."""
    base=urlsplit(source_url)
    if base.scheme!='https' or base.hostname!='codehub.gridics.com' or not str(document_id).isdigit() or not str(revision).isdigit():
        raise Invalid('Unbound native source identity/revision')
    if root.get('docId')!=str(document_id) or not root.get('id') or root.get('path')!='/'+root['id']:
        raise Invalid('Source root identity/path mismatch')
    return 'https://codehub.gridics.com/api/v1/codehub/'+str(document_id)+'?'+urlencode({'tree':1,'_format':'json','pathes[]':root['id'],'revision':revision})


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
    enforce_access_advisory()
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
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
        if host=='codehub.gridics.com' and request.resource_type in {'document','xhr','fetch','stylesheet'}:
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
        role=response_role(r.url,r.request.resource_type)
        if role is None:
            return
        if r.status in {401,403,429}:
            save(stop,{'url':r.url,'status':r.status,'at':now()})
        try:
            content_type=r.headers.get('content-type','')
            raw,image_reason=read_nonimage_response(r)
            if raw is None:
                events.append({'url':r.url,'action':'image_body_not_saved','reason':image_reason,'phase':phase})
                return
            path='response-'+str(len(responses)).zfill(5)+'.bin'
            (output/path).write_bytes(raw)
            row={'url':r.url,'status':r.status,'method':r.request.method,'request_data':r.request.post_data,'resource_type':r.request.resource_type,'response_role':role,'content_type':content_type,'path':path,'sha256':digest(raw),'bytes':len(raw),'phase':phase,'epoch':epoch,'at':now()}
            if role=='stylesheet':
                try:
                    row['source_document_url']=r.request.frame.url
                except Exception:
                    row['source_document_url']=None
                    row['source_document_binding_error']='Observed stylesheet request has no accessible owner frame'
                row['stylesheet_note']='Actually requested first-party stylesheet original source; no CSS URLs or image assets imported by collector'
            responses.append(row)
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
                    revision=parse_qs(urlsplit(root_response['url']).query).get('revision',[])
                    if len(revision)!=1:
                        raise Invalid('Native inventory has no single pinned revision')
                    for root in roots[len(rows):]:
                        path=root['path']
                        url=base+'#'+path
                        api=native_tree_url(config['source_url'],config['document_id'],root,revision[0])
                        def matches_tree(r):
                            query=parse_qs(urlsplit(r['url']).query)
                            return urlsplit(r['url']).path=='/api/v1/codehub/'+str(config['document_id']) and query.get('tree')==['1'] and query.get('revision')==revision and query.get('pathes[]') in ([path],[path.lstrip('/')])
                        # First retain the complete source tree, including roots
                        # the public client intentionally cannot put in its DOM.
                        fresh=[r for r in responses if r.get('epoch')==epoch and r.get('phase')==phase and r.get('status')==200 and matches_tree(r)]
                        if not fresh:
                            fetched=page.evaluate('''async url=>{const r=await fetch(url);const mime=r.headers.get('content-type')||'';if(mime.trim().toLowerCase().startsWith('image/')){if(r.body)await r.body.cancel();return {status:r.status,url:r.url,image_body_cancelled:true}}await r.arrayBuffer();return {status:r.status,url:r.url}}''',api)
                            if stop.exists() or fetched['status']!=200 or fetched.get('image_body_cancelled'):
                                raise Invalid('Native tree request failed; retained source cannot be skipped')
                        tree_response=await_response(page,matches_tree)
                        eligibility=section_renderability(root)
                        renderer_qualified=any(script_role(r.get('url',''))=='renderer' and r.get('epoch')==epoch and r.get('phase')==phase and r.get('status')==200 and digest(checked(output,r))==RENDERER_SHA256 for r in responses)
                        row={'root':root,'url':url,'tree_response':tree_response,'dom_path':None,'dom_sha256':None,'renderability':eligibility,'renderer_profile_qualified':renderer_qualified}
                        if eligibility['eligible'] or not renderer_qualified:
                            if page.url!=url:
                                page.goto(url,wait_until='domcontentloaded',timeout=120000)
                            source=page.locator('div.section[data-path="'+path+'"]')
                            try:
                                source.wait_for(timeout=120000)
                                dom=source.evaluate('(n)=>n.outerHTML')
                                name=phase+'-'+root['id']+'.html'
                                (output/name).write_text(dom)
                                row.update(dom_path=name,dom_sha256=digest(dom.encode()),render_status='captured')
                            except PlaywrightTimeout:
                                if stop.exists():
                                    raise Invalid('Publisher stop observed while waiting for DOM')
                                row.update(render_status='dom_unavailable',render_diagnostic={'reason':'Ordinary root DOM unavailable after normal navigation; no renderer exemption claimed; native-only evidence retained'})
                        else:
                            row.update(render_status='source_unrenderable',render_diagnostic={'reason':'Pinned public renderer cannot expose this source root; never drop its native descendants','source_reasons':eligibility['reasons']})
                        if row.get('render_status')!='captured':
                            diagnostic=page.content();name=phase+'-'+root['id']+'-diagnostic.html';(output/name).write_text(diagnostic)
                            row.update(diagnostic_dom_path=name,diagnostic_dom_sha256=digest(diagnostic.encode()))
                        rows.append(row)
                        save(checkpoint,{'phase':phase,'roots_response':root_response,'roots':rows,'phase_complete':False})
                        print(json.dumps({'phase':phase,'root_id':root['id'],'root':root.get('text'),'render_status':row['render_status'],'collected':len(rows),'total':len(roots)}),flush=True)
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
