"""Narrow MIME-whitespace delta review; no source/network/native reparse."""
import sys
sys.dont_write_bytecode=True
import copy,hashlib,importlib,json,pathlib,socket,unittest
from unittest.mock import patch
ROOT=pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00')
PREFIX=ROOT/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59'
OLD=PREFIX/'corpus-package-fidelity-candidate-v1/candidate/common.py'
CAND=PREFIX/'corpus-package-image-mime-candidate-v1/candidate'
HERE=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='b522283ffaa16e8d8291357dc7de437b4b0dcab82ea800c6b5ce050999b70308'
assert sha(CAND/'common.py')==expected
old=OLD.read_text();new=(CAND/'common.py').read_text()
assert new==old.replace("attrs.get('type','').lower().startswith('image/')","attrs.get('type','').strip().lower().startswith('image/')").replace("str(value.get(k,'')).lower()","str(value.get(k,'')).strip().lower()")
sys.path.insert(0,str(CAND));common=importlib.import_module('common');tests=importlib.import_module('test_package')
from PIL import Image
calls=[]
def no(*a,**k):calls.append('forbidden image/network operation');raise AssertionError(calls[-1])
rejected=[]
with patch.object(socket,'socket',side_effect=no),patch.object(socket,'create_connection',side_effect=no),patch.object(Image,'open',side_effect=no):
    with (HERE/'tests.log').open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    assert result.wasSuccessful() and result.testsRun==27
    for html in ['<object type=" IMAGE/PNG" data="https://example.test/123"></object>','<embed type=" IMAGE/PNG" src="https://example.test/123">']:
        try:common.check_html(html)
        except ValueError:rejected.append(html)
        else:raise AssertionError('Known image HTML accepted')
    metadata={'type':' IMAGE/PNG','url':'data:application/octet-stream;base64,SYNTHETIC_SENTINEL'}
    original=copy.deepcopy(metadata)
    try:common.check_metadata(metadata)
    except ValueError:rejected.append('recursive padded MIME known image opaque data payload')
    else:raise AssertionError('Known image metadata accepted')
    assert metadata==original
    pdf='<a type=" application/pdf " href="https://example.test/123">Available legal document label</a>'
    common.check_html(pdf)
    ordinary={'type':' application/pdf ','url':'https://example.test/123','caption':'Available legal document label'}
    before=copy.deepcopy(ordinary);common.check_metadata(ordinary);assert ordinary==before
    omissions={'image_omissions':[{'url':'https://example.test/original.png','policy':'[IMAGE]','caption':'Available label'}]}
    common.check_metadata(omissions)
assert not calls and sha(CAND/'common.py')==expected
report={'passed':True,'scope':'Only padded MIME classification delta; original data/output applicability is separately measured by owner',
        'old_common_sha256':sha(OLD),'common_sha256':expected,'exact_delta_only_strip_before_existing_lower_classification':True,
        'tests_independently_passed':27,'known_image_contexts_refused':rejected,
        'ordinary_nonimage_PDF_link_and_metadata_unchanged':True,'omitted_image_locator_and_available_label_metadata_preserved':True,
        'synthetic_metadata_not_mutated':True,'forbidden_calls':calls,'source_unchanged':True,
        'source_normalization_native_parse_or_network':False,'actual_source_exposure_claim':False}
(HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
