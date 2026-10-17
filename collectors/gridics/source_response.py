"""Observed original publisher response selection; no discovery or asset fetching."""
from urllib.parse import urlsplit
from .publisher import script_role
from .image_content import is_image_content


def response_role(url,resource_type):
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.hostname!='codehub.gridics.com':return None
    if resource_type=='stylesheet':return 'stylesheet'
    if resource_type in {'document','xhr','fetch'}:return 'native_response'
    if resource_type=='script':return script_role(url)
    return None


def read_nonimage_response(response):
    """Known image MIME never reads body; mislabeled image prefix never persists.

    No image decoding or secondary resource traversal occurs. Original HTML,
    JSON, CSS, PDF, JS or ZIP with embedded image references remains source.
    """
    mime=response.headers.get('content-type','')
    if is_image_content(mime):return None,'Image MIME rejected before body read'
    raw=response.body()
    if is_image_content(mime,raw[:2048]):return None,'Separate image signature rejected; no body saved'
    return raw,None
