"""Source-sensitive synthetic IR/receipt fixtures; no live acquisition claims."""
import ast,copy,json,os,shutil,socket,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from common import *
import package
from flagstaff import ROOT

def fixture(base):
    root=base/'input';root.mkdir()
    def save(n,d):
        p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encoded(d))
    cfg={'schema_version':1,'target_id':'original-flagstaff-az','profile':'flagstaff_html','jurisdiction':'Flagstaff','state':'AZ','source_url':ROOT,'publication':'City Code including Charter','required_formats':['html']}
    url=ROOT+'html/source-fixture.html';stamp='2026-10-15T01:02:03+00:00'
    htmls=['<h1 class="Title">Source heading</h1><p>Unnumbered parent text, including “quotes” and\nline breaks.\u2028Literal line separator.\u0085Literal next line.</p>','<h3 class="Cite" id="1"><a name="1">1</a> Duplicate</h3><ol><li>A<ol type="a"><li>Nested enumeration</li></ol></li></ol><p>Legal note<sup>1</sup></p><aside role="note">Footnote body [IMAGE]</aside>','<h3 class="Cite" id="1"><a name="1">1</a> Duplicate</h3><table><tr><th rowspan="2">Header</th><th colspan="2">Schedule</th></tr><tr><td>[IMAGE]</td><td>Exact legal cell</td></tr></table>','<p>Unnumbered operative body with no source heading.</p>']
    original=('<main>'+''.join(htmls)+'</main>').encode();(root/'source/raw').mkdir(parents=True);(root/'source/raw/body.bin').write_bytes(original);(root/'source/raw/toc.bin').write_bytes(b'<nav>Source-sensitive synthetic TOC fixture</nav>')
    rows=[]
    for i,h in enumerate(htmls):
        rows.append({'record_id':'stable-'+str(i),'source_url':url+'#heading-'+str(i),'source_sha256':sha(original),'source_heading_level':'h1' if i==0 else 'h3' if i<3 else None,'source_heading_classes':['Title'] if i==0 else ['Cite'] if i<3 else [],'source_heading_ids':['heading-'+str(i)] if i<3 else [],'source_child_section_ids':[],'heading':'Source heading' if i==0 else '1 Duplicate' if i<3 else 'Source introduction','kind':'container' if i==0 else 'section' if i<3 else 'source_introduction','jurisdiction':'Flagstaff, AZ','semantic_html':h,'full_text':'Original plain convenience text is not used to flatten canonical HTML','tables':[],'notes':[],'block_indices':[i],'image_placeholder_count':h.count('[IMAGE]')})
    # Correct canonical structure must win; bad legacy detector text remains only in rich evidence.
    rows[2]['canonical_structure_selection']={'profile':'synthetic-canonical-fixture'}
    rows[2]['superseded_detector_diagnostics']={'original_record_fields':{'text':'BAD_OLD_GRID','tables':[{'text':'BAD_OLD_GRID'}]}}
    inv=[{'edge_id':'edge-'+str(i),'root_index':0,'source_order':i,'source_url':url+'#heading-'+str(i),'label':rows[i]['heading'],'source_id':'heading-'+str(i),'ancestor_classes':['heading-0']+(['heading-'+str(i)] if i else [])} for i in range(3)]
    toc_url=ROOT+'cgi/fixture-toc';raws=[{'role':'content','source_url':url,'final_url':url,'status':200,'headers':{'content-type':'text/html'},'started_at':stamp,'finished_at':stamp,'path':'raw/body.bin','sha256':sha(original)},{'role':'toc-start','source_url':toc_url,'final_url':toc_url,'status':200,'headers':{'content-type':'text/html'},'started_at':stamp,'finished_at':stamp,'path':'raw/toc.bin','sha256':sha((root/'source/raw/toc.bin').read_bytes())}]
    source={'schema':'flagstaff-full-html-1','source_url':ROOT,'started_at':stamp,'finished_at':stamp,'images_downloaded':False,'artifacts':raws,'inventory':inv,'observed_readers':[{'url':toc_url,'root':{'label':'Source heading'}}]};save('source/checkpoint.json',source)
    parser=b'# synthetic parser witness, never executed\n';(root/'normalized/executed-normalization').mkdir(parents=True);(root/'normalized/executed-normalization/fixture.py').write_bytes(parser);fingerprint={'fixture.py':sha(parser)}
    summary={'records':4,'opening_currency':'Literal source currency fixture, not parsed as legal date','closing_currency':'Literal source currency fixture, not parsed as legal date','code_fingerprint':fingerprint}
    cov={'config':cfg,'formats':{'html':{'summary':summary}},'publication_text_complete':True,'attachments_complete':True,'source_consistency_complete':False,'publication_accepted':False,'complete':False,'whole_jurisdiction_complete':False,'external_adopted_legal_dependency_closure_complete':False,'independent_final_review_complete':False,'errors':['Synthetic retained unresolved reference']}
    save('checkpoint.json',{'config':cfg});save('collection-start.json',{'publication_config':cfg});save('coverage.json',cov);save('normalized/summary.json',summary);save('normalized/executed-normalization.json',fingerprint);save('normalized/source-inventory.json',inv);save('normalized/source-link-defects.json',[{'url':'https://example.invalid/missing','correction_applied':False}]);save('normalized/document-audits.json',[{'url':url,'source_blocks':4,'missing_toc_edges':[],'extra_body_headings':[],'heading_only_unresolved':[],'mapping':[{'edge_id':'edge-'+str(i),'record_id':rows[i]['record_id']} for i in range(3)]}]);(root/'normalized/records.jsonl').write_bytes(jsonl(rows))
    verified=copy.deepcopy(cov);verified.update(full_raw_replay_equal=True,input_files_modified=False,source_route_ledger_verified=True,opening_body_closing_chronology_verified=True,publication_config=cfg);verified['formats']['html']['summary']['source_checkpoint_sha256']=file_hash(root/'source/checkpoint.json')
    family=base/'family.json';family.write_bytes(encoded(verified));hashes=files(root);proof={'fixture_status':'Synthetic source-sensitive IR/receipt fixture, not actual verification or acquisition','evidence_read_only':True,'publisher_requests':0,'source_changed_during_run':False,'runtime_changed_during_run':False,'evidence_sha256_before':hashes,'evidence_sha256_after':hashes,'collector_sources_before':{'fixture':'stable'},'collector_sources_after':{'fixture':'stable'},'publication_id':'original-flagstaff-az-primary','selected_config':cfg};pp=base/'proof.json';pp.write_bytes(encoded(proof));return root,pp,family

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.root,self.proof,self.family=fixture(self.base);self.out=self.base/'output'
    def tearDown(self):self.temp.cleanup()
    def runpack(self,**kw):return package.run(self.root,self.proof,self.family,self.out,'originals-flagstaff-html-v1',**kw)
    def test_exact16_bom_envelope_toc_duplicate_unnumbered_and_fidelity(self):
        self.assertFalse(self.runpack()['complete']);rows=load(self.out/'aggregate-fulltext.json')['provisions'];toc=load(self.out/'aggregate-toc.json')['provisions']
        self.assertEqual(list(rows[0]),FIELDS);self.assertEqual(rows[1]['citation'],rows[2]['citation']);self.assertEqual(rows[3]['citation'],'');self.assertEqual(rows[3]['section_number'],'');self.assertEqual(rows[0]['scrape_date'],'2026-10-15T01:02:03+00:00');self.assertTrue((self.out/'aggregate-fulltext.csv').read_bytes().startswith(b'\xef\xbb\xbf'))
        self.assertIn('<ol type="a">',rows[1]['full_text']);self.assertIn('<sup>1</sup>',rows[1]['full_text']);self.assertIn('Footnote body [IMAGE]',rows[1]['full_text']);self.assertIn('rowspan="2"',rows[2]['full_text']);self.assertIn('colspan="2"',rows[2]['full_text']);self.assertEqual([dict(r,full_text='') for r in rows],toc)
        self.assertNotIn('BAD_OLD_GRID',json.dumps(rows));self.assertIn(b'BAD_OLD_GRID',(self.out/'evidence/input/normalized/records.jsonl').read_bytes());self.assertEqual(load(self.out/'inherited-coverage.json'),load(self.root/'coverage.json'))
    def test_readonly_relocated_verify_and_no_io_apis(self):
        self.runpack();moved=self.base/'relocated';shutil.copytree(self.out,moved);before=files(moved)
        with patch.object(socket,'socket',side_effect=AssertionError('Network forbidden')):
            self.assertTrue(package.verify(moved)['package_verified'])
        self.assertEqual(before,files(moved))
    def test_interrupted_resume_byte_equivalence_and_finished_readonly(self):
        with self.assertRaises(package.InterruptedPackage):self.runpack(interrupt_after=4)
        self.runpack(resume=True);fresh=self.base/'fresh';package.run(self.root,self.proof,self.family,fresh,'originals-flagstaff-html-v1');self.assertEqual(files(self.out),files(fresh));before=files(self.out);self.runpack(resume=True);self.assertEqual(before,files(self.out))
    def test_fresh_unowned_and_unrelated_output_refused(self):
        self.out.mkdir();(self.out/'unrelated').write_text('Do not touch');
        with self.assertRaisesRegex(ValueError,'Fresh unpopulated'):self.runpack()
        self.assertEqual((self.out/'unrelated').read_text(),'Do not touch')
    def test_source_corruption_and_duplicate_ir_refused(self):
        (self.root/'source/raw/body.bin').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'Input differs'):self.runpack()
    def test_output_csv_corruption_even_after_manifest_rehash_refused(self):
        self.runpack();p=self.out/'aggregate-fulltext.csv';p.write_bytes(p.read_bytes().replace(b'Exact legal cell',b'Wrong legal cell'));m=load(self.out/'run-manifest.json');m['artifact_hashes']['aggregate-fulltext.csv']=file_hash(p);(self.out/'run-manifest.json').write_bytes(encoded(m))
        with self.assertRaisesRegex(ValueError,'Corpus projection differs'):package.verify(self.out)
    def test_missing_duplicate_disposition_and_wrong_version_refused(self):
        p=package.reader('originals-flagstaff-html-v1')(self.root,load(self.proof),load(self.family));p.dispositions.append(p.dispositions[0])
        with self.assertRaisesRegex(ValueError,'disposition'):artifacts(p)
        d=load(self.family);d['publication_config']['publication']='Wrong edition';self.family.write_bytes(encoded(d))
        with self.assertRaisesRegex(ValueError,'config'):self.runpack()
    def test_resume_changed_input_and_corrupt_committed_bytes_refused(self):
        with self.assertRaises(package.InterruptedPackage):self.runpack(interrupt_after=2)
        first=next(iter(load(self.out/'package-state.json')['artifacts']));safe(self.out,first).write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'Corrupt committed'):self.runpack(resume=True)
    def test_image_rule_literal_and_active_payload_refusal(self):
        p=package.reader('originals-flagstaff-html-v1')(self.root,load(self.proof),load(self.family))
        self.assertEqual(sum(r['full_text'].count('[IMAGE]') for r in p.rows),2)
        for html in ['<img src="https://example.invalid/image.png">','<svg><text>Forbidden graphic payload</text></svg>','<p style="background:url(image.png)">caption</p>','<span data-source="DATA:IMAGE/SVG+XML,payload">Caption</span>','<object type="IMAGE/PNG" data="opaque"></object>']:
            q=copy.deepcopy(p);q.rows[0]['full_text']=html;q.provenance[0]['corpus_row_sha256']=sha(canonical(q.rows[0]));
            with self.subTest(html=html),self.assertRaises(ValueError):artifacts(q)
    def test_separate_image_file_never_copied(self):
        (self.root/'forbidden.PNG').write_text('not pixels');proof=load(self.proof);proof['evidence_sha256_before']=proof['evidence_sha256_after']=files(self.root);self.proof.write_bytes(encoded(proof))
        with self.assertRaisesRegex(ValueError,'Separate image'):self.runpack()
        self.assertFalse(self.out.exists())
    def test_block_ownership_fault_even_with_rehashed_input_refused(self):
        p=self.root/'normalized/records.jsonl';rows=[json.loads(l) for l in p.read_text().split('\n') if l];rows[1]['block_indices']=[0];p.write_bytes(jsonl(rows));proof=load(self.proof);proof['evidence_sha256_before']=proof['evidence_sha256_after']=files(self.root);self.proof.write_bytes(encoded(proof))
        with self.assertRaisesRegex(ValueError,'source blocks'):self.runpack()
    def test_unsafe_path_unsupported_reader_and_symlink_refused(self):
        with self.assertRaises(ValueError):safe(self.root,'../escape')
        with self.assertRaisesRegex(ValueError,'Unsupported reader'):package.reader('speculative-pdf-sections')
        (self.root/'linked').symlink_to(self.root/'coverage.json')
        with self.assertRaisesRegex(ValueError,'Symlink'):self.runpack()
    def test_wrong_replay_proof_and_unknown_source_epoch_refused(self):
        original=load(self.family)
        for field,value in [('full_raw_replay_equal',False),('source_route_ledger_verified',False),('input_files_modified',True)]:
            d=copy.deepcopy(original);d[field]=value;self.family.write_bytes(encoded(d))
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'replay proof'):self.runpack()
        d=copy.deepcopy(original);d['formats']['html']['summary']['source_checkpoint_sha256']='0'*64;self.family.write_bytes(encoded(d))
        with self.assertRaisesRegex(ValueError,'checkpoint'):self.runpack()
    def test_resume_source_drift_refused_even_with_new_input_hash_manifest(self):
        with self.assertRaises(package.InterruptedPackage):self.runpack(interrupt_after=1)
        p=self.root/'normalized/source-link-defects.json';p.write_bytes(encoded([{'changed':True}]))
        proof=load(self.proof);proof['evidence_sha256_before']=proof['evidence_sha256_after']=files(self.root);self.proof.write_bytes(encoded(proof))
        with self.assertRaisesRegex(ValueError,'Resume input'):self.runpack(resume=True)
    def test_actual_source_sensitive_fixture_projection(self):
        base=Path(__file__).parent/'fixtures';d=load(base/'actual-selected.json');cases={c['case']:c for c in d['cases']}
        self.assertEqual(len(cases),7)
        for c in cases.values():
            r,row=c['ir_record'],c['corpus_row'];self.assertEqual(file_hash(safe(base,c['raw_artifact'])),c['raw_sha256']);self.assertEqual(r['source_sha256'],c['raw_sha256']);self.assertEqual(row['full_text'],r['semantic_html']);self.assertEqual(row['full_text'].count('[IMAGE]'),r['image_placeholder_count']);check_html(row['full_text'])
        a,b=cases['duplicate_printed_heading'],cases['duplicate_printed_heading_second_occurrence'];self.assertEqual(a['corpus_row']['citation'],b['corpus_row']['citation']);self.assertNotEqual(a['ir_record']['record_id'],b['ir_record']['record_id']);self.assertEqual(cases['unnumbered_body']['corpus_row']['citation'],'')
        self.assertIn('<table',cases['table']['corpus_row']['full_text']);self.assertTrue(cases['source_list_wrapper']['ir_record']['source_list_groups']);self.assertTrue(cases['notes']['ir_record']['notes']);self.assertIn('[IMAGE]',cases['image']['corpus_row']['full_text'])
    def test_no_network_image_pdf_execution_dependencies(self):
        forbidden={'requests','http','urllib.request','subprocess','PIL','pypdf','pdfplumber','pypdfium2','fitz','playwright'}
        for name in package.MODULES:
            tree=ast.parse((Path(__file__).parent/name).read_text());imports=[]
            for n in ast.walk(tree):
                if isinstance(n,ast.Import):imports.extend(a.name for a in n.names)
                elif isinstance(n,ast.ImportFrom):imports.append(n.module or '')
            self.assertFalse(forbidden.intersection(imports),(name,imports))
    def test_unknown_checkpoint_phase_and_nonpositive_boundary_refused(self):
        with self.assertRaisesRegex(ValueError,'positive'):self.runpack(interrupt_after=0)
        with self.assertRaises(package.InterruptedPackage):self.runpack(interrupt_after=1)
        p=self.out/'package-state.json';d=load(p);d['phase']='foreign';p.write_bytes(encoded(d))
        with self.assertRaisesRegex(ValueError,'checkpoint'):self.runpack(resume=True)
    def test_rehashed_unrelated_artifact_cannot_enter_verified_package(self):
        self.runpack();(self.out/'unrelated.txt').write_text('must not be adopted')
        state=load(self.out/'package-state.json');state['artifacts']['unrelated.txt']=file_hash(self.out/'unrelated.txt');(self.out/'package-state.json').write_bytes(encoded(state))
        manifest=load(self.out/'run-manifest.json');manifest['artifact_hashes']['unrelated.txt']=file_hash(self.out/'unrelated.txt');manifest['artifact_hashes']['package-state.json']=file_hash(self.out/'package-state.json');(self.out/'run-manifest.json').write_bytes(encoded(manifest))
        with self.assertRaisesRegex(ValueError,'artifact inventory'):package.verify(self.out)
    def test_shipped_cli_with_and_without_B_writes_no_bytecode(self):
        self.runpack();environment=dict(os.environ)
        environment.pop('PYTHONDONTWRITEBYTECODE',None);environment.pop('PYTHONPYCACHEPREFIX',None)
        for flag in [[],['-B']]:
            target=self.base/('ordinary' if not flag else 'no-bytecode');shutil.copytree(self.out,target);before=files(target)
            with self.subTest(flag=flag):
                result=subprocess.run([sys.executable,*flag,str(target/'packager-source/package.py'),'verify','--out',str(target)],cwd=self.base,env=environment,capture_output=True,text=True)
                self.assertEqual(result.returncode,2,(result.stdout,result.stderr));self.assertTrue(json.loads(result.stdout)['package_verified']);self.assertEqual(files(target),before);self.assertFalse(list(target.rglob('__pycache__')))

    def repin(self):
        proof=load(self.proof);proof['evidence_sha256_before']=proof['evidence_sha256_after']=files(self.root);self.proof.write_bytes(encoded(proof))
    def test_physical_LF_jsonl_preserves_unicode_legal_separators(self):
        self.runpack();rows=load(self.out/'aggregate-fulltext.json')['provisions']
        self.assertIn('\u2028Literal line separator.\u0085Literal next line.',rows[0]['full_text']);self.assertTrue(package.verify(self.out)['package_verified'])
    def test_publisher_hierarchy_and_displayed_locator(self):
        self.runpack();rows=load(self.out/'aggregate-fulltext.json')['provisions'];nodes=[json.loads(l) for l in (self.out/'source-nodes.jsonl').read_text().split('\n') if l]
        self.assertEqual(rows[1]['title'],'Source heading');self.assertEqual(rows[1]['section_number'],'1');self.assertEqual(rows[1]['section_name'],'Duplicate');self.assertEqual(nodes[1]['parent_node_id'],nodes[0]['node_id']);self.assertNotEqual(nodes[1]['node_id'],nodes[2]['node_id'])
    def test_rehashed_reader_active_image_and_metadata_faults_refused(self):
        source=self.root/'normalized/records.jsonl';original=source.read_bytes()
        for html in ['<input TYPE="IMAGE" src="opaque">','<object data="https://example.invalid/file.PNG"></object>','<a href="https://example.invalid/diagram.svg?version=1">Diagram</a>','<p style="background:URL (opaque)">Legal caption</p>']:
            rows=[json.loads(l) for l in original.decode().split('\n') if l];rows[1]['semantic_html']+=html;source.write_bytes(jsonl(rows));self.repin()
            with self.subTest(html=html),self.assertRaises(ValueError):self.runpack()
            self.assertFalse(self.out.exists())
    def test_recursive_normalized_metadata_image_contexts_refused(self):
        p=package.reader('originals-flagstaff-html-v1')(self.root,load(self.proof),load(self.family))
        for value in [{'nested':{'uri':'DATA:IMAGE/svg+xml,<svg>payload</svg>'}},{'images':[{'url':'DATA:application/octet-stream;base64,SENTINEL'}]},{'snippet':'<input type=image src=opaque>'}]:
            q=copy.deepcopy(p);q.metadata['fault']=value
            with self.subTest(value=value),self.assertRaises(ValueError):artifacts(q)
    def test_root_scoped_tokenized_source_ID_parent_and_unknown_fields(self):
        from flagstaff_hierarchy import derive
        rows=[json.loads(l) for l in (self.root/'normalized/records.jsonl').read_text().split('\n') if l];inv=load(self.root/'normalized/source-inventory.json');mapping={e['edge_id']:rows[i]['record_id'] for i,e in enumerate(inv)}
        inv[1].update(source_id='child ID',ancestor_classes=['heading-0','child','ID']);d=derive(rows,inv,mapping);self.assertEqual(d['parents']['toc:edge-1'],'toc:edge-0')
        inv[1]['ancestor_classes']=['heading-0','different']
        with self.assertRaisesRegex(ValueError,'suffix'):derive(rows,inv,mapping)
        inv=load(self.root/'normalized/source-inventory.json');rows[1]['semantic_html']=rows[1]['semantic_html'].replace('id="1"','id="2"').replace('name="1"','name="2"');d=derive(rows,inv,mapping);self.assertEqual(d['records'][rows[1]['record_id']]['fields']['section_number'],'');self.assertTrue(d['issues'])


    def test_typed_adjacent_chapter_continuation_and_repeated_component_numbers(self):
        from flagstaff_hierarchy import derive
        rows=[json.loads(l) for l in (self.root/'normalized/records.jsonl').read_text().split('\n') if l];inv=load(self.root/'normalized/source-inventory.json');mapping={e['edge_id']:rows[i]['record_id'] for i,e in enumerate(inv)}
        rows[0].update(source_heading_level='h2',source_heading_classes=['CH'],heading='CHAPTER 13-16 TRAFFIC SIGNALS,',full_text='CHAPTER 13-16 TRAFFIC SIGNALS,',semantic_html='<h2 class="CH">CHAPTER 13-16 TRAFFIC SIGNALS,</h2>')
        rows[1].update(source_heading_level='h2',source_heading_classes=['CHTitle'],heading='AND CONDUIT',semantic_html='<h2 class="CHTitle">AND CONDUIT</h2>')
        inv[2]['ancestor_classes']=['heading-0','heading-1','heading-2'];d=derive(rows,inv,mapping)
        self.assertEqual(d['records']['stable-2']['fields']['chapter'],'CHAPTER 13-16 TRAFFIC SIGNALS,\nAND CONDUIT')
        rows[1]['block_indices']=[12];d=derive(rows,inv,mapping);self.assertTrue(any('continuation' in q['issue'] for q in d['issues']));self.assertEqual(d['records']['stable-2']['fields']['chapter'],'CHAPTER 13-16 TRAFFIC SIGNALS,')
        # Repeated own IDs in distinct component paths cannot cross-wire parents.
        rows[0].update(source_heading_level='h1',source_heading_classes=['Title'],heading='Book',semantic_html='<h1 class="Title">Book</h1>');inv=[dict(inv[0],source_id='book',ancestor_classes=['book'])]
        mapping={'edge-0':'stable-0'}
        for index,article in [(1,'A'),(2,'B')]:
            parent='article-'+article;eid='parent-'+article;rid='parent-record-'+article
            rows.append(dict(rows[0],record_id=rid,source_heading_level='h2',source_heading_classes=['CH'],heading='ARTICLE '+article,semantic_html='<h2 class="CH">ARTICLE '+article+'</h2>'))
            inv.append(dict(inv[0],edge_id=eid,source_id=parent,ancestor_classes=['book',parent]));mapping[eid]=rid
            leaf='leaf-'+article;inv.append(dict(inv[0],edge_id=leaf,source_id='number1',ancestor_classes=['book',parent,'number1']));mapping[leaf]=rows[index]['record_id']
        d=derive(rows,inv,mapping);self.assertEqual(d['parents']['toc:leaf-A'],'toc:parent-A');self.assertEqual(d['parents']['toc:leaf-B'],'toc:parent-B')


    def test_additional_known_image_resource_contexts_and_plain_pdf_link(self):
        p=package.reader('originals-flagstaff-html-v1')(self.root,load(self.proof),load(self.family))
        for html in ['<a type="image/png" href="data:application/octet-stream;base64,SENTINEL">Graphic</a>','<link rel="preload" as="image" href="/opaque">','<link rel="shortcut icon" href="/opaque">','<source srcset="/opaque 1x">','<svg:image href="/opaque"></svg:image>']:
            q=copy.deepcopy(p);q.rows[0]['full_text']=html;q.provenance[0]['corpus_row_sha256']=sha(canonical(q.rows[0]))
            with self.subTest(html=html),self.assertRaises(ValueError):artifacts(q)
        q=copy.deepcopy(p);q.rows[0]['full_text']+='<a type="application/pdf" href="https://example.invalid/enacted.pdf">Adopted document</a>';q.provenance[0]['corpus_row_sha256']=sha(canonical(q.rows[0]));self.assertTrue(artifacts(q))
        check_metadata({'image_omissions':[{'url':'https://example.invalid/original.png','policy':'[IMAGE]','source_sha256':'123'}]})


    def test_image_MIME_whitespace_refused_PDF_control_preserved(self):
        for tag,attribute in [('object','data'),('embed','src')]:
            for mime in [' IMAGE/PNG','\tIMAGE/PNG \n']:
                with self.subTest(tag=tag,mime=mime),self.assertRaises(ValueError):check_html('<'+tag+' type="'+mime+'" '+attribute+'="https://example.invalid/opaque"></'+tag+'>')
            check_html('<'+tag+' type=" APPLICATION/PDF " '+attribute+'="https://example.invalid/document.pdf"></'+tag+'>')
        with self.assertRaises(ValueError):check_metadata({'nested':{'type':' IMAGE/PNG ','url':'DATA:application/octet-stream;base64,PIXEL_SENTINEL'}})
        check_metadata({'nested':{'type':' APPLICATION/PDF ','url':'https://example.invalid/document.pdf'}})

if __name__=='__main__':unittest.main(verbosity=2)
