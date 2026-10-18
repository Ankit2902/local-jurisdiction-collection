"""Hash-bound changed-predicate exposure; inert parsing only, no source acquisition."""
import hashlib,json,socket,sys
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
root=Path(sys.argv[1]);base=Path(__file__).resolve().parent;follow=root/'outputs/collection-readiness-followup-2026-10-17/american-legal'
sha=lambda b:hashlib.sha256(b).hexdigest();results=[]
with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')),patch('PIL.Image.open',side_effect=AssertionError('No image decoding')):
 for name,source,normalized in [('Dallas',follow/'primary-4-dallas_tx-v7',follow/'research/native-note-ownership-v1/actual-dallas-normalization'),('Cleveland',follow/'cleveland-final-v6',follow/'cleveland-final-v6')]:
  entry=json.loads((source/'requests.json').read_text())['native-export'];raw=(source/entry['file']).read_bytes();assert sha(raw)==entry['sha256'];soup=BeautifulSoup(raw,'html.parser');anchors=soup.find_all(['a','link']);affected=[{'tag':e.name,'source_id':e.get('id'),'raw_ref_sha256':sha((e.get('href') or e.get('to') or '').encode()),'markup_sha256':sha(str(e).encode())} for e in anchors if (e.get('href') or e.get('to')) and e.get('type','').strip().lower().startswith('image/')]
  results.append({'publication':name,'source_native_sha256':sha(raw),'source_native_bytes':len(raw),'source_anchor_link_count':len(anchors),'declared_image_anchor_link_count':len(affected),'affected':affected,'retained_sections_sha256':sha((normalized/'sections.jsonl').read_bytes()),'retained_CSV_sha256':sha((normalized/'sections.csv').read_bytes()),'changed_predicate_unreachable_on_exact_source':not affected,'byte_compatibility':'Exact changed predicate and its added branch are unreachable on every original source anchor/link; unchanged source input and every other parser statement imply byte-identical output. No fresh acquisition or full replay claimed.' if not affected else 'Affected source found: requires separate fresh normalization before byte-compatibility claim'})
  del soup,anchors,raw
report={'kind':'Current image-context changed-predicate exposure, original native source bytes','before_model_sha256':sha((base.parent/'executed-v9/model.py').read_bytes()),'candidate_model_sha256':sha((base/'source/model.py').read_bytes()),'sources':results,'zero_affected_source_anchors':all(not r['affected'] for r in results),'network_requests':0,'image_decode_calls':0,'new_live_acquisition':False}
(base/'actual-source-exposure.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
