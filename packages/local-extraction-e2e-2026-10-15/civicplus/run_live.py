#!/usr/bin/env python3
"""Execute bounded fresh discovery -> acquisition -> parse -> verify, recording commands."""
import argparse,hashlib,json,os,platform,subprocess,sys
from importlib.metadata import version,PackageNotFoundError
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--jurisdiction',choices=['portland-me','rockland-me'],required=True);p.add_argument('--out',required=True);p.add_argument('--runtime',choices=['http','playwright','cua-files'],required=True);p.add_argument('--capture');p.add_argument('--id',action='append',required=True);p.add_argument('--channel',default='chrome');p.add_argument('--review-file');p.add_argument('--executable-path');args=p.parse_args()
 out=Path(args.out).resolve()
 if out.exists():raise ValueError('Fresh E2E run requires a new output directory; no existing cache is accepted')
 out.mkdir(parents=True);package=out/'package'
 report={'jurisdiction':args.jurisdiction,'runtime':args.runtime,'started_at':now(),'commands':[],'environment':{'python_executable':sys.executable,'python_version':platform.python_version(),'platform':platform.platform(),'requests_ca_bundle':os.environ.get('REQUESTS_CA_BUNDLE'),'tls_checks_disabled':False},'code_hashes':{n:sha(ROOT/n) for n in ['civicplus.py','review_pdf.py','run_live.py','capture_browser.py','capture_cua.mjs']},'selected_ids':args.id,'corpus_complete':False}
 def command(argv):
  before=now();result=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True);entry={'argv':argv,'cwd':str(ROOT),'started_at':before,'finished_at':now(),'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr};report['commands'].append(entry)
  print(json.dumps(entry),flush=True)
  if result.returncode:raise RuntimeError('Command failed: '+argv[2])
 for name in ['requests','pdfplumber','beautifulsoup4','json5','playwright']:
  try:report['environment'][name+'_version']=version(name)
  except PackageNotFoundError:report['environment'][name+'_version']=None
 try:
  browser_extra=['--executable-path',args.executable_path] if args.executable_path else []
  extra=[]
  if args.runtime in ['playwright','cua-files']:
   capture=Path(args.capture).resolve() if args.capture else out/'capture'
   if args.runtime=='playwright':command([sys.executable,str(ROOT/'capture_browser.py'),'--jurisdiction',args.jurisdiction,'--out',str(capture),'--channel',args.channel,*browser_extra])
   receipt=json.loads((capture/'capture-receipt.json').read_text())
   if receipt['result']!='captured':raise ValueError('Browser capture was not successful')
   for name,h in receipt['files'].items():
    if sha(capture/name)!=h:raise ValueError('Capture hash mismatch: '+name)
   report['browser_capture_receipt']=receipt;report['browser_capture_path']=str(capture)
   extra=['--index-html',str(capture/'index.html'),'--transport',receipt['runtime'],'--retrieved-at',receipt['finished_at']]
   if args.jurisdiction=='portland-me':extra+=['--rendered-html',str(capture/'widget.html')]
  command([sys.executable,str(ROOT/'civicplus.py'),'discover','--jurisdiction',args.jurisdiction,'--out',str(package),*extra])
  acquire=[sys.executable,str(ROOT/'civicplus.py'),'acquire','--package',str(package)]
  for ident in args.id:acquire+=['--id',ident]
  command(acquire)
  parse_command=[sys.executable,str(ROOT/'civicplus.py'),'parse','--package',str(package)]
  if args.review_file:
   review=Path(args.review_file).resolve();parse_command+=['--review-file',str(review)];report['review_file']={'path':str(review),'sha256':sha(review)}
  command(parse_command)
  command([sys.executable,str(ROOT/'civicplus.py'),'verify','--package',str(package)])
  if args.runtime in ['http','playwright']:
   final_extra=[]
   if args.runtime=='playwright':
    final_capture=out/'final-capture';command([sys.executable,str(ROOT/'capture_browser.py'),'--jurisdiction',args.jurisdiction,'--out',str(final_capture),'--channel',args.channel,*browser_extra])
    final_receipt=json.loads((final_capture/'capture-receipt.json').read_text());report['final_browser_capture_receipt']=final_receipt
    final_extra=['--index-html',str(final_capture/'index.html'),'--transport','standalone_playwright','--retrieved-at',final_receipt['finished_at']]
    if args.jurisdiction=='portland-me':final_extra+=['--rendered-html',str(final_capture/'widget.html')]
   command([sys.executable,str(ROOT/'civicplus.py'),'discover','--jurisdiction',args.jurisdiction,'--out',str(out/'final-inventory'),*final_extra])
   initial=json.loads((package/'inventory.json').read_text());final=json.loads((out/'final-inventory/inventory.json').read_text())
   signature=lambda inv:[{key:d[key] for key in ['node_id','publication_id','label','scope','source_order']} for d in inv['documents']]
   coherent=signature(initial)==signature(final);report['inventory_recheck']={'method':'fresh official index/capture after acquisition and parse','coherent':coherent,'initial_raw_sha256':initial['inventory_sha256'],'final_raw_sha256':final['inventory_sha256'],'initial_documents':len(initial['documents']),'final_documents':len(final['documents']),'legal_currency_note':'Observed labels/revision markers compared; legal current-through remains unknown.'}
   if not coherent:raise ValueError('Official document inventory changed during run; reconcile before acceptance')
  else:report['inventory_recheck']={'coherent':None,'method':'Use reconcile_cua.py after a fresh final capture; automated CUA access is intentionally separate from standalone Python.'}
  report.update(live_acquisition_status='passed_bounded',validation=json.loads((package/'validation-report.json').read_text()),input_hashes={str(f.relative_to(out)):sha(f) for f in sorted((package/'raw').rglob('*')) if f.is_file()},output_hashes={str(f.relative_to(out)):sha(f) for f in sorted(package.rglob('*')) if f.is_file() and 'raw' not in f.relative_to(package).parts})
 except Exception as e:report.update(live_acquisition_status='blocked',error=str(e))
 report['finished_at']=now();(out/'E2E-VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['live_acquisition_status']=='passed_bounded' else 2
if __name__=='__main__':sys.exit(main())
