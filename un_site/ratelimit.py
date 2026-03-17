from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse


def _get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def ratelimit(requests_per_minute, key_prefix='rl', json=False):
    """Decorator that limits a view to `requests_per_minute` per client IP.

    Uses Django's cache backend (LocMemCache by default) with a 60-second
    sliding window. Returns HTTP 429 when the limit is exceeded.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            ip = _get_client_ip(request)
            cache_key = f'{key_prefix}:{ip}'
            count = cache.get(cache_key, 0)
            if count >= requests_per_minute:
                if json:
                    return JsonResponse({'error': 'Too many requests'}, status=429)
                return HttpResponse('Too many requests', status=429, content_type='text/plain')
            cache.set(cache_key, count + 1, timeout=60)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
