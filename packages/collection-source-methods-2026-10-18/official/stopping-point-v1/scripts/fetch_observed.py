"""One observed public URL, reviewed serial transport; no automatic retries."""
import argparse,hashlib,json,pathlib,sys,urllib.parse
sys.dont_write_bytecode=True
import transport
HERE=pathlib.Path(__file__).resolve().parent
BASE=HERE.parent
def preflight(url):
    p=urllib.parse.urlparse(url);host=(p.hostname or '').lower()
    if p.scheme!='https':raise ValueError('Only observed HTTPS sources are qualified')
    for row in json.loads((BASE/'preflight/retained-refusals.json').read_text()):
        if host==row['host'] or host.removeprefix('www.')==row['host'].removeprefix('www.'):
            raise RuntimeError('Retained official host refusal; no retry: '+row['url'])
    blocked={'municode':['municode.com','api.municode.com'],'american-legal':['amlegal.com'],'ecode360':['ecode360.com'],'municipal.codes':['municipal.codes'],'gridics':['gridics.com']}
    for advisory in json.loads((BASE/'preflight/access-advisories.json').read_text())['advisories']:
        if advisory.get('operator_review_required'):
            if any(host==d or host.endswith('.'+d)for d in blocked.get(advisory['family'],[])):
                raise RuntimeError('Retained publisher-family stop; no request: '+advisory['family'])
    return host
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--url',required=True);parser.add_argument('--out',required=True,type=pathlib.Path);args=parser.parse_args()
    assert not args.out.exists(),'Fresh acquisition directory required'
    preflight(args.url)
    reserve=transport.reserve
    def checked_reserve(url):preflight(url);return reserve(url)
    transport.reserve=checked_reserve
    data,receipt=transport.fetch(args.url)
    args.out.mkdir(parents=True)
    receipt['executed_sources']={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest()for n in ['transport.py','fetch_observed.py']}
    receipt['no_automatic_retry']=True
    (args.out/'body.bin').write_bytes(data);(args.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt.get(k)for k in ['url','status','final_url','bytes','sha256','access_stop','policy_omitted_image']}))
    return 3 if receipt.get('access_stop')or receipt['status']!=200 or receipt.get('policy_omitted_image')else 0
if __name__=='__main__':raise SystemExit(main())
