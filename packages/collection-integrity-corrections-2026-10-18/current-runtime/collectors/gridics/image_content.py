"""Reject separate image responses without decoding or extracting pixels."""
import re


def is_image_content(content_type, prefix=b''):
    if str(content_type).strip().lower().startswith('image/'):
        return True
    if prefix.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff', b'GIF87a', b'GIF89a', b'II*\x00', b'MM\x00*', b'BM', b'\x00\x00\x01\x00')):
        return True
    if prefix.startswith(b'RIFF') and prefix[8:12] == b'WEBP':
        return True
    if prefix[4:8] == b'ftyp' and prefix[8:12] in {b'avif', b'avis', b'heic', b'heix', b'hevc', b'hevx', b'mif1', b'msf1'}:
        return True
    text = prefix.removeprefix(b'\xef\xbb\xbf')
    return bool(re.match(br'\s*(?:<\?xml[^>]+>\s*)?<svg\b', text, re.I))
