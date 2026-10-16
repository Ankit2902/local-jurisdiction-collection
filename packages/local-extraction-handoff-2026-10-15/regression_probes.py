#!/usr/bin/env python3
"""Run synthetic offline behavior probes against the existing collector snapshot.

A failed criterion identifies work for the tech team. Exit 0 means probes ran;
--require-pass returns 1 while any criterion fails. Never retrieves a source.
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run(code_root):
    sys.path.insert(0, str(code_root))
    from adapters.browser_vendor_collectors import BrowserVendorCollector, Publication, FixtureTransport
    from adapters import kingcounty_code, gridics_codehub
    results = []
    def record(name, criterion, passed, observed):
        results.append({'probe': name, 'acceptance_criterion': criterion, 'passes': bool(passed), 'observed': observed})
    with tempfile.TemporaryDirectory(prefix='local-code-probes-') as tmp:
        for city, code in [('bellingham', 'BMC'), ('everett', 'EMC')]:
            base = f'https://{city}.municipal.codes/{code}'
            c = BrowserVendorCollector(Publication(city, city, 'municipal_codes', base+'/contents'), FixtureTransport({}), Path(tmp)/city)
            allowed = c._allowed(base+'/1.01.010')
            record(city+'_publication_boundary', 'A /contents discovery URL allows observed section routes under the same publication.', allowed, {'section_allowed': allowed})
        c = BrowserVendorCollector(Publication('example','Example','municipal_codes','https://example.municipal.codes/Code'),FixtureTransport({}),Path(tmp)/'toc')
        c._sections('<main><h1>Contents</h1><nav><a href="/Code/1">Title 1</a></nav></main>','https://example.municipal.codes/Code',[])
        record('municipal_codes_toc_fallback','A pure contents page emits no provision.',not c.rows,{'rows_emitted':len(c.rows),'numbers':[r['section_number'] for r in c.rows]})
        c = BrowserVendorCollector(Publication('example','Example','ecode360','https://ecode360.com/123'),FixtureTransport({}),Path(tmp)/'ecode')
        c._add('1.01 Same heading','Municipal body','https://ecode360.com/124',['Municipal Code'],'1.01','Same heading')
        c._add('1.01 Same heading','Charter body','https://ecode360.com/125',['City Charter'],'1.01','Same heading')
        record('ecode360_family_identity','Different source nodes/families with the same printed label remain separate.',len(c.rows)==2,{'rows_emitted':len(c.rows)})
        rows=kingcounty_code.parse_title_sections('<p><b>1.02.010 Example.</b></p><p>Operative second paragraph.</p><table><tr><td>Required table content.</td></tr></table>','https://example.test/title.htm')
        body='\n'.join(r['full_text'] for r in rows)
        record('king_county_continuation','Full section body includes following paragraphs and tables until the next legal section.', 'Operative second paragraph.' in body and 'Required table content.' in body, {'body':body})
        rows=gridics_codehub.parse_sections_html('<h2>TITLE 1: GENERAL</h2><h3>CHAPTER 1.01: RULES</h3><div class="section"><a><h4>1.01.010 Duty.</h4></a><ul><li><p>One obligation.</p></li></ul></div>')
        body='\n'.join(r['full_text'] for r in rows)
        record('gridics_nested_blocks','A nested paragraph inside a list item is serialized once.',body.count('One obligation.')==1,{'body':body})
    return {'kind':'synthetic_offline_probes','code_root':str(code_root),'probes':results,'failed_criteria':sum(not x['passes'] for x in results)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code-root',type=Path,default=ROOT/'reference-code')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--require-pass',action='store_true')
    args=parser.parse_args()
    try:
        result=run(args.code_root)
    except ImportError as exc:
        parser.exit(2, f'Missing dependency: {exc}. Install beautifulsoup4 and requests in an isolated environment.\n')
    text=json.dumps(result,indent=2)+'\n'
    if args.output:args.output.write_text(text)
    else:print(text,end='')
    return 1 if args.require_pass and result['failed_criteria'] else 0

if __name__=='__main__':
    raise SystemExit(main())
