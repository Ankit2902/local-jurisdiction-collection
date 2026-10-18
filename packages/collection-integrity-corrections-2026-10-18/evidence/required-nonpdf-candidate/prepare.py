import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent;repo=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
source=repo/'collectors/ops/launcher.py';baseline=source.read_text();shutil.copyfile(source,root/'launcher-baseline.py')
needle="""    native = any(coverage.get(key) is True for key in
"""
replacement="""    # The integrity map contains required nonimage documents only. Unknown or
    # non-PDF formats need their own explicit text/structure qualification;
    # nonempty bytes, archive integrity or parent HTML are not that proof.
    nonpdf_dimensions = {}
    if isinstance(asset_integrity, dict):
        for url, detail in asset_integrity.items():
            if url in required_pdf_assets:
                continue
            detail = detail if isinstance(detail, dict) else {}
            for key in ('document_text_completeness_qualified', 'document_structure_completeness_qualified'):
                nonpdf_dimensions['asset_document_integrity[' + url + '].' + key] = detail.get(key)
    if nonpdf_dimensions:
        semantic = semantic and all(value is True for value in nonpdf_dimensions.values())
    native = any(coverage.get(key) is True for key in
"""
assert baseline.count(needle)==1;candidate=baseline.replace(needle,replacement)
needle2="""            'pdf_structure_dimensions': pdf_dimensions,
"""
assert candidate.count(needle2)==1;candidate=candidate.replace(needle2,needle2+"            'nonpdf_document_structure_dimensions': nonpdf_dimensions,\n")
(root/'launcher-candidate.py').write_text(candidate);shutil.copyfile(repo/'collectors/encodeplus/documents.py',root/'encodeplus-documents.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(root/'source-binding.json').write_text(json.dumps({'production_launcher_sha256':sha(source),'candidate_launcher_sha256':sha(root/'launcher-candidate.py'),'provider_source':'collectors/encodeplus/documents.py','provider_sha256':sha(repo/'collectors/encodeplus/documents.py'),'retained_nonpdf_witness':'None found in bounded next-phase EP coverage scan; provider-behavior regression only'},indent=2)+'\n')
