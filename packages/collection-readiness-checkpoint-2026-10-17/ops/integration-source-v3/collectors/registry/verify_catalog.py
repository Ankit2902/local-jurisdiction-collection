#!/usr/bin/env python3
"""Read-only union130 audit against original raw source bundles, not prior success flags."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
from urllib.parse import urlsplit
from catalog import load_catalog,HERE
from dispatch import qualified,command,Unsupported
from verify import audit as audit_expansion

def audit(catalog=None):
    cat=catalog or load_catalog();errors=[]
    def check(ok,message):
        if not ok:errors.append(message)
    expansion=audit_expansion();check(expansion['passed'],'Frozen expansion source audit: '+str(expansion['errors']))
    manifest=json.loads((HERE/'original-source-evidence-manifest.json').read_text());archive=HERE/'original-source-evidence.zip';check(hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['zip_sha256'],'Original source archive SHA')
    raw={}
    with zipfile.ZipFile(archive) as z:
        check(set(z.namelist())=={e['path'] for e in manifest['files']},'Original source bundle exact entries')
        for e in manifest['files']:
            b=z.read(e['path']);raw[e['path']]=b;check(len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'],'Corrupt original source '+e['path'])
    matrix=json.loads(raw['packages/local-extraction-e2e-2026-10-15/SOURCE-MATRIX.json'])['jurisdictions'];review=json.loads(raw['packages/ecode360-headed-2026-10-16/runtime-review/evidence/reviewed-route-registry.json']);expected={'original-'+r['slug']:r for r in matrix};customers={r['slug']:r for r in review}
    ts=cat['targets'];ps=cat['publications'];tb={t['id']:t for t in ts};pb={p['id']:p for p in ps};original=[t for t in ts if t['id'].startswith('original-')]
    additional=HERE/'readiness-additional-publications.json'
    if additional.exists():
        am=json.loads((HERE/'readiness-source-evidence-manifest.json').read_text());az=HERE/'readiness-source-evidence.zip';check(hashlib.sha256(az.read_bytes()).hexdigest()==am['archive_sha256'],'New discovery archive SHA')
        with zipfile.ZipFile(az) as z:
            check(set(z.namelist())=={item['member'] for item in am['files']},'New discovery exact archive entries')
            for item in am['files']:check(hashlib.sha256(z.read(item['member'])).hexdigest()==item['sha256'],'New discovery source corrupt '+item['member'])
            for p in json.loads(additional.read_text())['publications']:
                current=pb.get(p['id']);check(current is not None,'Missing qualified new discovery '+p['id'])
                if p['id']=='100-fairfax-public-facilities-manual':
                    cfg=json.loads(z.read('fairfax-pfm/config.json'));toc=z.read('fairfax-pfm/toc.html').decode();witness=z.read('fairfax-pfm/zoning-reference.html').decode();check(p['source_url']==cfg['base'] and p['observed_title']==cfg['identity'] and cfg['identity'] in toc and 'fairfaxcounty-va-pfm' in witness,'PFM source/config/dependency witness mismatch')
            qualifications=HERE/'readiness-qualified-configs.json'
            if qualifications.exists():
                for ident,q in json.loads(qualifications.read_text())['publications'].items():
                    if q['qualification_evidence'].get('kind')=='gridics-native-inventory':
                        prefix=q['qualification_evidence']['prefix'];cfg=json.loads(z.read(prefix+'/config.json'));inv=z.read(prefix+'/inventory.json');receipt=json.loads(z.read(prefix+'/receipt.json'));doc=z.read(prefix+'/document.html');dr=json.loads(z.read(prefix+'/document-receipt.json'));p=pb.get(ident,{})
                        check(hashlib.sha256(inv).hexdigest()==receipt['sha256'] and receipt['status']==200 and hashlib.sha256(doc).hexdigest()==dr['sha256'],'Gridics raw document/inventory binding '+ident)
                        check(receipt['url'].startswith('https://codehub.gridics.com/api/v1/codehub/'+cfg['document_id']+'?') and all(n['docId']==cfg['document_id'] for n in json.loads(inv)) and p.get('source_url')==cfg['source_url'] and p['observed_title'] in doc.decode(),'Gridics exact source/publication identity '+ident)
                        continue
                    prefix=q['qualification_evidence']['prefix'];cfg=json.loads(z.read(prefix+'/config.json'));toc=z.read(prefix+'/toc.html');receipt=json.loads(z.read(prefix+'/receipt.json'));p=pb.get(ident,{})
                    check(receipt['http_status']==200 and not receipt.get('challenge') and hashlib.sha256(toc).hexdigest()==receipt['sha256'],'Qualified TOC transport/source binding '+ident)
                    check(p.get('source_url')==cfg['base'] and p.get('observed_title')==cfg['identity'] and cfg['identity'] in toc.decode() and receipt['final_url'].startswith(cfg['base']),'Qualified config/source identity '+ident)
    check(len(ts)==130 and len(tb)==130,'130 unique targets required');check(set(t['id'] for t in original)==set(expected),'Exact original30 IDs required');check(len(ps)==len(pb),'Duplicate publication IDs');check(len([p for p in ps if p['role']=='primary'])==130,'One primary per130targets')
    for tid,row in expected.items():
        t=tb.get(tid)
        if not t:continue
        for dependency in p.get('required_publication_dependencies',[]):check(dependency in pb and pb[dependency]['target_id']==p['target_id'],'Required publication dependency absent/foreign '+p['id'])
        check((t['jurisdiction'],t['state'],t['slug'])==(row['jurisdiction'],row['state'],row['slug']),'Original government/state mismatch '+tid)
        p=pb.get(t['primary_publication_id']);check(bool(p) and p['target_id']==tid and p['role']=='primary','Original primary ownership '+tid)
        if not p:continue
        check(t['primary_publication']==p,'Original embedded primary drift '+tid)
        check(t['prior_validation']['kind']=='bounded_sample_only' and not t['jurisdiction_complete'],'Original bounded proof promoted '+tid)
        if row['current_source_type']=='ecode360':
            identity=customers[row['slug']];check(p['expected_identity'].get('customer_id')==identity['customer_id'] and p['source_url']=='https://ecode360.com/'+identity['customer_id'],'Original eCode exactcustomer root '+tid)
        else:check(p['source_url']==row['current_source_url'],'Original source route changed without source qualification '+tid)
        if row['current_source_type']=='municode':
            base='packages/local-extraction-e2e-2026-10-15/bulk-and-official-html/live/final-daly-city/source/start/';client=json.loads(raw[base+'clients.json'])[0];books=json.loads(raw[base+'publications.json'])['codes'];check(p['expected_identity'].get('publisher_client_id')==client['ClientID'] and any(b['productId']==p['publisher_product_id'] for b in books),'Original Municode client/product raw binding '+tid)
    for p in ps:
        t=tb.get(p['target_id']);check(t is not None,'Orphan '+p['id'])
        if not t:continue
        check(not p.get('full_live_verified') and p.get('validation_level')=='mapped_only','Base config cannot confer live proof '+p['id'])
        check(not p.get('image_policy',{}).get('download_images',True),'Image policy absent '+p['id'])
        if p['runnable']:
            try:
                plan=command(p,t,'{OUT}');check(not plan['jurisdiction_complete'],'Jurisdiction falsely complete '+p['id'])
                q=qualified(p,t)
                if p['publisher']=='official':check(q['config']['source_url'].rstrip('/')==p['source_url'].rstrip('/'),'Current official config silently changes original source '+p['id'])
            except Exception as exc:errors.append('Undispatchable declared runnable '+p['id']+': '+str(exc))
        else:check(bool(p.get('unsupported_reason')),'Unsupported without reason '+p['id'])
        if p['publisher']=='american-legal' and p['runnable']:
            proof=p.get('strategy_evidence',{});check(bool(proof),'Explicit observed AL strategy required '+p['id'])
            if proof:
                with zipfile.ZipFile(HERE/proof['bundle']) as z:s=z.read(proof['member']).decode()
                m=re.search(r'window\._redux_state\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")',s);codes=json.loads(json.loads(m[1]))['codes'];books=codes['selectedVersion']['toc'];selected=[b for b in books if b['slug']==p['selector']['publication'] and b['client_slug']==urlsplit(p['source_url']).path.split('/')[2]]
                check(len(selected)==1,'Observed AL selector binding '+p['id'])
                if selected:check(p['observed_is_pdf']==selected[0]['is_pdf'] and p['acquisition_strategy']==('traverse' if selected[0]['is_pdf'] else 'native'),'Observed AL type/strategy mismatch '+p['id'])
        if p['id'].startswith('original-') and p['role']=='secondary':
            ref=next((x for x in expected[p['target_id']].get('extra_publication_families',[]) if p['source_url']==x['url'].removesuffix('/contents')),None);check(ref is not None,'Invented original secondary root '+p['id']);check(bool(ref and ref.get('accepted'))==p['runnable'],'Unaccepted original family declared runnable '+p['id'])
    return {'schema_version':1,'network_requests_sent':0,'read_only':True,'passed':not errors,'errors':errors,'targets':len(ts),'publications':len(ps),'dispatchable':sum(p['runnable'] for p in ps),'original_targets':len(original),'original_full_live_proofs_inferred':0}
if __name__=='__main__':
    result=audit();print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 2)
