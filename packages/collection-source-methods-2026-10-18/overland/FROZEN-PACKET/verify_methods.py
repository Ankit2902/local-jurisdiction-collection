"""Read-only whole-output and original-receipt audit; never re-extract a PDF."""
import sys
sys.dont_write_bytecode=True
import pathlib,json,csv,hashlib,subprocess,collections
H=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify_one(id):
 out=H/'full-native'/id;cp=json.loads((out/'checkpoint.json').read_text());cfg=json.loads((out/'config.json').read_text());cov=json.loads((out/'coverage.json').read_text());rows=[json.loads(l)for l in(out/'records.jsonl').read_text().split('\n')if l];receipt=json.loads((out/'raw/source.pdf.receipt.json').read_text());assert cfg==json.loads((H/'configs'/('native-'+id+'.json')).read_text());assert receipt==json.loads((H/'native-discovery'/(id+'.bin.receipt.json')).read_text());assert cfg['url']==receipt['url']==receipt['final_url'];assert sha(out/'raw/source.pdf')==sha(H/'native-discovery'/(id+'.bin'))==cfg['expected_sha256'];assert len(rows)==cfg['expected_pages']and[p['physical_page']for p in rows]==list(range(1,cfg['expected_pages']+1));assert all(r['document_id']==id and r['raw_sha256']==cfg['expected_sha256'] for r in rows)
 with(out/'records.csv').open(newline='')as f:
  cs=list(csv.DictReader(f));assert len(cs)==len(rows)
  for c,r in zip(cs,rows):assert all(c[k]==str(r[k]) for k in c),'CSV differs from full canonical page records'
 assert all(cov[k]is False for k in['publication_text_complete','publication_complete','attachments_complete','required_external_legal_dependencies_complete','edition_complete','jurisdiction_complete','closing_acquisition_performed']);assert cov['native_document_complete']and cov['source_page_traversal_complete'];assert cp['forbidden_operations']==[]
 command=[sys.executable,'-B',str(out/'collector-source/collectors/encodeplus/retained_native.py'),'--verify',str(out)];p=subprocess.run(command,capture_output=True);assert p.returncode==0,p.stderr.decode();replay=json.loads(p.stdout);assert replay['artifact_replay_verified']and not replay['native_parser_reexecuted'];assert all(replay[k]==v for k,v in cov.items())
 return {'id':id,'pages':len(rows),'records_sha256':sha(out/'records.jsonl'),'coverage_sha256':sha(out/'coverage.json'),'checkpoint_sha256':sha(out/'checkpoint.json'),'source_words':cov['source_word_count'],'images':cov['image_placeholders'],'cells':cov['detected_table_cells'],'agree':cov['independent_detected_cells_agree'],'cid_pages':cov['undecoded_CID_literal_pages'],'engine_disagreement_pages':cov['independent_engine_failure_pages'],'verify_command':command,'verify_exit':p.returncode,'all_original_receipt_source_config_page_csv_bindings':True}
if __name__=='__main__':
 results=[verify_one(i)for i in['82-cfe47a936088','82-7a796760f2f3','82-301463c368c5','82-02572b382672','82-34ff7d4dbd3e','82-6eedef9a53f0']];print(json.dumps({'passed':True,'documents':results,'native_parser_reexecuted':False,'network_or_image_operations':False},indent=2))
