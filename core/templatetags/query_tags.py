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
