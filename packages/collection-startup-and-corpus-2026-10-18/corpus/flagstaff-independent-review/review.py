"""Independent all-source inventory/field consumer, guards and ordinary CLI review."""
import sys
sys.dont_write_bytecode = True
import collections, copy, csv, hashlib, importlib, io, json, os, pathlib, re
import shutil, socket, subprocess, tempfile, time, unittest
from unittest.mock import patch

ROOT = pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00')
BASE = ROOT/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/corpus-package-fidelity-candidate-v1'
PACK = BASE/'actual/flagstaff-package-v2'
CAND = BASE/'candidate'
HERE = pathlib.Path(__file__).resolve().parent
WITNESS = HERE.parent/'corpus-package-source-groundtruth-v1/source-parent-witnesses.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
lines = lambda p: [json.loads(x) for x in p.read_text(encoding='utf-8').split('\n') if x]
FIELDS = 'jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()
start = time.monotonic()
ready = read(BASE/'CANDIDATE-READY.json')
assert sha(BASE/'CANDIDATE-MANIFEST.json') == ready['manifest_sha256']
manifest = read(BASE/'CANDIDATE-MANIFEST.json')
def check_freeze():
    for name, proof in manifest['files'].items():
        path = BASE/name
        assert path.stat().st_size == proof['bytes'] and sha(path) == proof['sha256'], name
check_freeze()
assert sha(PACK/'run-manifest.json') == ready['actual_run_manifest_sha256']
sys.path.insert(0, str(CAND))
p = importlib.import_module('package')
common = importlib.import_module('common')
test = importlib.import_module('test_package')
from PIL import Image
calls = []
def forbidden(*args, **kwargs):
    calls.append('forbidden network/image operation')
    raise AssertionError(calls[-1])

with patch.object(socket, 'socket', side_effect=forbidden), patch.object(socket, 'create_connection', side_effect=forbidden), patch.object(Image, 'open', side_effect=forbidden):
    with (HERE/'tests.log').open('w') as out:
        tested = unittest.TextTestRunner(stream=out, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test))
    assert tested.wasSuccessful() and tested.testsRun == 26
    before = common.files(PACK)
    verified = p.verify(PACK)
    assert verified['package_verified'] and verified['serialization_complete'] and not verified['complete']
    raw = PACK/'evidence/input'
    source = read(raw/'source/checkpoint.json')
    audits = read(raw/'normalized/document-audits.json')
    ir = lines(raw/'normalized/records.jsonl')
    rows = read(PACK/'aggregate-fulltext.json')['provisions']
    nodes = lines(PACK/'source-nodes.jsonl')
    dispositions = lines(PACK/'node-dispositions.jsonl')
    provenance = lines(PACK/'record-provenance.jsonl')
    witness = read(WITNESS)
    for name, h in witness['input_sha256'].items():
        assert sha(raw/name) == h
    mapping = {m['edge_id']:m['record_id'] for a in audits for m in a['mapping']}
    assert len(mapping) == len(source['inventory']) == 2658
    assert len(ir) == len(rows) == len(nodes) == len(dispositions) == len(provenance) == 2661
    byir = {r['record_id']:r for r in ir}
    bynode = {n['node_id']:n for n in nodes}
    assert len(byir) == len(bynode) == len({d['node_id'] for d in dispositions}) == 2661
    expected_parent = {w['node_id']:w['expected_source_parent_node_id'] for w in witness['witnesses']}
    # These three contextual parent bindings remain distinct from missing TOC edges.
    bodyonly = set(byir)-set(mapping.values())
    assert bodyonly == {x['record_id'] for x in witness['body_only_units']}
    body_context = {}
    from urllib.parse import urldefrag
    for rid in bodyonly:
        record = byir[rid]
        relevant = [e for e in source['inventory'] if urldefrag(e['source_url'])[0] == urldefrag(record['source_url'])[0]]
        if record['source_heading_level'] is None:
            matches = [e for e in relevant if not e.get('ancestor_classes')]
        else:
            parent_paths = [e['ancestor_classes'][:-len(e['source_id'].split())] for e in relevant]
            assert parent_paths and all(x == parent_paths[0] for x in parent_paths)
            matches = [e for e in source['inventory'] if e['root_index'] == relevant[0]['root_index'] and e.get('ancestor_classes') == parent_paths[0]]
        assert len(matches) == 1
        expected_parent['body:'+rid] = 'toc:'+matches[0]['edge_id']
        body_context[rid] = {'record_heading':record['heading'], 'parent_heading':matches[0]['label'], 'context_edges':[e['edge_id'] for e in relevant]}
    assert set(expected_parent) == set(bynode)
    for nid, parent in expected_parent.items():
        assert bynode[nid]['parent_node_id'] == parent, nid
    owner = {'toc:'+edge:rid for edge,rid in mapping.items()}
    owner.update({'body:'+rid:rid for rid in bodyonly})
    bydisp = {d['node_id']:d for d in dispositions}
    assert set(bydisp) == set(bynode)
    for nid,rid in owner.items():
        assert bydisp[nid]['record_ids'] == [rid]
    def role(record):
        classes, level, text = record['source_heading_classes'], record['source_heading_level'], record['heading']
        if classes == ['Title'] and level == 'h1': return 'title'
        if classes == ['Division'] and level == 'p': return 'division'
        if classes == ['CH'] and level == 'h2':
            if text.upper().startswith('CHAPTER '): return 'chapter'
            if text.upper().startswith('ARTICLE '): return 'article'
        if classes == ['CHTitle'] and level == 'h2': return 'chapter'
        return None
    printed_continuations = []
    def literal_label(record):
        if record['source_heading_classes'] != ['CHTitle']: return record['heading']
        i = next(i for i,r in enumerate(ir) if r['record_id'] == record['record_id'])
        previous = ir[i-1]
        assert role(previous) == 'chapter' and previous['full_text'] == previous['heading']
        assert previous['source_sha256'] == record['source_sha256']
        assert urldefrag(previous['source_url'])[0] == urldefrag(record['source_url'])[0]
        assert max(previous['block_indices'])+1 == min(record['block_indices'])
        printed_continuations.append([previous['record_id'],record['record_id']])
        return previous['heading']+'\n'+record['heading']
    content_receipts = {a['source_url']:a for a in source['artifacts'] if a['role'] == 'content'}
    fieldcounts = collections.Counter()
    duplicate_roles = []
    section_count = 0
    for i,(r,row,q) in enumerate(zip(ir,rows,provenance)):
        assert list(row) == FIELDS and all(isinstance(v,str) for v in row.values())
        expected = {k:'' for k in FIELDS}
        receipt = content_receipts[urldefrag(r['source_url'])[0]]
        heading = r['heading'] if r['source_heading_level'] else ''
        expected.update(jurisdiction=r['jurisdiction'], code_name=read(raw/'checkpoint.json')['config']['publication'], citation=heading, full_text=r['semantic_html'], source_url=r['source_url'], scrape_date=receipt['started_at'], section_name=heading)
        record_nodes = [n for n, rid in owner.items() if rid == r['record_id']]
        independent_chains = []
        alternatives = []
        for nid in record_nodes:
            chain=[]
            while nid:
                assert nid not in chain
                chain.append(nid)
                nid=expected_parent[nid]
            chain.reverse()
            independent_chains.append(chain)
            fields = {k:'' for k in ['division','title','subtitle','chapter','subchapter','article','part','subpart']}
            seenroles = set()
            for n in chain:
                ancestor=byir[owner[n]]
                field=role(ancestor)
                if field:
                    if field in seenroles: duplicate_roles.append({'record_id':r['record_id'],'chain':chain,'role':field})
                    seenroles.add(field)
                    fields[field]=literal_label(ancestor)
            alternatives.append(fields)
        assert all(x == alternatives[0] for x in alternatives)
        expected.update(alternatives[0])
        assert q['hierarchy_evidence']['source_chains'] == independent_chains
        # Independent locator derives from displayed text and retained own-source IDs.
        is_cite = r['source_heading_classes'] == ['Cite'] and r['source_heading_level'] == 'h3'
        is_section_group = r['source_heading_classes'] == ['CH'] and heading.upper().startswith('SECTION ')
        if is_cite or is_section_group:
            label = heading[8:] if is_section_group else heading
            if label.startswith('Amendment No. '):
                parts = label.split(' ',3)
                locator = ' '.join(parts[:3])
            else: locator = label.split(' ',1)[0]
            numeric = bool(re.fullmatch(r'(?:\d+|[A-Za-z]+-\d+)(?:[.-][A-Za-z0-9]+)*',locator)) or bool(re.fullmatch(r'Amendment No\. \d+',locator))
            ids = r['source_heading_ids']
            if numeric and any(x.strip().replace('-','.') == locator.replace('-','.') for x in ids):
                expected['section_number'] = locator
                section_count += 1
                if is_cite: expected['section_name'] = heading[len(locator):].lstrip()
        assert row == expected, (i,r['heading'],{k:(row[k],expected[k]) for k in FIELDS if row[k] != expected[k]})
        assert q['record_id'] == r['record_id'] and q['row_ordinal'] == i and q['rich_ir']['line_ordinal'] == i
        assert q['rich_ir']['record_sha256'] == common.sha(common.canonical(r))
        assert q['corpus_row_sha256'] == common.sha(common.canonical(row))
        assert sha(PACK/q['raw_artifact_path']) == q['raw_sha256'] == r['source_sha256'] == receipt['sha256']
        assert q['locator']['block_indices'] == r['block_indices']
        assert row['full_text'].count('[IMAGE]') == r['image_placeholder_count']
        fieldcounts.update(k for k,v in row.items() if v)
    assert not duplicate_roles and section_count == 2271
    assert sum(r['full_text'].count('[IMAGE]') for r in rows) == 882
    pid=read(PACK/'run-manifest.json')['publication_id']
    for stem in ['aggregate-fulltext','aggregate-toc','publications/'+pid+'/fulltext','publications/'+pid+'/toc']:
        expected_rows = [dict(row,full_text='') for row in rows] if stem.endswith('toc') else rows
        assert read(PACK/(stem+'.json'))['provisions'] == expected_rows
        data=(PACK/(stem+'.csv')).read_bytes()
        assert data[:3] == b'\xef\xbb\xbf'
        csv.field_size_limit(64*1024*1024)
        reader=csv.DictReader(io.StringIO(data.decode('utf-8-sig'),newline=''))
        assert reader.fieldnames == FIELDS and list(reader) == expected_rows
    inherited = read(PACK/'inherited-coverage.json')
    assert inherited == read(raw/'coverage.json')
    assert not any(inherited[k] for k in ['source_consistency_complete','publication_accepted','complete','whole_jurisdiction_complete'])
    proof=read(PACK/'evidence/proofs/read-only-proof.json')
    assert common.files(raw) == proof['evidence_sha256_before'] == proof['evidence_sha256_after']
    # Root's four concrete HTML contexts plus recursive output metadata fail closed.
    guard_cases=['<input type="image" src="opaque">','<object data="https://example.invalid/file.PNG"></object>','<a href="https://example.invalid/diagram.svg?version=1">Diagram</a>','<p style="background:URL (opaque)">Caption</p>']
    for html in guard_cases:
        try: common.check_html(html)
        except ValueError: pass
        else: raise AssertionError('Image guard accepted '+html)
    for metadata in [{'nested':[{'uri':'DATA:IMAGE/PNG;base64,QUJD\nCONTINUATION'}]}, {'image_omissions':[{'url':'data:application/octet-stream;base64,SENTINEL'}]}, {'nested':{'html':guard_cases[0]}}]:
        try: common.check_metadata(metadata)
        except ValueError: pass
        else: raise AssertionError('Metadata guard accepted payload')
    common.check_html('<a type="application/pdf" href="https://example.invalid/enacted.pdf">Adopted document</a>')
    common.check_metadata({'image_omissions':[{'url':'https://example.invalid/original.png','policy':'[IMAGE]'}]})
    assert before == common.files(PACK)

# Direct script entrypoint, without -B or bytecode environment override.
with tempfile.TemporaryDirectory() as temp:
    td=pathlib.Path(temp)
    moved=td/'relocated'
    shutil.copytree(PACK,moved)
    moved_before=common.files(moved)
    env=dict(os.environ)
    env.pop('PYTHONDONTWRITEBYTECODE',None)
    env.pop('PYTHONPYCACHEPREFIX',None)
    env.pop('PYTHONPATH',None)
    result=subprocess.run([sys.executable,str(moved/'packager-source/package.py'),'verify','--out',str(moved)],cwd=td,env=env,capture_output=True,text=True)
    (HERE/'direct-ordinary-cli.stdout').write_text(result.stdout)
    (HERE/'direct-ordinary-cli.stderr').write_text(result.stderr)
    assert result.returncode == 2 and json.loads(result.stdout) == verified
    assert moved_before == common.files(moved) and not list(moved.rglob('__pycache__'))
assert not calls
check_freeze()
report={'passed':True,'scope':'Independent frozen Flagstaff package/all 2,661 source units and direct CLI; no source normalization/native PDF/publisher/image operations',
        'candidate_manifest_sha256':sha(BASE/'CANDIDATE-MANIFEST.json'),'candidate_files_checked':len(manifest['files']),
        'operational_modules_sha256':ready['operational_modules_sha256'],'actual_run_manifest_sha256':sha(PACK/'run-manifest.json'),
        'source_groundtruth_sha256':sha(WITNESS),'source_toc_edges':2658,'source_root_nodes':18,'source_toc_parent_links':2640,
        'body_only_units':3,'body_only_parent_context':body_context,'all_2661_field_values_independently_equal':True,
        'populated_fields':dict(fieldcounts),'same_type_roles_on_source_chains':duplicate_roles,
        'same_type_role_conflict_qualification':'Zero actual conflicts; future repeated same-type hierarchy not qualified by this actual source proof',
        'all_16_fields_BOM_JSON_CSV_TOC_equal':True,'canonical_HTML_source_record_ID_date_citation_IMAGE_unchanged':True,
        'own_displayed_anchor_section_locators':section_count,'image_markers':882,'original_input_files':len(proof['evidence_sha256_before']),
        'all_original_source_inventory_dispositions_and_raw_relative_provenance_verified':True,
        'four_root_image_context_refusals':4,'recursive_normalized_metadata_payload_refusals':3,
        'ordinary_nonimage_PDF_and_image_omission_metadata_controls':True,'physical_LF_U2028_U0085_fault_test_passed':True,
        'tests_independently_passed':tested.testsRun,'ordinary_direct_shipped_CLI_exit':result.returncode,'ordinary_CLI_bytecode_or_output_mutation':False,
        'forbidden_calls':calls,'package_verified':True,'serialization_complete':True,'source_consistency_complete':False,
        'publication_accepted':False,'whole_publication_complete':False,'source_candidate_package_unchanged':True,
        'seconds':time.monotonic()-start,
        'limitations':['Only the actual Flagstaff operational HTML reader is qualified, not all families/publications.',
                       'Original three missing-source-anchor defects and all dependency/edition/jurisdiction false gates stay unchanged.',
                       'This is retained-IR packaging verification, not new raw source normalization or live acquisition.',
                       'Future conflicting same-type role chains require explicit unresolved mapping; this actual source has none.']}
(HERE/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
