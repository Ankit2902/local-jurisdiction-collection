"""Source-bound Clark configuration audit, not a native reparse or legal acceptance.

Uses portable documentary witnesses pinned to the sealed full30 proof. Native
originals remain in that proof; no PDF/image extraction or network is performed.
"""
import datetime,hashlib,json,zipfile
from bs4 import BeautifulSoup
ID='96-7e8795b1baee'
KIND='fresh-full30-native-capture-all-page-parse-real-closing-guarded-family-verify'
BUNDLE='clark-title30-source-evidence.zip'
MANIFEST='clark-title30-source-evidence-manifest.json'
SEALED='f138e7116c4552c242c79177fae024b6eb0158617b821c72a8818db539008537'
PEER='6681d51a12377c2395e3f50065f03bd60d34d00441f6d5c7572cbc3be05b0d4d'
CONFIG='a9f72d7a2e9dfad0ac295448de8f4699e7d7ebee18bf71020bebcda9b1345813'
ROUTE='https://www.clarkcountynv.gov/government/departments/comprehensive_planning_department/library/title-30'
HEADER='Title 30 - Effective 9/17/2026'
PATH='collectors/official/configs/clark-title30-current-associated-documents.json'
def sha(data):return hashlib.sha256(data).hexdigest()
def audit(here,catalog):
    errors=[]
    def need(ok,message):
        if not ok:raise ValueError(message)
    try:
        overrides=json.loads((here/'followup-qualified-configs.json').read_text())['publications']
        selected={ident:q for ident,q in overrides.items()if q.get('qualification_evidence',{}).get('kind')==KIND}
        need(set(selected)=={ID},'Exact one Clark source-qualified entry required')
        q=selected[ID];pub=next(p for p in catalog['publications']if p['id']==ID);e=q['qualification_evidence']
        need(pub['target_id']=='96'and pub['publisher']=='official'and pub['source_url']==ROUTE,'Clark publication/government/source binding')
        need(pub['validation_level']=='mapped_only'and not pub.get('full_live_verified'),'Clark base mapping cannot confer live/semantic acceptance')
        need(pub.get('adapter_mode')=='pdf_set'and pub.get('adapter_config_path')==PATH and pub.get('runnable'),'Clark exact official adapter configuration')
        need(pub['expected_identity'].get('client_names')==['Clark County']and pub['expected_identity'].get('state')=='NV'and not pub['expected_identity'].get('publisher_product_id'),'Clark official identity must not borrow a publisher product')
        need(pub['image_policy']['placeholder']=='[IMAGE]'and pub['image_policy']['download_images']is False,'Clark literal no-image policy')
        need(e.get('bundle')==BUNDLE and e.get('source_manifest')==MANIFEST,'Clark source bundle/manifest selection')
        m=json.loads((here/MANIFEST).read_text());archive=(here/BUNDLE).read_bytes()
        need(sha(archive)==m['archive_sha256']==e['source_archive_sha256'],'Clark source archive hash')
        with zipfile.ZipFile(here/BUNDLE)as z:
            entries={r['member']:r for r in m['files']};need(set(z.namelist())==set(entries),'Clark source archive exact entries')
            raw={n:z.read(n)for n in entries}
            for n,b in raw.items():need(len(b)==entries[n]['bytes']and sha(b)==entries[n]['sha256'],'Clark archive witness corrupt: '+n)
        need(sha(raw['full30/MANIFEST.json'])==SEALED==e['manifest_sha256'],'Clark sealed full30 proof identity')
        full=json.loads(raw['full30/MANIFEST.json'])['files']
        def witness(name):
            b=raw['full30/'+name];r=full[name];need(len(b)==r['bytes']and sha(b)==r['sha256'],'Clark sealed source witness differs: '+name);return b
        def obj(name):return json.loads(witness(name))
        need(sha(raw['peer/review.json'])==PEER==e['independent_audit_sha256'],'Clark independent review identity')
        peer=json.loads(raw['peer/review.json']);need(peer['passed']and peer['packet_manifest_sha256']==SEALED and peer['requested_file_pages_complete']and not peer['legal_semantic_coverage_complete']and not peer['jurisdiction_complete'],'Clark independent proof qualification scope')
        config=witness('config.json');need(sha(config)==CONFIG==e['config_sha256'],'Clark tested config fingerprint')
        actual=(here.parents[1]/PATH).read_bytes();need(actual==config,'Clark current config differs from tested source config')
        c=json.loads(config);need(c['source_url']==ROUTE and c['jurisdiction']=='Clark County'and c['state']=='NV'and c['mode']=='pdf_set'and c['coverage_level']=='file_pages','Clark exact government/native-file/page scope')
        need(witness('run/config.json')==config,'Clark producer selected config')
        state=obj('run/checkpoint.json');need(state['completed']and not state['limits_history']and len(state['items'])==len(state['done'])==30 and len(set(state['done']))==30,'Clark entire unbounded selected inventory')
        opening=witness('run/'+state['identity']['source_ref']);closing=witness('run/'+state['consistency']['raw_ref'])
        need(opening==closing and state['consistency']['consistent']and state['identity']['source_currency']==HEADER,'Clark actual later source/currency closure')
        soup=BeautifulSoup(opening,'html.parser');currency=soup.select(c['source_currency_selector']);need(len(currency)==1 and currency[0].get_text(' ',strip=True)==HEADER,'Clark exact unique current source group')
        anchors=soup.select(c['inventory_selector']);inventory=obj('source-inventory.json');ordered=[(a['href'],a.get_text(' ',strip=True))for a in anchors]
        need(len(ordered)==30 and len({u for u,t in ordered})==30 and ordered==[(r['url'],r['label'])for r in inventory['current_documents']],'Clark current30 source-owned ordered inventory')
        need(ordered==[(i['url'],i['heading'])for i in state['items']],'Clark producer inventory vs source anchors')
        legacy=inventory['historical_documents_explicitly_outside_current_group'];need(len(legacy)==66 and not({r['url']for r in legacy}&{u for u,t in ordered}),'Clark legacy66 explicitly excluded')
        def receipt(ref,url,expected_name=None):
            name='run/'+ref.removesuffix('.bin')+'.receipt.json';r=obj(name)
            need(r['status']==200 and not r.get('access_stop')and not r.get('policy_omitted_image')and r['url']==url and r['final_url']==url,'Clark source response identity/refusal: '+name)
            if expected_name:need(r['request_name']==expected_name,'Clark request ownership: '+name)
            body=full['run/'+ref];need(body['sha256']==r['sha256']and body['bytes']==r['bytes'],'Clark retained original body/receipt: '+name)
            return r
        a=receipt(state['identity']['source_ref'],ROUTE,'discovery');b=receipt(state['consistency']['raw_ref'],ROUTE)
        need(datetime.datetime.fromisoformat(b['started_at'])>datetime.datetime.fromisoformat(a['finished_at']),'Clark actual later page response required')
        checks={x['id']:x for x in state['item_consistency']};need(len(checks)==30 and set(checks)==set(state['done']),'Clark all30 later source checks')
        for item in state['items']:
            start=receipt(item['raw_ref'],item['url'],'item:'+item['id']);x=checks[item['id']];end=receipt(x['raw_ref'],item['url'])
            need(x['matches_initial_content']and x['sha256']==start['sha256']==end['sha256'],'Clark native initial/later hash closure')
            need(end['request_name'].startswith('item-end:'+item['id']+':')and datetime.datetime.fromisoformat(end['started_at'])>datetime.datetime.fromisoformat(start['finished_at']),'Clark later native response ownership')
        coverage=obj('run/coverage.json');verification=obj('verify.stdout');status=obj('status.json')
        need(coverage['requested_level']=='file_pages'and coverage['requested_coverage_complete']and coverage['pdf_page_extraction_complete']and coverage['parsed_record_count']==381 and coverage['image_placeholder_count']==229,'Clark measured full file/page coverage')
        need(not coverage['legal_semantic_coverage_complete']and not coverage['jurisdiction_complete']and coverage['manual_review_required'],'Clark semantic gaps remain explicit')
        need(verification['all_run_files_unchanged']and verification['run_file_count']==177 and not verification['forbidden_calls']and status['collection_exit']==0 and not status['image_calls'],'Clark retained guarded family verification')
        for n,h in state['scripts'].items():need(sha(witness('run/executed/'+n))==h,'Clark exact executed source snapshot: '+n)
        need(e['full_file_pages_live_verified']is True and e['full_live_verified']is False and e['legal_semantic_coverage_complete']is False and e['jurisdiction_complete']is False,'Clark configuration evidence must not waive legal/jurisdiction qualification')
    except (OSError,KeyError,ValueError,TypeError,StopIteration,zipfile.BadZipFile)as exc:
        errors.append('Clark Title30 source qualification: '+str(exc))
    return errors
