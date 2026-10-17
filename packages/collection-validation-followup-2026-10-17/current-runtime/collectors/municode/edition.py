"""Conservative native PDF header assessment; never all-body correspondence proof."""
import re
def assess_edition(job, header):
    name=job.get('Name') or ''
    api=re.search(r'\bsupplement\s+(\d+)\b',name,re.I)
    native=re.search(r'\bsupplement\s+(?:no\.?\s*)?(\d+)\b',header,re.I)
    result={'api_job_id':job.get('Id'),'api_job_name':name,'native_supplement_number':int(native.group(1)) if native else None,'api_supplement_number':int(api.group(1)) if api else None,'status':'unqualified','edition_label_matches':None,'full_body_correspondence_verified':False}
    if api and native and api.group(1)!=native.group(1):
        result.update(status='mismatch',edition_label_matches=False,reason='Native PDF supplement differs from current API job; publisher download routing alone did not establish edition alignment.')
    else:
        normalize=lambda s:re.findall(r'[a-z]+|[0-9]+',re.sub(r'\bsupplement\s+no\.?', 'supplement',s,flags=re.I).lower())
        wanted=normalize(name);actual=normalize(header)
        if len(''.join(wanted))>=8 and any(actual[i:i+len(wanted)]==wanted for i in range(len(actual))):
            result.update(status='header_label_corroborated',edition_label_matches=True,reason='Exact normalized job label appears in the native header; this is header corroboration only, not body completeness or identity proof.')
        else:result['reason']='Native header does not establish the complete API job label; no edition-alignment claim.'
    return result
