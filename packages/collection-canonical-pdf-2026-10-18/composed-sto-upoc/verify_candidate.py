"""Relocated stdlib-only, read-only source/consumer/manifest verification."""
import collections,csv,gzip,hashlib,io,json
from pathlib import Path
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda n:json.loads((R/n).read_text())
lines=lambda b:[json.loads(l) for l in b.decode().splitlines()]
def main():
 m=read('MANIFEST.json')
 for e in m['files']:
  p=R/e['path'];assert p.is_file() and not p.is_symlink() and p.stat().st_size==e['bytes'] and sha(p.read_bytes())==e['sha256'],e['path']
 actual={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='MANIFEST.json'}
 assert actual=={e['path'] for e in m['files']}
 s=read('validation-summary.json');d=read('actual-canonical-differential.json');plan=read('FINAL-PROMOTION-PLAN.json');assert len(plan['whitelist'])==9 and plan['deletions']==[]
 for e in plan['whitelist']:assert sha((R/e['source']).read_bytes())==e['candidate_sha256']
 assert sha((R/'baseline-pdf_structure.py').read_bytes())==plan['whitelist'][0]['production_before_sha256']
 assert sha((R/'baseline-native_document.py').read_bytes())==plan['whitelist'][1]['production_before_sha256']
 assert s['suite']['tests']==76 and s['suite']['exit']==0 and sha((R/'full76-tests.stderr').read_bytes())==s['suite']['log_sha256']
 assert 'Ran 76 tests in 97.447s' in (R/'full76-tests.stderr').read_text() and (R/'full76-tests.stderr').read_text().rstrip().endswith('OK')
 raw=gzip.decompress((R/'source-original636-records.jsonl.gz').read_bytes());assert sha(raw)==d['input_records_sha256'];base=lines(raw);rows=lines((R/'derived-records.jsonl').read_bytes());sto=lines((R/'source-STO-canonical-three-pages.jsonl').read_bytes());by={r['id']:r for r in sto};counts=collections.Counter()
 assert len(base)==len(rows)==636 and len(sto)==3
 for b,r in zip(base,rows):
  assert b['id']==r['id']
  sel=r.get('canonical_structure_selection',{}).get('profile')
  if sel=='upoc_printed_index':
   old=r['superseded_detector_diagnostics']['original_record_fields'];assert old=={k:b[k] for k in ['tables','ordered_blocks','text','ordering','pdf_qualification']};x=r['source_printed_indexes'][0]
   assert r['tables']==[] and r['text']=='\n'.join(u['canonical_printed_text'] for u in x['units'])
   assert [z['word_ids'] for z in r['ordered_blocks']]==[u['source_word_ids'] for u in x['units']]
   assert collections.Counter(w for z in r['ordered_blocks'] for w in z['word_ids'])==collections.Counter(w['id'] for w in x['source_words'])
   assert r['canonical_structure_selection']['source_sha256']==r['raw_sha256']==b['raw_sha256']
   counts['UPOC']+=1
  elif r['id'] in by:assert r==by[r['id']];counts['STO']+=1
  else:assert r==b;counts['noops']+=1
  diag=r.get('superseded_detector_diagnostics',{}).get('original_record_fields');tables=diag['tables'] if diag else r['tables'];assert tables==b['tables']
  counts['oldfalse']+=sum(not c['independent_character_agreement'] for t in tables for c in t['cells']);counts['canonicalfalse']+=sum(not c['independent_character_agreement'] for t in r['tables'] for c in t['cells'])
  assert [v for v in r['ordered_blocks'] if v['kind']=='image_placeholder']==[v for v in b['ordered_blocks'] if v['kind']=='image_placeholder'];counts['images']+=r['image_placeholder_count']
 assert counts==dict(UPOC=4,STO=3,noops=629,oldfalse=795,canonicalfalse=318,images=201)
 csvrows=list(csv.DictReader(io.StringIO((R/'derived-records.csv').read_text())));assert len(csvrows)==636 and all(a['id']==b['id'] and a['text']==b['text'] for a,b in zip(csvrows,rows))
 for n,k in [('derived-records.jsonl','derived_jsonl_sha256'),('derived-records.csv','derived_csv_sha256'),('changed-four-pages.jsonl','changed_four_sha256'),('combined-changed-seven-pages.jsonl','combined_seven_sha256')]:assert sha((R/n).read_bytes())==d[k]
 assert d['dimensions']['whole_book_semantic_or_table_completeness_qualified'] is False and d['dimensions']['legacy_40th_vs_primary_42nd_adoption_conflict_resolved'] is False
 print(json.dumps({'passed':True,'manifest_sha256':sha((R/'MANIFEST.json').read_bytes()),'files':len(m['files']),'tests':76,'records':636,'counts':dict(counts),'writes':0,'network':0},sort_keys=True))
if __name__=='__main__':main()
