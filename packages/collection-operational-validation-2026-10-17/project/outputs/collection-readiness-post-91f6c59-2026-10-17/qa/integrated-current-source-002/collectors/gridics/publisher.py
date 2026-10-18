"""Explicit profiles of retained public Gridics client code, never executed remotely.

The renderer changes BodyM markup before inserting it into the browser. Preserve
the original native text in exports; apply this profile only to the independent
rendered comparison and only when that acquisition retained the exact client.
"""
import re
from urllib.parse import urlsplit

RENDERER_SHA256 = 'e02b7d56c01f9a7d2b3a980fe469efdcd5a10f1effb387075fd75c7ec9c6564a'
ROUTER_SHA256 = 'c30a56b6f1876a252ea3fc999a6e0951141575174085a91aab6bddbeb3043ec0'


def section_renderability(root):
    """Source eligibility for the pinned client's div.section, never an exclusion.

    Initial client tree filters out missing/Body dataTag. getTextRecursively
    creates section wrappers only for a nonempty text value on section/subsection.
    Every native root is still acquired, including those this UI cannot expose.
    """
    original = root.get('li_attr')
    attrs = original if isinstance(original,dict) else {}
    reasons = []
    if not isinstance(attrs.get('dataTag'),str) or attrs['dataTag'] not in {'section', 'subsection'}:
        reasons.append('Pinned renderer has no section wrapper for this dataTag')
    if not isinstance(root.get('text'), str) or not root['text'].strip():
        reasons.append('Source heading text is missing or empty')
    if not isinstance(attrs.get('tag'),str) or attrs['tag'] not in {'h1','h2','h3','h4','h5','h6'}:
        reasons.append('Source heading tag is unknown')
    return {'eligible':not reasons,'reasons':reasons}


def script_role(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname != 'codehub.gridics.com':
        return None
    if re.fullmatch(r'/build/static/js/Doc\.[a-zA-Z0-9]+\.chunk\.js', parsed.path):
        return 'renderer'
    if parsed.path == '/react/init/js':
        return 'router'
    return None


def body_for_rendering(markup, parent_data_tag):
    if parent_data_tag not in {'section', 'subsection'}:
        return markup
    # Exact three replacements in getTextRecursively of the pinned client.
    markup = re.sub(r'(<p\b[^>]*>)(</p>)', r'\1<br />\2', markup)
    markup = re.sub(r'>[\t\n\v\f\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+<', '><', markup)
    return re.sub(r'(\n|\t)+', '', markup)


def fragment_path(fragment):
    # Exact routing separators/options in getPathParts of the pinned client.
    for expression in (r'&anchor=(.[^&]+)', r'&elementIndex=([^&]+)', r'&elementTag=([^&]+)'):
        fragment = re.sub(expression, '', fragment, count=1)
    fragment = fragment.replace('#', '', 1).replace('%5C', '/').replace('\\', '/')
    return '/' + '/'.join(part for part in fragment.split('/') if part)
