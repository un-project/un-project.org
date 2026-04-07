from django import template
from django.http import QueryDict

register = template.Library()


@register.simple_tag(takes_context=True)
def url_with_page(context, page_num):
    """Return the current query string with page replaced by page_num."""
    request = context.get('request')
    if not request:
        return f'?page={page_num}'
    params = request.GET.copy()
    params['page'] = page_num
    return f'?{params.urlencode()}'


@register.filter
def get_item(mapping, key):
    """Look up a dict value by a variable key: {{ mydict|get_item:variable }}."""
    return mapping.get(key)


@register.simple_tag(takes_context=True)
def url_with_param(context, param, value):
    """Return the current query string with the named param set to value."""
    request = context.get('request')
    if not request:
        return f'?{param}={value}'
    params = request.GET.copy()
    params[param] = value
    return f'?{params.urlencode()}'


@register.simple_tag(takes_context=True)
def filter_url(context, **kwargs):
    """Build a filter URL preserving all current GET params (minus page),
    overriding with supplied kwargs. Pass key='' to remove a param."""
    request = context.get('request')
    params = request.GET.copy() if request else QueryDict('', mutable=True)
    params.pop('page', None)
    for key, value in kwargs.items():
        if value is None or value == '':
            params.pop(key, None)
        else:
            params[key] = value
    qs = params.urlencode()
    return f'?{qs}' if qs else '?'
