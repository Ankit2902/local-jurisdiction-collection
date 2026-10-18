import copy,csv,hashlib,io,json,pathlib,sys
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P/'candidate'));sys.dont_write_bytecode=True
from collectors.encodeplus import native_document,infrastructure_logical as m
source=P.parent/'solid-waste-production-integration-candidate-v1/derivative-mixed718/records.jsonl'
base=[json.loads(x) for x in source.read_text().splitlines()];old=[r for r in base if r.get('raw_sha256')==m.source.SHA];assert len(old)==62
import gzip
fixture=json.loads(gzip.decompress((P/'candidate/collectors/encodeplus/fixtures/infrastructure-printed-native/source-ir-and-native-inventory.json.gz').read_bytes()))
cfg=json.loads((P/'candidate/collectors/encodeplus/configs/native-82-0c6b3dc40877.json').read_text());rows,_=m.project_records(fixture['source_pages'],fixture['native_inventory'],cfg,'raw/start.pdf')
rows[0]['mixed_source_diagnostic_lineage']={'original_asset_page_records':copy.deepcopy(old),'note':'Native catalog namespace replaces prior parent-asset namespace; source SHA/page geometry/words are unchanged. Other native publications untouched.'}
mixed=[];used=False
for r in base:
 if r.get('raw_sha256')==m.source.SHA:
  if not used:mixed.extend(rows);used=True
 else:mixed.append(r)
assert len(mixed)==828
assert [r for r in mixed if r.get('document_id')!=m.source.ID]==[r for r in base if r.get('raw_sha256')!=m.source.SHA]
D=P/'mixed828-native-exports';D.mkdir();out=native_document.outputs(mixed)
for name,body in out.items():(D/name).write_bytes(body)
cs=list(csv.DictReader(io.StringIO(out['records.csv'].decode())));assert len(cs)==828
for r,c in zip(mixed,cs):assert r['id']==c['id'] and r['text']==c['text'] and json.loads(c['source_pages'])==r.get('source_pages',[])
def images(rs):return [(r,b) for r in rs for b in r.get('ordered_blocks',[]) if b.get('kind')=='image_placeholder']
oldimages=images(base);newimages=images(mixed);assert len(oldimages)==len(newimages)==201
# Preserve exact standalone native ownership while exposing the historical asset alias explicitly.
alias=[];asset=old[0]['document_id']
for r,b in oldimages:
 expected=copy.deepcopy(b)
 if r.get('raw_sha256')==m.source.SHA:
  expected=json.loads(json.dumps(expected).replace(asset+'::page:',m.source.ID+'::page:'));alias.append({'old_asset_id':b['id'],'native_catalog_id':expected['id'],'source_sha256':m.source.SHA,'bbox':b['bbox']})
 assert any(expected==n for _,n in newimages)
assert len(alias)==5
proof={'passed':True,'baseline_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'before_records':718,'after_records':828,'other_record_noops':656,'actual_native_outputs_used':True,'csv_json_text_and_source_page_lists_match':True,'source_images_total':201,'other_image_ids_blocks_unchanged':196,'selected_five_images_native_catalog_ownership_unchanged_from_original_native62':True,'explicit_asset_to_catalog_image_namespace_aliases':alias,'original62_asset_diagnostics_retained':True,'raw_or_image_binaries_acquired':False,'scope':'Retained IR derivative and actual serializers only; no native parse, live acquisition or legal/dependency acceptance','output_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in out.items()}}
(P/'mixed828-differential.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'passed':True,'records':828,'other_noops':656,'images':201,'namespace_aliases':5,'csv_json_consistent':True}))
