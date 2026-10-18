import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
project=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');repo=project/'github/local-jurisdiction-collection'
source=repo/'collectors/ops/launcher.py';shutil.copyfile(source,root/'launcher-baseline.py')
s=source.read_text();old="""    pdf_present = any(isinstance(coverage.get(key), (int, float)) and coverage.get(key) > 0 for key in
                      ('pdf_text_layer_pages_parsed', 'pdf_retained_asset_document_count',
                       'pdf_normalized_distinct_document_count'))
"""
new="""    asset_integrity = coverage.get('asset_document_integrity', {})
    required_pdf_assets = {url: detail for url, detail in asset_integrity.items()
                           if isinstance(detail, dict) and str(detail.get('format', '')).upper() == 'PDF'} if isinstance(asset_integrity, dict) else {}
    pdf_present = bool(required_pdf_assets) or any(isinstance(coverage.get(key), (int, float)) and coverage.get(key) > 0 for key in
                      ('pdf_text_layer_pages_parsed', 'pdf_retained_asset_document_count',
                       'pdf_normalized_distinct_document_count'))
"""
assert s.count(old)==1;s=s.replace(old,new)
old2="""        semantic = all(value is True for value in pdf_dimensions.values()) if pdf_dimensions else False
"""
new2="""        # Retained required PDFs are independently qualified documents, not
        # semantic credit supplied by their parent HTML or file integrity alone.
        for url, detail in required_pdf_assets.items():
            for key in ('pdf_semantic_text_completeness_qualified', 'pdf_table_completeness_qualified'):
                pdf_dimensions['asset_document_integrity[' + url + '].' + key] = detail.get(key)
        semantic = all(value is True for value in pdf_dimensions.values()) if pdf_dimensions else False
"""
assert s.count(old2)==1;s=s.replace(old2,new2);(root/'launcher-candidate.py').write_text(s)
actual=project/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/overland-primary-unified-v1/coverage.json';shutil.copyfile(actual,root/'fixtures/overland-coverage.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(root/'source-binding.json').write_text(json.dumps({'production_launcher_sha256':sha(source),'candidate_launcher_sha256':sha(root/'launcher-candidate.py'),'actual_coverage_source':str(actual.relative_to(project)),'actual_coverage_sha256':sha(actual)},indent=2)+'\n')
