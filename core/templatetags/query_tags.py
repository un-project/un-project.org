from django import template

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
