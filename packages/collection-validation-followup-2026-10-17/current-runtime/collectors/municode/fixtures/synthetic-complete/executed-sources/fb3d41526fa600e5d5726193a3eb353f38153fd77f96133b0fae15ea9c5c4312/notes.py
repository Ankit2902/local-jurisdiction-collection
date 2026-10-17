"""Preserve nested publisher notes while applying the same image policy as legal bodies."""
import re
from html import escape
from image_policy import sanitize, safe_metadata, image_url

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
        if image_url(clean.strip()) and not markup:
            omissions.append({'source_field': locator, 'reason': 'note image reference deliberately omitted', 'source': safe_metadata(item, locator)})
            source_markup.append('<img src="'+escape(item, quote=True)+'">')
            return '[IMAGE]'
        if 'data:image/' in clean.lower():
            omissions.append({'source_field': locator, 'reason': 'inline image in note text deliberately omitted', 'source': safe_metadata(item, locator)})
            clean = re.sub(r'data:image/[^\s\"\'<>)]*', '[IMAGE]', clean, flags=re.I)
        return clean
    return walk(value, 'Notes'), omissions, source_markup
