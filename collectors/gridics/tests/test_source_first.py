"""Actual full Education root + fail-closed native-only reconciliation; zero network."""
import copy,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from collectors.gridics import model, collect
from collectors.gridics.publisher import section_renderability

FIX=Path(__file__).resolve().parents[1]/'fixtures'
TREE=json.loads((FIX/'miami-unrenderable-education.json').read_text())
ROOT=TREE[0]['path']
CFG={'source_url':'https://codehub.gridics.com/us/fl/miami-comp#'+ROOT,'document_id':'94','identity_term':'Miami','jurisdiction':'Miami','state':'FL'}


class SourceFirstTests(unittest.TestCase):
    def test_actual_complete_root_preserves_every_owner_id_and_body(self):
        self.assertEqual(model.digest((FIX/'miami-unrenderable-education.json').read_bytes()),'fc3250022046ba435c6bf0e7b74dae549d711bcc4b32b3d9b3f7919d1e08d7d1')
        records,counts=model.native_records(copy.deepcopy(TREE),CFG,ROOT)
        self.assertEqual(counts,{'native_node_count':104,'body_block_count':52})
        self.assertEqual(len(records),52)
        self.assertTrue(all(r['heading']=='' and r['disposition']=='source_unqualified' for r in records))
        source={}
        def walk(n):
            source[n['id']]=n
            for c in n.get('children',[]):walk(c)
        walk(TREE[0])
        owned={r['source_id'] for r in records}
        blocks={b for r in records for b in r['body_block_ids']}
        self.assertEqual(owned|blocks,set(source))
        self.assertFalse(owned&blocks)
        self.assertEqual(sum(bool(r['text']) for r in records),51)
        self.assertEqual(sum(len(r['tables']) for r in records),1)
        self.assertEqual(sum(len(row) for r in records for t in r['tables'] for row in t),10)
        self.assertIn('Section 163.3191', '\n'.join(r['text'] for r in records))
        self.assertIn('Objective EDU-1.2', '\n'.join(r['text'] for r in records))
        for r in records:
            n=source[r['source_id']]
            self.assertEqual(r['source_sequence'],[c['id'] for c in n.get('children',[])])
            self.assertEqual(r['source_body_sha256'],model.digest(''.join(source[b]['text'] for b in r['body_block_ids']).encode()))

    def test_actual_root_cannot_supply_a_rendered_section(self):
        disposition=section_renderability(TREE[0])
        self.assertFalse(disposition['eligible'])
        self.assertIn('Source heading text is missing or empty',disposition['reasons'])

    def test_source_bound_public_url_and_no_guessed_path(self):
        url=collect.native_tree_url(CFG['source_url'],'94',TREE[0],'8626')
        self.assertEqual(url,'https://codehub.gridics.com/api/v1/codehub/94?tree=1&_format=json&pathes%5B%5D=506df571-d1e3-4692-bfb3-816db47b916c&revision=8626')
        for args in [('https://example.invalid','94',TREE[0],'8626'),(CFG['source_url'],'95',TREE[0],'8626'),(CFG['source_url'],'94',dict(TREE[0],path='/guessed'),'8626'),(CFG['source_url'],'94',TREE[0],'')]:
            with self.assertRaises(model.Invalid):collect.native_tree_url(*args)

    def test_unknown_own_text_is_retained_and_never_promoted_to_heading(self):
        root=copy.deepcopy(TREE[0]);root['li_attr']={};root['text']='<p>Unclassified operative citation § 2.1.</p>';root['children']=[]
        records,_=model.native_records([root],CFG,ROOT)
        self.assertEqual(records[0]['heading'],'')
        self.assertEqual(records[0]['text'],'Unclassified operative citation § 2.1.')
        self.assertEqual(records[0]['disposition'],'source_unqualified')

    def test_nonstring_original_own_text_hash_never_collapses(self):
        root=copy.deepcopy(TREE[0]);root['children']=[];root['text']={'unrecognized':'alpha'}
        first=model.native_records([root],CFG,ROOT)[0][0]
        root['text']={'unrecognized':'beta'}
        second=model.native_records([root],CFG,ROOT)[0][0]
        self.assertNotEqual(first['source_original_text_sha256'],second['source_original_text_sha256'])
        self.assertEqual(first['heading'],'');self.assertEqual(first['disposition'],'source_unqualified')

    def test_body_at_root_keeps_source_id_without_fabricating_heading(self):
        root=copy.deepcopy(TREE[0]);root['children']=[];root['li_attr']={'dataTag':'BodyM'};root['text']='<p>Body at unusual root.</p>'
        records,counts=model.native_records([root],CFG,ROOT)
        self.assertEqual(len(records),1);self.assertEqual(records[0]['source_id'],root['id'])
        self.assertEqual(records[0]['heading'],'');self.assertEqual(records[0]['text'],'Body at unusual root.')
        self.assertEqual(records[0]['disposition'],'source_unqualified')

    def test_malformed_attribute_types_are_preserved_by_hash_without_payload(self):
        root=copy.deepcopy(TREE[0]);root['children']=root['children'][:1];root['children'][0]['text']='<p>Retained operative body.</p>'
        root['li_attr']={'tag':{'image':'data:image/png;base64,ATTRIBUTE_SECRET'},'dataTag':['data:image/png;base64,ATTRIBUTE_SECRET']}
        records,_=model.native_records([root],CFG,ROOT)
        self.assertEqual(records[0]['source_id'],root['id']);self.assertEqual(records[0]['text'],'Retained operative body.')
        self.assertEqual(records[0]['heading'],'');self.assertFalse(section_renderability(root)['eligible'])
        self.assertEqual(records[0]['heading_tag']['unrecognized_source_type'],'dict')
        self.assertEqual(records[0]['source_data_tag']['unrecognized_source_type'],'list')
        self.assertNotIn('ATTRIBUTE_SECRET',json.dumps(records))

    def test_new_unknown_and_image_node_paths_remove_payload(self):
        root=copy.deepcopy(TREE[0]);root['children']=root['children'][:1]
        child=root['children'][0];child['text']='<table><tr><td background="map.png">Caption<img src="data:image/png;base64,PIXEL_SECRET"></td></tr></table>'
        records,_=model.native_records([root],CFG,ROOT)
        serialized=json.dumps(records)
        self.assertNotIn('PIXEL_SECRET',serialized)
        self.assertNotIn('<img',serialized)
        self.assertEqual(records[0]['text'].count('[IMAGE]'),2)
        self.assertIn('[IMAGE]Caption[IMAGE]',records[0]['tables'][0][0][0]['text'])
        child['li_attr']['dataTag']='BodyImage';child['text']='DATA:IMAGE/PNG;base64,PIXEL_SECRET'
        records,_=model.native_records([root],CFG,ROOT)
        self.assertEqual(records[0]['text'],'[IMAGE]');self.assertNotIn('PIXEL_SECRET',json.dumps(records))
        root['children']=[];root['li_attr']={};root['text']='data:image/png;base64,PIXEL_SECRET'
        records,_=model.native_records([root],CFG,ROOT)
        self.assertEqual(records[0]['text'],'[IMAGE]');self.assertNotIn('PIXEL_SECRET',json.dumps(records))

    def fixture(self,folder,full_inventory=False):
        """Synthetic two-phase envelope of actual one-root source, not live proof."""
        root=copy.deepcopy(TREE[0]);root.pop('children');ledger=[]
        inventory=json.loads((FIX/'miami-comp-root-inventory.json').read_text()) if full_inventory else [root]
        for phase,minute in [('start','00'),('end','10')]:
            def response(name,raw,query):
                path=phase+'-'+name+'.json';(folder/path).write_bytes(raw)
                rr={'path':path,'sha256':model.digest(raw),'bytes':len(raw),'status':200,'content_type':'application/json','url':'https://codehub.gridics.com/api/v1/codehub/94?'+query+'&revision=8626','phase':phase,'epoch':phase,'at':'2026-10-17T00:'+minute+':00+00:00'};ledger.append(rr);return rr
            inv=response('inventory',json.dumps(inventory).encode(),'topLevel=1')
            tree=response('tree',(FIX/'miami-unrenderable-education.json').read_bytes(),'tree=1&pathes%5B%5D='+root['id'])
            with zipfile.ZipFile(FIX/'miami-renderer.zip') as z:
                raw=z.read('publisher-renderer.js')
            client_name=phase+'-renderer.js';(folder/client_name).write_bytes(raw)
            ledger.append({'path':client_name,'sha256':model.digest(raw),'bytes':len(raw),'status':200,'content_type':'application/javascript','url':'https://codehub.gridics.com/build/static/js/Doc.fac920ca.chunk.js','phase':phase,'epoch':phase,'at':'2026-10-17T00:'+minute+':00+00:00'})
            diagnostic=phase+'-diagnostic.html';(folder/diagnostic).write_text('<html><title>Miami</title><body>Public app, no section for this root.</body></html>')
            row={'root':root,'url':CFG['source_url'],'tree_response':tree,'dom_path':None,'dom_sha256':None,'render_status':'source_unrenderable','render_diagnostic':{'reason':'Source fields unavailable'},'renderability':section_renderability(root),'diagnostic_dom_path':diagnostic,'diagnostic_dom_sha256':model.digest((folder/diagnostic).read_bytes())}
            model.save(folder/(phase+'-checkpoint.json'),{'phase':phase,'phase_complete':True,'roots_response':inv,'roots':[row]})
        model.save(folder/'responses.json',ledger)

    def test_actual_native_only_full_root_not_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp);self.fixture(f);records,refs,c=model.analyze(f,CFG)
            self.assertEqual(len(records),52)
            self.assertTrue(c['native_source_complete'])
            self.assertFalse(c['complete']);self.assertFalse(c['publication_text_complete'])
            self.assertFalse(c['source_qualification_complete']);self.assertFalse(c['rendered_publication_qa_complete'])
            self.assertEqual(len(c['unqualified_source_ids']),52);self.assertEqual(len(c['native_only_roots']),2)

    def test_original49_root_inventory_never_dropped_to_visible_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp);self.fixture(f,full_inventory=True)
            with self.assertRaisesRegex(model.Invalid,'does not exhaust'):model.analyze(f,CFG)

    def test_missing_native_or_wrong_root_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp);self.fixture(f);(f/'start-tree.json').unlink()
            with self.assertRaises((FileNotFoundError,model.Invalid)):model.analyze(f,CFG)
        with self.assertRaisesRegex(model.Invalid,'root mismatch'):model.native_records(TREE,CFG,'/wrong')

    def test_no_fabricated_native_only_exemption(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp);self.fixture(f);cp=model.read(f/'start-checkpoint.json');cp['roots'][0]['render_diagnostic']={};model.save(f/'start-checkpoint.json',cp)
            with self.assertRaisesRegex(model.Invalid,'Malformed native-only'):model.analyze(f,CFG)

    def test_source_unrenderable_requires_actual_exact_publisher_client(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp);self.fixture(f);model.save(f/'responses.json',[r for r in model.read(f/'responses.json') if not r['path'].endswith('renderer.js')])
            with self.assertRaisesRegex(model.Invalid,'requires exact same-phase'):model.analyze(f,CFG)

    def test_source_root_metadata_cannot_be_rewritten_to_skip_dom(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp);self.fixture(f);cp=model.read(f/'start-checkpoint.json');cp['roots'][0]['root']['pos']='invented';model.save(f/'start-checkpoint.json',cp)
            with self.assertRaisesRegex(model.Invalid,'descriptor changed'):model.analyze(f,CFG)

    def test_raw_native_metadata_change_detected_even_when_text_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp);self.fixture(f);tree=model.read(f/'end-tree.json');tree[0]['children'][0]['unrecognized_source_metadata']='changed';raw=json.dumps(tree).encode();(f/'end-tree.json').write_bytes(raw)
            cp=model.read(f/'end-checkpoint.json');receipt=cp['roots'][0]['tree_response'];receipt.update(bytes=len(raw),sha256=model.digest(raw));model.save(f/'end-checkpoint.json',cp)
            ledger=model.read(f/'responses.json')
            for r in ledger:
                if r['path']==receipt['path']:r.update(receipt)
            model.save(f/'responses.json',ledger)
            coverage=model.analyze(f,CFG)[2]
            self.assertTrue(coverage['native_inventory_capture_complete'])
            self.assertFalse(coverage['raw_native_start_end_consistent']);self.assertFalse(coverage['native_source_complete']);self.assertFalse(coverage['complete'])

    def test_known_stop_before_browser_import_or_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp);destination=f/'must-not-exist';missing=f/'package/collectors/gridics'
            with patch.object(collect,'HERE',missing):
                with self.assertRaisesRegex(model.Invalid,'known Gridics PDF HEAD 403 stop remains'):collect.acquire(destination,CFG,False)
            self.assertFalse(destination.exists())

    def test_published_stop_even_with_fresh_gate_no_browser_import(self):
        import builtins
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp);here=f/'collectors/gridics';here.mkdir(parents=True)
            model.save(f/'collectors/registry/access-advisories.json',{'schema_version':1,'advisories':[{'family':'gridics','operator_review_required':True}]})
            original=builtins.__import__
            def tripwire(name,*args,**kwargs):
                if name.startswith('playwright'):
                    raise AssertionError('Browser import reached despite published stop')
                return original(name,*args,**kwargs)
            with patch.object(collect,'HERE',here),patch.object(collect,'GATE',f/'fresh-gate'),patch('builtins.__import__',tripwire):
                with self.assertRaisesRegex(model.Invalid,'Published Gridics workflow access stop'):collect.acquire(f/'out',CFG,False)
            self.assertFalse((f/'out').exists());self.assertFalse((f/'fresh-gate').exists())

    def test_http_failure_not_accepted_as_native_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp);self.fixture(f);cp=model.read(f/'start-checkpoint.json');receipt=cp['roots'][0]['tree_response'];receipt['status']=403
            model.save(f/'start-checkpoint.json',cp)
            ledger=model.read(f/'responses.json')
            for r in ledger:
                if r['path']==receipt['path']:r['status']=403
            model.save(f/'responses.json',ledger)
            with self.assertRaisesRegex(model.Invalid,'not HTTP 200'):model.analyze(f,CFG)


if __name__=='__main__':unittest.main(verbosity=2)
