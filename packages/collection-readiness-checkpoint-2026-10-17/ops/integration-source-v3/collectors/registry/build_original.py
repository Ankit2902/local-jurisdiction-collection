#!/usr/bin/env python3
"""Author original30 extension only from sealed retained source identities."""
import copy,hashlib,json
from pathlib import Path
from urllib.parse import urlparse
from dispatch import ROOT,qualified,Unsupported
HERE=Path(__file__).resolve().parent
MATRIX='packages/local-extraction-e2e-2026-10-15/SOURCE-MATRIX.json'
ECODE='packages/ecode360-headed-2026-10-16/runtime-review/evidence/reviewed-route-registry.json'
def read(p):return json.loads((ROOT/p).read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main():
    rows=read(MATRIX)['jurisdictions'];review={x['slug']:x for x in read(ECODE)}
    expansion=read('collectors/registry/targets.json')['targets'];policy=copy.deepcopy(expansion[0]['primary_publication']['image_policy'])
    targets=[];pubs=[];sources={MATRIX,ECODE};official=[]
    for row in rows:
        tid='original-'+row['slug'];kind=row['current_source_type'];url=row['current_source_url'];family={'ecode360':'ecode','municipal_codes':'ecode','codepublishing':'official','civicplus_pdf':'official','openlaw_xml':'official','king_county_html':'official'}.get(kind,kind)
        identity={'client_names':[row['jurisdiction']],'state':row['state']};selector={};basis=[MATRIX];title='Municipal Code';runnable=kind in ('ecode360','municipal_codes','municode');reason=None
        if kind=='ecode360':
            actual=review[row['slug']];identity.update(customer_id=actual['customer_id'],historical_code_id=actual['code_id']);url='https://ecode360.com/'+actual['customer_id'];basis.append(ECODE)
        if kind=='municipal_codes':selector={'publication_path':urlparse(url).path}
        if kind=='municode':
            base='packages/local-extraction-e2e-2026-10-15/bulk-and-official-html/live/final-daly-city/source/start/'
            client=read(base+'clients.json')[0];book=read(base+'publications.json')['codes'][0];identity.update(publisher_client_id=client['ClientID'],publisher_product_id=book['productId'],publisher_product_name=book['productName'],publisher_publication_id=book['publicationId']);selector={'product_id':book['productId']};title=book['productName'];basis += [base+'clients.json',base+'publications.json'];sources.update(basis)
        if not runnable:reason='Exact whole-publication inventory/content parser configuration is not yet qualified for this original source; historical bounded pass does not qualify current collector'
        pub={'id':tid+'-primary','target_id':tid,'title':title,'observed_title':title if kind=='municode' else None,'source_url':url,'publisher':family,'source_family':'municipal.codes' if kind=='municipal_codes' else kind,'scope_kind':'publication','role':'primary','required_for_jurisdiction':True,'expected_identity':identity,'selector':selector,'publisher_product_id':identity.get('publisher_product_id'),'publisher_publication_id':identity.get('publisher_publication_id'),'runnable':runnable,'unsupported_reason':reason,'validation_level':'mapped_only','full_live_verified':False,'evidence_paths':basis,'image_policy':policy}
        overlaps=[x['id'] for x in expansion if (x['jurisdiction'].casefold(),x['state'])==(row['jurisdiction'].casefold(),row['state'])]
        target={'id':tid,'sequence':None,'cohort':'original','slug':row['slug'],'jurisdiction':row['jurisdiction'],'state':row['state'],'entity_type':'County' if row['slug']=='king-county-wa' else 'City','publisher':family,'source_family':pub['source_family'],'source_url':url,'primary_publication_id':pub['id'],'primary_publication':pub,'expected_identity':identity,'overlap_of':overlaps,'known_publications':row.get('extra_publication_families',[]),'unresolved_required_scope':[{'scope':'Additional independent publications and uncodified amendments','status':'unresolved','reason':'Original bounded inventory does not establish exhaustive jurisdiction coverage'}],'prior_validation':{'kind':'bounded_sample_only','records':row['validated_records'],'evidence':MATRIX,'remaining_gate':row['remaining_gate']},'jurisdiction_complete':False}
        targets.append(target);pubs.append(pub)
        if family=='official':official.append({'target_id':tid,'source_type':kind,'source_url':url,'historical_source_row':row})
        for extra in row.get('extra_publication_families',[]):
            # Accepted retained inventory establishes the exact root, not full content.
            eu=extra['url'].removesuffix('/contents');ep=copy.deepcopy(pub);ep.update(id=tid+'-'+extra['id'],title=extra['id'].removeprefix('family-'),observed_title=None,role='secondary',source_url=eu,selector={'publication_path':urlparse(eu).path},runnable=bool(extra.get('accepted')),unsupported_reason=None if extra.get('accepted') else 'Observed family route was not accepted; access challenge retained, no retry authorized',full_live_verified=False);pubs.append(ep)
    for t in targets:
        try:qualified(t['primary_publication'],t)
        except Unsupported as exc:
            t['primary_publication']['runnable']=False;t['primary_publication']['unsupported_reason']=str(exc)
    write(HERE/'original-targets.json',{'schema_version':1,'scope':'Original30; no full validation inferred from historical samples','targets':targets})
    write(HERE/'original-publications.json',{'schema_version':1,'publications':pubs})
    # A compact portable source bundle is separate from the frozen expansion bundle.
    import zipfile
    manifest=[]
    with zipfile.ZipFile(HERE/'original-source-evidence.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(sources):
            b=(ROOT/path).read_bytes();info=zipfile.ZipInfo(path,date_time=(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b);manifest.append({'path':path,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
    write(HERE/'original-source-evidence-manifest.json',{'files':manifest,'zip_sha256':hashlib.sha256((HERE/'original-source-evidence.zip').read_bytes()).hexdigest()})
    write(HERE/'original-official-needs.json',{'scope':'Exact source inventory needs; no selector guesses','targets':official})
if __name__=='__main__':main()
