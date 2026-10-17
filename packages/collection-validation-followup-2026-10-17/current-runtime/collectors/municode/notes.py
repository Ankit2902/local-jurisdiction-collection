"""Preserve nested publisher notes while applying the same image policy as legal bodies."""
import re
from html import escape
from image_policy import sanitize, safe_metadata, image_url

def redact_note_image_text(value):
    """Redact explicit URI bounds; ambiguous wrapped bare text stays unqualified.

    Quotes/parentheses provide a source boundary without inferring which prose
    words are base64. Bare whitespace-delimited image/prose cannot safely establish that
    boundary: retain its source hash/locator for review and prohibit completeness.
    """
    pieces=[];cursor=0;gaps=[]
    for match in re.finditer(r'data:image/',value,re.I):
        start=match.start()
        if start<cursor:continue
        prefix=value[:start].rstrip()
        opener=prefix[-1:] if prefix else ''
        closing={'"':'"',"'":"'",'(':')','[':']'}.get(opener)
        end=value.find(closing,match.end()) if closing else -1
        if end<0:
            token=re.match(r'[^\s\"\'<>\)\]]*',value[start:])
            end=start+len(token.group())
            whitespace=re.match(r'\s*',value[end:]).group()
            if whitespace and end+len(whitespace)<len(value) and value[end+len(whitespace)] not in '\"\'<>)]':
                boundary=re.search(r'[\"\'<>\)\]]',value[match.end():])
                end=match.end()+boundary.start() if boundary else len(value)
                gaps.append({'source_start_character':start,'source_end_character':end,'reason':'Unquoted whitespace-delimited data-image URI/prose boundary is ambiguous; original Notes field requires source review'})
        pieces.append(value[cursor:start]);pieces.append('[IMAGE]');cursor=end
    pieces.append(value[cursor:])
    return ''.join(pieces),gaps

def sanitize_notes(value, base, known_images=()):
    omissions = []; source_markup = []
    def walk(item, locator):
        if isinstance(item, list):
            return [walk(v, locator+'['+str(i)+']') for i, v in enumerate(item)]
        if isinstance(item, dict):
            return {k: walk(v, locator+'.'+str(k)) for k, v in item.items()}
        if not isinstance(item, str):
            return item
        markup = bool(re.search(r'<[A-Za-z/!]', item))
        if markup:
            source_markup.append(item)
            clean, found = sanitize(item, base, known_images)
            omissions.extend({**o, 'source_field': locator} for o in found)
        else:
            clean = item
        # A source image URI may also be a bare metadata/text value, outside an HTML tag.
        if image_url(clean.strip()) and not markup and not re.search(r'\s', clean.strip()):
            omissions.append({'source_field': locator, 'reason': 'note image reference deliberately omitted', 'source': safe_metadata(item, locator)})
            source_markup.append('<img src="'+escape(item, quote=True)+'">')
            return '[IMAGE]'
        if 'data:image/' in clean.lower():
            omissions.append({'source_field': locator, 'reason': 'inline image in note text deliberately omitted', 'source': safe_metadata(item, locator)})
            clean, gaps = redact_note_image_text(clean)
            for gap in gaps:
                omissions.append({'source_field':locator,'qualification_error':gap['reason'],'source_range':{'start':gap['source_start_character'],'end':gap['source_end_character']},'source':safe_metadata(item,locator)})
        return clean
    return walk(value, 'Notes'), omissions, source_markup
