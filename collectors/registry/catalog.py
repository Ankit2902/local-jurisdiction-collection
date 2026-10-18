"""Union catalog for stable expansion IDs and separately namespaced original IDs."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load_catalog(cohort='all', here=None):
    """Return {targets:[],publications:[]} without network or filesystem writes.

    Existing numeric string IDs remain unchanged. No proof is inherited across
    aliases. The original cohort is independently source-bound and qualified.
    """
    here=Path(here or HERE)
    if cohort not in ('expansion','original','all'):raise ValueError('Unknown cohort')
    ts=[];ps=[]
    for name in (['expansion','original'] if cohort=='all' else [cohort]):
        prefix='' if name=='expansion' else 'original-'
        for filename,out,key in [(prefix+'targets.json',ts,'targets'),(prefix+'publications.json',ps,'publications')]:
            data=json.loads((here/filename).read_text());out.extend(data[key])
    for filename in ('readiness-additional-publications.json','followup-additional-publications.json'):
        additional=here/filename
        if additional.exists():
            selected={t['id'] for t in ts}
            ps.extend(p for p in json.loads(additional.read_text())['publications'] if p['target_id'] in selected)
    for entries in (ts,ps):
        ids=[x['id'] for x in entries]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate catalog IDs')
    tids={t['id'] for t in ts}
    if any(p['target_id'] not in tids for p in ps):raise ValueError('Publication owner absent')
    override_path=here/'readiness-overrides.json'
    if override_path.exists():
        overrides=json.loads(override_path.read_text())['publications']
        for pub in ps:pub.update(overrides.get(pub['id'],{}))
    qualification_path=here/'readiness-qualified-configs.json'
    if qualification_path.exists():
        qualifications=json.loads(qualification_path.read_text())['publications']
        for pub in ps:pub.update(qualifications.get(pub['id'],{}))
    qualification_path=here/'followup-qualified-configs.json'
    if qualification_path.exists():
        qualifications=json.loads(qualification_path.read_text())['publications']
        for pub in ps:pub.update(qualifications.get(pub['id'],{}))
    qualification_path=here/'original-adapter-qualified-configs.json'
    if qualification_path.exists():
        qualifications=json.loads(qualification_path.read_text())['publications']
        for pub in ps:pub.update(qualifications.get(pub['id'],{}))
    advisory_path=here/'access-advisories.json'
    if not advisory_path.is_file():raise ValueError('Access advisory catalog missing; use the complete collector package')
    if advisory_path.exists():
        advisories=json.loads(advisory_path.read_text())['advisories']
        for pub in ps:
            pub['observed_access_advisories']=[a for a in advisories if a.get('operator_review_required') and a['family'] in (pub['publisher'],pub['source_family'])]
    by_id={p['id']:p for p in ps}
    for target in ts:target['primary_publication']=by_id[target['primary_publication_id']]
    return {'schema_version':1,'cohort':cohort,'targets':ts,'publications':ps}
