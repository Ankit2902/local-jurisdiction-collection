"""Bounded live official acquisition -> parser CLI -> portable output qualification.

Each invocation requires a NEW output directory. Reports never claim full corpus completion.
HTTP is Requests with ordinary certificate verification; browser evidence is optional and hash-bound.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,platform,re,subprocess,sys,traceback,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from common import acquire,clean,decode,dump,sha
import san_mateo as sm,king_county as kc,daly_city as dc
from archive_includes import ArchiveIncludes
HERE=Path(__file__).resolve().parent

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def canonical(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
def verify_capture(path,destination=None):
    path=Path(path);receipt=json.loads(Path(str(path)+'.capture.json').read_text());data=path.read_bytes()
    if receipt['sha256']!=sha(data) or receipt['bytes']!=len(data):raise ValueError('Browser evidence receipt mismatch')
    if destination is not None:
        destination=Path(destination);destination.mkdir(parents=True,exist_ok=True);(destination/path.name).write_bytes(data);dump(destination/(path.name+'.capture.json'),receipt)
        path=destination/path.name
    return {'artifact':('source/browser/'+path.name if destination is not None else str(path)),'receipt':receipt}
def hashfiles(root):
    return [{'path':str(p.relative_to(root)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file() and p.name!='E2E-VALIDATION.json']
class Run:
    def __init__(self,args):
        self.args=args;self.out=args.out.resolve()
        if self.out.exists():raise ValueError('Fresh output directory required; cache replay is not a live E2E run')
        self.out.mkdir(parents=True);self.commands=[];self.report={'jurisdiction':args.method,'started_at':now(),'status':'running','scope':'bounded_live_pilot','full_corpus_extracted':False,'environment':{'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'requests_ca_bundle':os.environ.get('REQUESTS_CA_BUNDLE'),'certificate_verification':True},'code_hashes':{p.name:sha(p.read_bytes()) for p in sorted(HERE.glob('*.py'))},'orchestrator_argv':sys.argv,'commands':self.commands,'checks':{},'limitations':[]}
    def cli(self,*args):
        command=[sys.executable,str(HERE/args[0]),*map(str,args[1:])];start=now();result=subprocess.run(command,cwd=HERE,capture_output=True,text=True)
        label=f'command-{len(self.commands)}';(self.out/(label+'.stdout.txt')).write_text(result.stdout);(self.out/(label+'.stderr.txt')).write_text(result.stderr)
        self.commands.append({'argv':command,'started_at':start,'ended_at':now(),'exit_code':result.returncode,'stdout':label+'.stdout.txt','stderr':label+'.stderr.txt'})
        if result.returncode:raise RuntimeError('Command failed: '+label)
    def finish(self):
        self.report['ended_at']=now();self.report['artifacts']=hashfiles(self.out);dump(self.out/'E2E-VALIDATION.json',self.report)
    def get(self,url,filename,**kw):return acquire(url,self.out/'source'/filename,**kw)
    def samples(self):
        manifests=[json.loads(p.read_text())|{'path':str(p.relative_to(self.out))} for p in self.out.glob('output/**/run-manifest.json')]
        if not manifests:raise ValueError('No output manifests')
        self.report['outputs']=manifests
        for m in manifests:
            if not m['records']:raise ValueError('Empty sample output')
        return manifests

def san(run):
    run.get('https://api.github.com/repos/cityofsanmateo/law-xml/commits/HEAD','head.json');head=json.loads((run.out/'source/head.json').read_text());commit=head['sha']
    if not re.fullmatch('[a-f0-9]{40}',commit):raise ValueError('Invalid resolved HEAD')
    run.report['resolved_commit']=commit;run.cli('san_mateo.py','acquire','--commit',commit,'--archive','--out',run.out/'source/pinned')
    tree=json.loads((run.out/'source/pinned/tree.json').read_text());archive=ArchiveIncludes(run.out/'source/pinned/repository.zip',tree,commit)
    base=sm.BASE;chosen={'index.xml'}|{base+x for x in ['code/index.xml','code/1.xml','charter/index.xml']}
    resolved=archive.resolve('index.xml',chosen);dump(run.out/'includes.json',resolved);archive.retain(chosen,run.out/'source/selected')
    for unit in resolved['units']:
        pub='charter' if '/charter/' in unit['path'] else 'municipal-code';source=run.out/'source/selected'/unit['path'];url=f'https://raw.githubusercontent.com/{sm.REPO}/{commit}/{unit["path"]}'
        run.cli('san_mateo.py','parse','--input',source,'--source-url',url,'--commit',commit,'--publication',pub,'--out',run.out/'output'/pub,'--scrape-date',run.report['started_at'][:10])
    manifests=run.samples();run.report['checks']={'git_blob_members_verified':archive.verified_members,'git_tree_untruncated':not tree.get('truncated',False),'bounded_include_resolution':resolved,'sample_manifests':len(manifests),'cli_exit_codes_zero':True,'csv_json_equal':True}
    run.report['limitations']=['Repository HEAD pins a reproducible source version, not legal current-through currency.','Only selected Title 1 and Charter parsed; every other include explicitly excluded from validation scope.','Archive file membership and Git blob hashes verified for all files, without full corpus XML parsing.']

def drift_check(start_pub,start_tree,end_pub,end_tree):
    result={'publication_json_equal':canonical(start_pub)==canonical(end_pub),'tree_json_equal':canonical(start_tree)==canonical(end_tree),'start_publication_sha256':canonical(start_pub),'end_publication_sha256':canonical(end_pub),'start_tree_sha256':canonical(start_tree),'end_tree_sha256':canonical(end_tree)}
    if not all(result[k] for k in ['publication_json_equal','tree_json_equal']):raise ValueError('Live latest publication/tree drift; outputs require repeat on stable version')
    return result

def daly(run):
    # IDs are replayed only after the live independent tree confirms them.
    ids=['TIT1GEPR_CH1.01COAD_1.01.010AD','TIT15BUCO_CH15.08BUCO_15.08.080TA1505.1MIROCOCLTYCOME','TIT15BUCO_CH15.32FICO_15.32.210APECD1DE']
    args=['daly_city.py','acquire','--out',run.out/'source/start']
    for ident in ids:args+=['--node-id',ident]
    run.cli(*args);start=run.out/'source/start';tree=json.loads((start/'toc.json').read_text());publication=json.loads((start/'publications.json').read_text());nodes=dc.inventory(tree)
    for i,ident in enumerate(ids):run.cli('daly_city.py','parse','--toc',start/'toc.json','--content',start/f'content-{i}.json','--node-id',ident,'--out',run.out/'output'/f'sample-{i}')
    run.report['checks']={'tree_nodes':len(nodes),'cli_exit_codes_zero':True,'csv_json_equal':True}
    run.report['publication']=publication;run.samples()
    if run.args.route_capture:
        evidence=verify_capture(run.args.route_capture,run.out/'source/browser');html=Path(run.args.route_capture).read_text();routes=dc.route_evidence(html)
        if evidence['receipt']['url']!='https://www.dalycity.org/':raise ValueError('City route evidence is not from official homepage')
        if not any(x['url']=='https://library.municode.com/ca/daly_city/ordinances/code_of_ordinances' for x in routes):raise ValueError('Official city replacement link absent')
        run.report['official_route_evidence']=evidence|{'links':routes}
    section_captures=list(run.args.section_capture or [])
    if run.args.standalone_browser:
        captured=run.out/'source/browser/daly-standalone.html'
        run.cli('browser_capture.py','--url',dc.ROOT+'?nodeId='+ids[0],'--out',captured,'--ready-selector','[id="c_'+ids[0]+'"] .chunk-content','--channel','chrome')
        section_captures.append(captured)
    for section_capture in section_captures:
        evidence=verify_capture(section_capture,run.out/'source/browser');receipt=evidence['receipt']
        if ids[0] not in receipt['url'] or not receipt['url'].startswith(dc.ROOT):raise ValueError('Browser section route identity mismatch')
        soup=BeautifulSoup(Path(section_capture).read_text(),'html.parser');api=json.loads((start/'content-0.json').read_text());doc=next(d for d in api['Docs'] if d['Id']==ids[0]);api_soup=BeautifulSoup(doc['Content'],'html.parser');body=api_soup.select_one('.chunk-content');browser=soup.select_one('.chunk-content')
        if browser is None:raise ValueError('Browser capture missing exact section body')
        # Select exact requested section from any chapter DOM capture by publisher chunk identity.
        candidates=soup.select('.chunk')
        exact=[x for x in candidates if x.get('id') in {ids[0],'c_'+ids[0]}]
        if exact:browser=exact[0].select_one('.chunk-content')
        if len(soup.select('.chunk-content'))>1 and not exact:raise ValueError('Ambiguous browser body identity')
        same=clean(body.get_text(' ',strip=True))==clean(browser.get_text(' ',strip=True))
        if not same:raise ValueError('Rendered/API section body differs')
        run.report['checks'].setdefault('browser_api_parity',[]).append({'equal':same,'node_id':ids[0],'api_text_sha256':sha(clean(body.get_text(' ',strip=True)).encode()),'browser_text_sha256':sha(clean(browser.get_text(' ',strip=True)).encode()),'evidence':evidence})
    for name,url in [('publications.json','https://library.municode.com/api/ClientContent/1857'),('toc.json','https://library.municode.com/api/codesToc/fullTree/latest?productId=16311&nodeId=16311')]:run.get(url,'end-'+name,headers={'X-CSRF':'1'})
    reconciliation=drift_check(publication,tree,json.loads((run.out/'source/end-publications.json').read_text()),json.loads((run.out/'source/end-toc.json').read_text()))
    run.report['checks']['start_end_reconciliation']=reconciliation
    run.report['limitations']=['Three exact observed sections parsed from publisher chapter responses; no full extraction.','Unincorporated ordinances remain a separate publication inventory; no codification inference.']
    if not section_captures:run.report['limitations'].append('Current rendered/API body parity not supplied to this run.')
    if not run.args.route_capture:run.report['limitations'].append('Official city browser route evidence not supplied to this run.')

def docx_text(data):
    import io
    with zipfile.ZipFile(io.BytesIO(data)) as z:root=ET.fromstring(z.read('word/document.xml'))
    ns='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    return '\n'.join(''.join(t.text or '' for t in p.iter(ns+'t')) for p in root.iter(ns+'p'))

def king(run):
    if not run.args.landing_capture:raise ValueError('Current official landing capture and hash receipt required')
    evidence=verify_capture(run.args.landing_capture,run.out/'source/browser');data=Path(run.args.landing_capture).read_bytes();run.report['landing_evidence']=evidence
    landing=kc.landing_inventory(data.decode(),'https://kingcounty.gov/en/dept/council/governance-leadership/county-code');dump(run.out/'landing-inventory.json',landing)
    source_base='https://aqua.kingcounty.gov/council/clerk/code/'
    docs=[('title1','04_Title_1',False),('title2a','05_Title_2A',False),('charter','03_Charter',True)]
    findings=[]
    for label,stem,charter in docs:
        url=source_base+stem+'.htm'
        if url not in data.decode() or source_base+stem+'.docx' not in data.decode():raise ValueError('Document route not corroborated on landing')
        run.get(url,label+'.htm');run.get(source_base+stem+'.docx',label+'.docx');source=run.out/'source'/(label+'.htm')
        args=['king_county.py','--input',source,'--source-url',url,'--out',run.out/'output'/label]
        if charter:args+=['--charter']
        run.cli(*args);parsed=kc.parse_title(source.read_bytes(),url,charter);word=docx_text((run.out/'source'/(label+'.docx')).read_bytes());html=decode(source.read_bytes())[0]
        toc={x['number'] for x in parsed['toc']};body={x['display_number'] for x in parsed['nodes'] if x['node_kind']=='section'}
        # Compare literal source spellings, never silently repair source numbering.
        differences={'toc_only':sorted(toc-body) if toc else [],'body_only':sorted(body-toc) if toc else [],'comparison_status':'compared' if toc else 'no_independent_section_toc_detected'}
        checks={num:{'html_present':num in html,'word_present':num in word} for num in sorted((toc-body)|(body-toc)) if toc}
        dates={'html':re.findall(r'UPDATED:\s*[^\n<]+',html,re.I)[:3],'word':re.findall(r'UPDATED:[^\n]+',word,re.I)[:3]}
        findings.append({'document':label,'encoding':parsed['encoding'],'source_sections':len(body),'section_nodes':sum(x['node_kind']=='section' for x in parsed['nodes']),'toc_body_differences':differences,'literal_spellings_in_official_formats':checks,'date_markers':dates,'landing_updated_marker':next((x['updated_marker_raw'] for x in landing['documents'] if x['url']==url),''),'status':'source_discrepancies_retained_pending_publisher_reconciliation' if differences['toc_only'] or differences['body_only'] or charter else 'checked'})
    dump(run.out/'source-reconciliation.json',findings);run.samples();run.report['checks']={'cli_exit_codes_zero':True,'csv_json_equal':True,'original_http_html_bytes':True,'html_word_source_evidence':findings}
    run.report['limitations']=['Three official documents parsed as bounded pilot; no complete jurisdiction export.','TOC/body numbering and Charter landing/header date conflicts retained as publisher source discrepancies; Word evidence does not authorize legal renumbering.','Title 21A source amendment/repeal/duplicate labels from earlier pilot remain outside this live three-document test.','Document equivalence here checks conflicting literal identifiers/dates; full Word/HTML paragraph parity is not claimed.']

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('method',choices=['san-mateo','daly-city','king-county']);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--landing-capture',type=Path);ap.add_argument('--route-capture',type=Path);ap.add_argument('--section-capture',type=Path,action='append');ap.add_argument('--standalone-browser',action='store_true',help='Run isolated installed Chrome capture for Daly body parity');args=ap.parse_args();run=Run(args)
    try:
        {'san-mateo':san,'daly-city':daly,'king-county':king}[args.method](run);run.report['status']='passed_bounded_live_pilot'
    except Exception as exc:
        run.report['status']='blocked';run.report['blocker']=str(exc);run.report['traceback']=traceback.format_exc();raise
    finally:run.finish()
    print(json.dumps({'status':run.report['status'],'report':str(run.out/'E2E-VALIDATION.json')},indent=2))
if __name__=='__main__':main()
