"""Portable known-stop guard. Missing local/tmp state never releases an observed stop."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
KNOWN_WITNESS='196ca151a450c474060d04357de28d00c7b6815aef47dabd018886f4c1abe0e5'
def advisory_state(local=None,central=None):
    paths=[Path(local) if local is not None else HERE/'access-advisory.json',Path(central) if central is not None else HERE.parent/'registry/access-advisories.json']
    records=[];errors=[];loaded=[]
    for path in paths:
        if not path.exists():continue
        try:
            data=json.loads(path.read_text())
            if data.get('schema_version')!=1:raise ValueError('Unsupported access-advisory schema')
            matching=[r for r in data.get('advisories',[]) if r.get('family')=='municode']
            if len(matching)!=1:raise ValueError('Expected exact Municode access advisory')
            record=matching[0];witness=record.get('raw_refusal_witness',{})
            if witness.get('sha256')!=KNOWN_WITNESS or record.get('operator_review_required') is not True or record.get('automatic_retry') is not False:raise ValueError('Known stop/advisory mismatch')
            records.append(record);loaded.append(str(path))
        except Exception as error:errors.append(str(path)+': '+str(error))
    if not records:errors.append('Known publisher stop remains even though canonical advisory is absent or invalid')
    return {'blocked':True,'family':'municode','operator_review_required':True,'automatic_retry':False,'known_refusal_witness_sha256':KNOWN_WITNESS,'advisories':records,'loaded_paths':loaded,'advisory_errors':errors,'reason':'Publisher access stopped after observed malformed source-relative HEAD403/Cf-Mitigated challenge; no automatic retry. Availability of other legitimate routes after the stop is untested. Missing or altered advisory/tmp state cannot release this known stop.'}
