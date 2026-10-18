"""Independent stdlib-only source/IR consumer. Never imports the collector or PDF APIs."""
import csv, gzip, hashlib, io, json, pathlib, sys
sys.dont_write_bytecode = True
sha = lambda b: hashlib.sha256(b).hexdigest()
NATIVE = '877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102'
URL = 'https://codes.opkansas.org/municipal-code/doclibrary.aspx?id=29e4fde6-8eab-4f2c-a715-8914aa24cfe0'
ALIAS = 'https://online.encodeplus.com/regs/overlandpark-ks/doclibrary.aspx?id=29e4fde6-8eab-4f2c-a715-8914aa24cfe0'
IDENT = '82-8fbdce15716d'
def need(condition, message):
    if not condition: raise ValueError(message)
def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def audit(root):
    root = pathlib.Path(root).resolve(); before = snapshot(root)
    manifest = json.loads((root/'MANIFEST.json').read_text())
    expected = {f['path']: f for f in manifest['files']}
    need(set(before)-{'MANIFEST.json'} == set(expected), 'Exact packet inventory')
    for name, f in expected.items():
        need(before[name] == f['sha256'] and (root/name).stat().st_size == f['bytes'], 'Packet bytes '+name)
    run = root/'actual-retained-full172'; cp = json.loads((run/'checkpoint.json').read_text())
    cfg = json.loads((run/'config.json').read_text()); coverage = json.loads((run/'coverage.json').read_text())
    need(cp['config'] == cfg, 'Config/checkpoint identity')
    canonical = json.dumps(cfg,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    need(sha(canonical) == cp['config_sha256'], 'Config canonical hash')
    need(cfg['id'] == IDENT and cfg['url'] == URL and cfg['expected_sha256'] == NATIVE and cfg['expected_pages'] == 172, 'Exact source selector')
    need(cfg['qualification']['catalog_source_url'] == ALIAS and cfg['qualification']['catalog_alias_acquisition_verified'] is False, 'Unverified alias retained')
    src = run/cp['source']['path']; receiptpath = run/cp['source']['receipt_path']
    data = src.read_bytes(); receipt = json.loads(receiptpath.read_text())
    need(sha(data) == NATIVE == cp['source']['sha256'] and len(data) == 1658134, 'Native original bytes')
    need(sha(receiptpath.read_bytes()) == cp['source']['receipt_sha256'], 'Exact original receipt')
    need(receipt['url'] == receipt['final_url'] == URL and receipt['http_status'] == 200 and not receipt.get('challenge') and not receipt.get('error'), 'No invented alias/closing/refusal')
    need(receipt['sha256'] == NATIVE and receipt['bytes'] == len(data), 'Receipt/source binding')
    headers = {k.lower():v for k,v in receipt['headers'].items()}
    need(headers['content-type'] == 'application/pdf' and headers['content-disposition'] == 'inline; filename=UPOC-Criminal-Code-Index-(2024)-Final-v2.pdf', 'Source filename/MIME')
    for name,h in cp['code_hashes'].items():
        need(sha((run/'collector-source/collectors/encodeplus'/name).read_bytes()) == h == sha((root/'candidate/collectors/encodeplus'/name).read_bytes()), 'Executed/candidate source '+name)
    for name,h in cp['normalized_outputs'].items(): need(sha((run/name).read_bytes()) == h, 'Executed normalized bytes '+name)
    rows = [json.loads(l) for l in (run/'records.jsonl').read_text().splitlines()]
    old = [json.loads(l) for l in gzip.decompress((root/'source/cached-whole172.jsonl.gz').read_bytes()).decode().splitlines()]
    need(len(rows) == len(old) == 172, 'Whole current/cached page inventory')
    need([r['physical_page'] for r in rows] == list(range(1,173)), 'Physical order/duplicates/gaps')
    for w in cfg['qualification']['native_identity_witnesses']:
        need(w['literal'] in rows[w['physical_page']-1]['text'], 'Actual historical source witness')
    oldid, oldref = old[0]['document_id'],old[0]['raw_ref']; newid,newref = rows[0]['document_id'],rows[0]['raw_ref']
    context = {'heading','publication','jurisdiction','path','document_source_title','primary_source_owners'}
    def rebind(v):
        if isinstance(v,str): return v.replace(oldid,newid).replace(oldref,newref)
        if isinstance(v,list): return [rebind(x) for x in v]
        if isinstance(v,dict): return {rebind(k):rebind(x) for k,x in v.items()}
        return v
    images=[]; failed_cid=[]; failed_engine=[]; diagnostic_cells=0; diagnostic_disagreements=0
    for a,r in zip(old,rows):
        page=r['physical_page'];q=r['pdf_qualification']
        need(r['document_id'] == IDENT and r['id'] == IDENT+'::page:'+str(page) and r['source_url'] == URL+'#page='+str(page) and r['page_count'] == 172 and r['raw_sha256'] == NATIVE, 'Page source/identity')
        need(a['text'] == r['text'], 'Legal text must be byte-exact with cached source')
        need({k:v for k,v in rebind(a).items() if k not in context} == {k:v for k,v in r.items() if k not in context}, 'Noncontext IR changed')
        b=[x for x in r['ordered_blocks'] if x['kind']=='image_placeholder'];images.extend((page,x['bbox'],x.get('source_name')) for x in b)
        need(all(x['text']=='[IMAGE]' and x.get('pixel_extraction') is False for x in b), 'Exact inert image placeholders')
        need(len(b) == r['image_placeholder_count'] == r['text'].count('[IMAGE]'), 'Placeholder positions/count')
        if q.get('undecoded_cid_literals'): failed_cid.append(page)
        if not q['independent_text_engine_characters_agree']: failed_engine.append(page)
        d=r.get('superseded_detector_diagnostics',{}).get('original_record_fields',{}).get('pdf_qualification',{})
        diagnostic_cells += d.get('detected_table_cells',0)
        diagnostic_disagreements += d.get('detected_table_cells',0)-d.get('independent_table_cells_agree',0)
    csv.field_size_limit(64*1024*1024)
    exported=list(csv.DictReader(io.StringIO((run/'records.csv').read_text(),newline='')))
    need(len(exported)==172, 'CSV full page inventory')
    for r,c in zip(rows,exported):
        need(c == {k:str(r[k]) for k in c}, 'CSV exact canonical text/identity/order')
    words=sum(r['pdf_qualification']['source_word_count'] for r in rows)
    cells=sum(r['pdf_qualification']['detected_table_cells'] for r in rows)
    agree=sum(r['pdf_qualification']['independent_table_cells_agree'] for r in rows)
    need((words,len(images),cells,agree,diagnostic_cells,diagnostic_disagreements)==(28603,46,745,745,514,272), 'Actual denominators')
    need(len(failed_cid)==len(failed_engine)==102 and failed_cid==coverage['undecoded_CID_literal_pages'] and failed_engine==coverage['independent_engine_failure_pages'], 'Actual unresolved pages')
    for flag in ['pdf_extractable_text_reconciled','source_logical_structure_qualified','publication_text_complete','publication_complete','all_tables_detected','attachments_complete','required_external_legal_dependencies_complete','edition_complete','current_adopted_edition_qualified','jurisdiction_complete','closing_acquisition_performed']:
        need(coverage[flag] is False,'Unqualified dimension must stay false '+flag)
    need(coverage['start_end_consistent'] is None and coverage['native_document_complete'] and coverage['source_page_traversal_complete'],'Native-only scope')
    need(cp['full_native_parser_executed_once'] and cp['forbidden_operations']==[] and cp['closing_acquisition_performed'] is False,'Original one-parse guard/closing ledger')
    need(snapshot(root)==before,'Independent review mutated input')
    return {'passed':True,'manifest_sha256':before['MANIFEST.json'],'source_sha256':NATIVE,'observed_url':URL,'unverified_catalog_alias':ALIAS,'source_files_unchanged':len(before),'captured_candidate_source_files':len(cp['code_hashes']),'physical_pages':172,'source_words':words,'IMAGE_placeholders':len(images),'named_image_sources':sorted({x[2] for x in images}),'canonical_cells':cells,'canonical_cells_agree':agree,'superseded_cells':diagnostic_cells,'superseded_disagree':diagnostic_disagreements,'CID_pages':failed_cid,'independent_engine_failure_pages':failed_engine,'all172_cached_text_exact':True,'all172_noncontext_IR_equal':True,'all172_CSV_fields_exact':True,'native_parser_calls':0,'publisher_calls':0,'image_decode_render_OCR_calls':0,'legal_current_edition_closing_complete':False}
if __name__=='__main__':
    print(json.dumps(audit(sys.argv[1]),indent=2))
