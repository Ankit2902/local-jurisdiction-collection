#!/usr/bin/env python3
"""Independently audit actual fresh headed DOM against delivered importer exports.
No network is permitted. Inputs are explicit receipts; baseline/synthetic fixtures
are never counted as fresh legal acquisition.
"""
import argparse,copy,csv,hashlib,importlib,json,re,sys
from pathlib import Path
from urllib.parse import urljoin
from unittest.mock import patch
from bs4 import BeautifulSoup
HERE=Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def tokens(s):return re.findall(r'\w+|[^\w\s]',s,re.UNICODE)
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def lines(p):return [json.loads(s) for s in p.read_text().splitlines()]
def audit_source(receipt_path,package,out):
    receipt_path=Path(receipt_path);r=json.loads(receipt_path.read_text());rawpath=receipt_path.parent/r['raw_artifact_path'];raw=rawpath.read_bytes();url=r['job']['url'];b=r['browser_state'];a=r['after_capture']
    assert r['accepted'] and r['acquisition_mode']=='fully_standalone_headed' and r['operator_assisted'] is False
    assert r['finished_at']>='2026-10-16' and r['final_document_http_status']==200 and not r.get('rate_limit')
    assert sha(raw)==r['sha256']==b['sha256']==a['sha256'];assert b['identity']==a['identity'] and b['url']==a['url']==url
    assert r['runtime']['fresh_context'] and r['runtime']['storage_state_imported'] is False
    assert not any(x['status']==429 for x in r['response_chronology'])
    identity=b['identity'];registry=json.loads((package/'route-registry.json').read_text());row=next(x for x in registry if x['slug']==r['job']['slug']);assert row['customer_id']==identity['customer_id'] and str(row['code_id'])==identity['code_id']
    source=BeautifulSoup(raw,'html.parser');toc=source.select('#toc .contentTitle[data-code-content-type][data-guid]');tocids=list(dict.fromkeys(t['data-guid'] for t in toc));assert tocids==[t['node_id'] for t in b['toc']]
    actual_headers={h['data-guid']:h for h in source.select('header .contentTitle[data-code-content-type][data-guid]')};bodies={nid:source.find(id=nid+'_content') for nid in tocids};assert all(bodies.values());assert len(bodies)==len(b['section_bodies'])
    ing=importlib.import_module('ingest_standalone');e=importlib.import_module('ecode360')
    with patch('requests.sessions.Session.request',side_effect=AssertionError('Publisher network disabled during independent review')):
        report=ing.ingest(receipt_path,row['jurisdiction'],out/'import')
        assert report['standalone_e2e_verified'] and report['standalone_automated_acquisition_verified']
        replay=e.replay(out/'import/inventory.json',out/'import/imported/artifacts.json',out/'independent-clean')
        e.replay(out/'import/inventory.json',out/'import/imported/artifacts.json',out/'independent-resume',stop_after=1)
        e.replay(out/'import/inventory.json',out/'import/imported/artifacts.json',out/'independent-resume')
    folder=out/'import/exports';rows=json.loads((folder/'aggregate-fulltext.json').read_text())['provisions'];prov=lines(folder/'record-provenance.jsonl');nodes=lines(folder/'source-nodes.jsonl');dispositions=lines(folder/'node-dispositions.jsonl')
    with (folder/'aggregate-fulltext.csv').open(encoding='utf-8-sig',newline='') as f:assert rows==list(csv.DictReader(f))
    pub=folder/'publications/municipal-code'
    assert rows==json.loads((pub/'fulltext.json').read_text())['provisions']
    with (pub/'fulltext.csv').open(encoding='utf-8-sig',newline='') as f:assert rows==list(csv.DictReader(f))
    tocrows=json.loads((folder/'aggregate-toc.json').read_text())['provisions'];assert tocrows==[dict(x,full_text='') for x in rows]
    assert len(rows)==len(prov)==len(nodes)==len(dispositions)==len(tocids)
    assert [p['node_id'] for p in prov]==tocids and len({p['record_id'] for p in prov})==len(rows)
    for f in ['aggregate-fulltext.csv','aggregate-fulltext.json','record-provenance.jsonl','source-nodes.jsonl','node-dispositions.jsonl']:
        assert (folder/f).read_bytes()==(out/'independent-clean'/f).read_bytes()==(out/'independent-resume'/f).read_bytes()
    artifacts=json.loads((out/'import/imported/artifacts.json').read_text())['artifacts'];artifact_sha={x['sha256'] for x in artifacts};comparisons=[]
    for record,p in zip(rows,prov):
        nid=p['node_id'];heading=actual_headers[nid];body=BeautifulSoup(str(bodies[nid]),'html.parser')
        for nested in list(body.select('[id$="_content"]')):
            if nested.get('id')!=nid+'_content' and nested.get('id','').removesuffix('_content') in bodies:nested.decompose()
        for el in body.select('script,style,button,input,svg,noscript'):el.decompose()
        images=[]
        for im in body.select('img'):
            images.append({'src':im.get('src',''),'alt':im.get('alt','')});im.replace_with('[IMAGE]'+(' '+im.get('alt') if im.get('alt') else ''))
        plain=BeautifulSoup(record['full_text'],'html.parser');semantic=BeautifulSoup(p['semantic_html'],'html.parser');sourcetokens=tokens(body.get_text(' ',strip=True));outtokens=tokens(plain.get_text(' ',strip=True))
        assert sourcetokens==outtokens==tokens(semantic.get_text(' ',strip=True)),nid+' exact token/body order mismatch'
        num=heading.select_one('.titleNumber').get_text(' ',strip=True).removeprefix('§').strip();assert record['section_number']==num
        assert record['source_url']=='https://ecode360.com/'+nid+'#'+nid and p['locator']=={'kind':'html-id','value':nid+'_content'}
        assert p['source_version']=='publisher-code-'+identity['code_id']+'-date-'+identity['currency_raw']
        assert record['jurisdiction']==row['jurisdiction'] and record['scrape_date']==r['finished_at'][:10]
        assert all(o['sha256'] in artifact_sha and o['transport']==r['transport'] and o['retrieved_at']==r['finished_at'] for o in p['origins'])
        structures={}
        for tag in ['table','tr','td','th','sup','sub','ol','ul','li','blockquote']:
            sig=lambda el:(tokens(el.get_text(' ',strip=True)),el.get('rowspan'),el.get('colspan'),el.get('scope'),el.get('headers'),el.get('start'),el.get('type'),el.get('value'))
            assert [sig(x) for x in body.select(tag)]==[sig(x) for x in semantic.select(tag)],nid+' structure mismatch '+tag
            structures[tag]=len(body.select(tag))
        refs=[urljoin(url,x['href']) for x in body.select('a[href]')];assert refs==[x['href'] for x in semantic.select('a[href]')],nid+' cross-reference mismatch'
        comparisons.append({'node_id':nid,'printed_number':num,'body_lexical_tokens':len(sourcetokens),'body_token_sha256':sha(json.dumps(sourcetokens,ensure_ascii=False).encode()),'exact_word_boundaries_and_order_equal':True,'structure_counts':structures,'cross_references_preserved_in_semantic_sidecar':len(refs),'images':images})
    return {'slug':r['job']['slug'],'classification':'actual_fresh_standalone_headed_legal_DOM_independently_verified','raw_source_sha256':sha(raw),'raw_bytes':len(raw),'receipt_sha256':sha(receipt_path.read_bytes()),'source_url':url,'identity':identity,'capture_scope':r['capture_selector'],'full_document':r['full_document'],'synthetic_wrapper_added':report['synthetic_wrapper_added'],'acquisition_script_sha256':r['script_sha256'],'records':len(rows),'csv_json_and_publication_equal':True,'counts_reconcile':True,'clean_resumed_provenance_equal':True,'comparisons':comparisons,'whole_corpus_complete':False,'fresh_publisher_export_download_claimed':False,'output_hashes':{str(p.relative_to(out)):sha(p.read_bytes()) for p in folder.rglob('*') if p.is_file()}}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',required=True);p.add_argument('--receipts',required=True,help='JSON list of receipt paths relative to this review directory');p.add_argument('--out',required=True);a=p.parse_args();package=Path(a.package).resolve();out=Path(a.out).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Use new independent review output')
    sys.path.insert(0,str(package));results=[]
    for name in json.loads(Path(a.receipts).read_text()):
        receipt=HERE/name;slug=json.loads(receipt.read_text())['job']['slug'];results.append(audit_source(receipt,package,out/slug))
    report={'publisher_network_calls':0,'source_hashes':{n:sha((package/n).read_bytes()) for n in ['ecode360.py','ingest_standalone.py','source_controls.py','route-registry.json']},'actual_fresh_accepted_sources':len(results),'actual_fresh_records':sum(x['records'] for x in results),'whole_corpus_complete':False,'results':results}
    dump(out/'semantic-review.json',report);print(json.dumps({'actual_fresh_accepted_sources':len(results),'actual_fresh_records':report['actual_fresh_records'],'status':'independent_semantic_review_passed'},indent=2))
if __name__=='__main__':main()
