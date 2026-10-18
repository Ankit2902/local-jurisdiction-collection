"""Relocated read-only stdlib verification. Never parses/renders native PDFs."""
import csv,gzip,hashlib,io,json
from pathlib import Path
R=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda n:json.loads((R/n).read_text());rows=lambda b:[json.loads(l) for l in b.decode().splitlines()]
def main():
 m=read('MANIFEST.json')
 for e in m['files']:
  p=R/e['path'];assert p.is_file() and not p.is_symlink() and p.stat().st_size==e['bytes'] and sha(p.read_bytes())==e['sha256'],e['path']
 s=read('validation-summary.json');p=read('FINAL-PROMOTION-PLAN.json');assert p['deletions']==[] and p['common_registry_edits'] is False
 for e in p['whitelist']:assert sha((R/e['source']).read_bytes())==e['candidate_sha256']
 assert s['full_family_tests']['tests']==90 and s['full_family_tests']['exit']==0 and s['post_alias_integration_tests']['tests']==9 and s['post_alias_integration_tests']['exit']==0
 assert sha((R/'full-family-tests.stderr').read_bytes())==s['full_family_tests']['log_sha256'] and sha((R/'post-alias-final-nine.stderr').read_bytes())==s['post_alias_integration_tests']['log_sha256']
 olddata=gzip.decompress((R/'source-mixed636.jsonl.gz').read_bytes());assert sha(olddata)=='95e28ea3fa4a60f30cf6b55a33d12f49ca04c3b6895ceca85bfe43af3355d58a';old=rows(olddata);mixed=rows((R/'derivative-mixed718/records.jsonl').read_bytes());standalone=rows((R/'standalone-final/records.jsonl').read_bytes());logical=[r for r in mixed if r.get('unit')=='pdf_logical_unit'];other=[r for r in mixed if r.get('unit')!='pdf_logical_unit'];source=s['source_sha256'];old6=[r for r in old if r['raw_sha256']==source]
 assert len(old)==636 and len(mixed)==718 and len({r['id'] for r in mixed})==718 and len(standalone)==len(logical)==88
 assert other==[r for r in old if r['raw_sha256']!=source] and len(other)==630
 assert sum('canonical_structure_selection' in r for r in other)==17
 assert logical[0]['mixed_source_diagnostic_lineage']['original_asset_page_records']==old6 and len(old6)==6
 for a,b in zip(logical,standalone):
  x=dict(a);x.pop('source_asset_document_id');x.pop('mixed_source_diagnostic_lineage',None);assert x==b
 assert [b for r in mixed for b in r.get('ordered_blocks',[]) if b['kind']=='image_placeholder']==[b for r in old for b in r.get('ordered_blocks',[]) if b['kind']=='image_placeholder']
 assert sum(r.get('image_placeholder_count',0) for r in mixed)==201
 evidence=standalone[0]['source_document_evidence'];assert len(evidence['source_controls'])==26 and len(evidence['source_glyphs'])==15574 and len(evidence['source_tags']['references'])==109
 assert evidence['qualification']['required_external_legal_dependencies_complete'] is False and evidence['qualification']['edition_currentness_qualified'] is False
 assert len(standalone[0]['superseded_detector_diagnostics']['original_page_records'])==6
 assert all('physical_page' not in r and r['page_count']==6 and r['unit']=='pdf_logical_unit' for r in standalone)
 for folder,rs in [('standalone-final',standalone),('derivative-mixed718',mixed)]:
  cs=list(csv.DictReader(io.StringIO((R/folder/'records.csv').read_text())));assert len(cs)==len(rs)
  for a,b in zip(cs,rs):assert a['id']==b['id'] and a['text']==b['text']
  for a,b in zip(cs,rs):
   if b.get('unit')=='pdf_logical_unit':assert a['physical_page']=='' and json.loads(a['source_pages'])==b['source_pages']
 assert all(x['AST_identical_except_localimports'] for x in read('reviewed-source-core-parity.json'))
 print(json.dumps({'passed':True,'files':len(m['files']),'manifest_sha256':sha((R/'MANIFEST.json').read_bytes()),'full_family_tests':90,'post_alias_tests':9,'physical_source_pages':6,'logical_units':88,'mixed_records':718,'other_noops':630,'images_preserved':201,'wholepublication_complete':False,'writes':0,'network':0},sort_keys=True))
if __name__=='__main__':main()
