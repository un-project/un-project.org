import re
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# UN symbol patterns, most-specific first so overlapping prefixes don't mis-match.
# Each tuple: (compiled regex, url_prefix)
_PATTERNS = [
    # SC resolution  e.g. S/RES/2573(2021)
    (re.compile(r'S/RES/\d+\(\d{4}\)'), '/votes/resolution/'),
    # GA resolution  e.g. A/RES/76/1
    (re.compile(r'A/RES/\d+/\d+'), '/votes/resolution/'),
    # GA meeting     e.g. A/76/PV.1
    (re.compile(r'A/\d+/PV\.\d+'), '/meeting/'),
    # SC meeting     e.g. S/PV.8900
    (re.compile(r'S/PV\.\d+'), '/meeting/'),
]


def _symbol_to_slug(symbol):
    return symbol.replace('/', '-').replace('.', '-')


@register.filter(is_safe=True)
def linkify_symbols(text):
    """
    Escape plain speech text and wrap UN meeting/resolution symbols in links.

    GA meetings:    A/76/PV.1     → /meeting/A-76-PV-1/
    SC meetings:    S/PV.8900     → /meeting/S-PV-8900/
    GA resolutions: A/RES/76/1   → /votes/resolution/A-RES-76-1/
    SC resolutions: S/RES/2573(2021) → /votes/resolution/S-RES-2573(2021)/
    """
    safe = escape(text)

    for pattern, url_prefix in _PATTERNS:
        def replace(m, prefix=url_prefix):
            symbol = m.group(0)
            slug = _symbol_to_slug(symbol)
            return f'<a href="{prefix}{slug}/">{symbol}</a>'
        safe = pattern.sub(replace, safe)

    return mark_safe(safe)
