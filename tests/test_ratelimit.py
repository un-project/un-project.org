"""Tests for the rate limiting decorator (un_site/ratelimit.py)."""
import pytest
from django.core.cache import cache
from django.test import Client, RequestFactory

from un_site.ratelimit import ratelimit


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def client():
    return Client()


# ── Decorator unit tests ────────────────────────────────────────────────────────

def test_requests_below_limit_pass(factory):
    @ratelimit(3, key_prefix='test:unit')
    def view(request):
        from django.http import HttpResponse
        return HttpResponse('ok')

    request = factory.get('/')
    request.META['REMOTE_ADDR'] = '10.0.0.1'
    for _ in range(3):
        response = view(request)
        assert response.status_code == 200


def test_request_over_limit_returns_429(factory):
    @ratelimit(3, key_prefix='test:over')
    def view(request):
        from django.http import HttpResponse
        return HttpResponse('ok')

    request = factory.get('/')
    request.META['REMOTE_ADDR'] = '10.0.0.2'
    for _ in range(3):
        view(request)
    response = view(request)
    assert response.status_code == 429


def test_json_flag_returns_json_429(factory):
    import json

    @ratelimit(1, key_prefix='test:json', json=True)
    def view(request):
        from django.http import JsonResponse
        return JsonResponse({'data': 'ok'})

    request = factory.get('/')
    request.META['REMOTE_ADDR'] = '10.0.0.3'
    view(request)  # consume the limit
    response = view(request)
    assert response.status_code == 429
    assert json.loads(response.content) == {'error': 'Too many requests'}


def test_plain_429_body(factory):
    @ratelimit(1, key_prefix='test:plain')
    def view(request):
        from django.http import HttpResponse
        return HttpResponse('ok')

    request = factory.get('/')
    request.META['REMOTE_ADDR'] = '10.0.0.4'
    view(request)
    response = view(request)
    assert response.status_code == 429
    assert b'Too many requests' in response.content


def test_different_ips_have_separate_limits(factory):
    @ratelimit(1, key_prefix='test:ips')
    def view(request):
        from django.http import HttpResponse
        return HttpResponse('ok')

    for ip in ('10.1.0.1', '10.1.0.2', '10.1.0.3'):
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = ip
        assert view(request).status_code == 200


def test_x_forwarded_for_used_as_ip(factory):
    @ratelimit(1, key_prefix='test:xff')
    def view(request):
        from django.http import HttpResponse
        return HttpResponse('ok')

    request = factory.get('/')
    request.META['REMOTE_ADDR'] = '1.2.3.4'
    request.META['HTTP_X_FORWARDED_FOR'] = '5.6.7.8, 1.2.3.4'
    view(request)           # counted against 5.6.7.8
    response = view(request)
    assert response.status_code == 429

    # Direct IP 1.2.3.4 (no XFF) is a separate bucket — still allowed
    request2 = factory.get('/')
    request2.META['REMOTE_ADDR'] = '1.2.3.4'
    assert view(request2).status_code == 200


# ── Integration: search endpoint ───────────────────────────────────────────────

@pytest.mark.django_db
def test_search_endpoint_allows_requests_under_limit(client):
    for _ in range(5):
        response = client.get('/search/', REMOTE_ADDR='10.2.0.1')
        assert response.status_code == 200


@pytest.mark.django_db
def test_search_endpoint_returns_429_over_limit(client):
    for _ in range(30):
        client.get('/search/', REMOTE_ADDR='10.2.0.2')
    response = client.get('/search/', REMOTE_ADDR='10.2.0.2')
    assert response.status_code == 429


# ── Integration: API endpoints ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_api_meetings_allows_requests_under_limit(client):
    for _ in range(5):
        response = client.get('/api/meetings/', REMOTE_ADDR='10.3.0.1')
        assert response.status_code == 200


@pytest.mark.django_db
def test_api_meetings_returns_json_429_over_limit(client):
    for _ in range(60):
        client.get('/api/meetings/', REMOTE_ADDR='10.3.0.2')
    response = client.get('/api/meetings/', REMOTE_ADDR='10.3.0.2')
    assert response.status_code == 429
    assert response.json() == {'error': 'Too many requests'}


@pytest.mark.django_db
def test_api_resolutions_returns_429_over_limit(client):
    for _ in range(60):
        client.get('/api/resolutions/', REMOTE_ADDR='10.3.0.3')
    response = client.get('/api/resolutions/', REMOTE_ADDR='10.3.0.3')
    assert response.status_code == 429
