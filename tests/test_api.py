"""Tests for the JSON API endpoints."""
import pytest
from django.test import Client

from countries.models import Country
from meetings.models import Document
from speakers.models import Speaker
from speeches.models import Speech
from votes.models import Resolution


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def ga_doc(db):
    return Document.objects.create(
        symbol='A/74/PV.1', body='GA', meeting_number=1, session=74
    )


@pytest.fixture
def sc_doc(db):
    return Document.objects.create(
        symbol='S/PV.6254', body='SC', meeting_number=6254, session=64
    )


@pytest.fixture
def ga_resolution(db):
    return Resolution.objects.create(
        draft_symbol='A/C.1/78/L.1', adopted_symbol='78/100',
        body='GA', session=78, title='Test resolution',
    )


@pytest.fixture
def sc_resolution(db):
    return Resolution.objects.create(
        draft_symbol='S/2019/100', adopted_symbol='2503(2019)',
        body='SC', session=74,
    )


# ── Meeting list ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_meeting_list_returns_200(client):
    response = client.get('/api/meetings/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_meeting_list_shape(client, ga_doc):
    data = client.get('/api/meetings/').json()
    assert 'count' in data
    assert 'results' in data
    assert 'next' in data
    assert 'previous' in data


@pytest.mark.django_db
def test_meeting_list_result_fields(client, ga_doc):
    result = client.get('/api/meetings/').json()['results'][0]
    assert result['symbol'] == 'A/74/PV.1'
    assert result['body'] == 'GA'
    assert result['session'] == 74
    assert result['docs_un_url'] == 'https://docs.un.org/en/A/74/PV.1'


@pytest.mark.django_db
def test_meeting_list_body_filter(client, ga_doc, sc_doc):
    data = client.get('/api/meetings/?body=GA').json()
    symbols = [r['symbol'] for r in data['results']]
    assert 'A/74/PV.1' in symbols
    assert 'S/PV.6254' not in symbols


@pytest.mark.django_db
def test_meeting_list_session_filter(client, ga_doc, sc_doc):
    data = client.get('/api/meetings/?session=74').json()
    symbols = [r['symbol'] for r in data['results']]
    assert 'A/74/PV.1' in symbols
    assert 'S/PV.6254' not in symbols


# ── Meeting detail ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_meeting_detail_returns_200(client, ga_doc):
    response = client.get(f'/api/meetings/{ga_doc.slug}/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_meeting_detail_404(client):
    assert client.get('/api/meetings/nonexistent/').status_code == 404


@pytest.mark.django_db
def test_meeting_detail_includes_speeches(client, ga_doc):
    country = Country.objects.create(name='Testland', iso3='TST', iso2='TS')
    speaker = Speaker.objects.create(name='Jane Doe', country=country)
    Speech.objects.create(
        document=ga_doc, speaker=speaker,
        text='Peace and security.',
        position_in_document=1, position_in_item=1,
    )
    data = client.get(f'/api/meetings/{ga_doc.slug}/').json()
    assert len(data['speeches']) == 1
    assert data['speeches'][0]['speaker'] == 'Jane Doe'
    assert data['speeches'][0]['country'] == 'Testland'
    assert data['speeches'][0]['text'] == 'Peace and security.'


@pytest.mark.django_db
def test_meeting_detail_speaker_with_organization(client, ga_doc):
    speaker = Speaker.objects.create(name='UN Rep', organization='United Nations Secretariat')
    Speech.objects.create(
        document=ga_doc, speaker=speaker,
        text='On behalf of the Secretary-General.',
        position_in_document=1, position_in_item=1,
    )
    speech = client.get(f'/api/meetings/{ga_doc.slug}/').json()['speeches'][0]
    assert speech['country'] is None
    assert speech['organization'] == 'United Nations Secretariat'


# ── Resolution list ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_resolution_list_returns_200(client):
    assert client.get('/api/resolutions/').status_code == 200


@pytest.mark.django_db
def test_resolution_list_result_fields(client, ga_resolution):
    result = client.get('/api/resolutions/').json()['results'][0]
    assert result['adopted_symbol'] == '78/100'
    assert result['body'] == 'GA'
    assert result['title'] == 'Test resolution'
    assert result['docs_un_url'] == 'https://docs.un.org/en/a/res/78/100'


@pytest.mark.django_db
def test_resolution_list_body_filter(client, ga_resolution, sc_resolution):
    data = client.get('/api/resolutions/?body=GA').json()
    symbols = [r['adopted_symbol'] for r in data['results']]
    assert '78/100' in symbols
    assert '2503(2019)' not in symbols


@pytest.mark.django_db
def test_resolution_sc_docs_url(client, sc_resolution):
    result = client.get('/api/resolutions/').json()['results'][0]
    assert result['docs_un_url'] == 'https://docs.un.org/en/S/RES/2503(2019)'


# ── Resolution detail ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_resolution_detail_returns_200(client, ga_resolution):
    response = client.get(f'/api/resolutions/{ga_resolution.slug}/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_resolution_detail_404(client):
    assert client.get('/api/resolutions/nonexistent/').status_code == 404


@pytest.mark.django_db
def test_resolution_detail_fields(client, ga_resolution):
    data = client.get(f'/api/resolutions/{ga_resolution.slug}/').json()
    assert data['adopted_symbol'] == '78/100'
    assert data['session'] == 78
    assert data['votes'] == []


# ── Speaker list ────────────────────────────────────────────────────────────────

@pytest.fixture
def country(db):
    return Country.objects.create(name='Testland', iso3='TST', iso2='TS')


@pytest.fixture
def speaker(db, country):
    return Speaker.objects.create(name='Jane Doe', country=country)


@pytest.fixture
def org_speaker(db):
    return Speaker.objects.create(name='UN Rep', organization='UN Secretariat')


@pytest.mark.django_db
def test_speaker_list_returns_200(client):
    assert client.get('/api/speakers/').status_code == 200


@pytest.mark.django_db
def test_speaker_list_shape(client, speaker):
    data = client.get('/api/speakers/').json()
    assert 'count' in data
    assert 'results' in data
    assert 'next' in data
    assert 'previous' in data


@pytest.mark.django_db
def test_speaker_list_result_fields(client, speaker):
    result = client.get('/api/speakers/').json()['results'][0]
    assert result['name'] == 'Jane Doe'
    assert result['country'] == 'Testland'
    assert result['country_iso3'] == 'TST'
    assert result['id'] == speaker.pk


@pytest.mark.django_db
def test_speaker_list_filter_by_country_iso3(client, speaker, org_speaker):
    data = client.get('/api/speakers/?country=TST').json()
    names = [r['name'] for r in data['results']]
    assert 'Jane Doe' in names
    assert 'UN Rep' not in names


@pytest.mark.django_db
def test_speaker_list_filter_by_country_id(client, speaker, org_speaker, country):
    data = client.get(f'/api/speakers/?country={country.pk}').json()
    names = [r['name'] for r in data['results']]
    assert 'Jane Doe' in names
    assert 'UN Rep' not in names


@pytest.mark.django_db
def test_speaker_list_org_speaker(client, org_speaker):
    result = client.get('/api/speakers/').json()['results'][0]
    assert result['name'] == 'UN Rep'
    assert result['country'] is None
    assert result['organization'] == 'UN Secretariat'


# ── Speaker detail ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_speaker_detail_returns_200(client, speaker):
    assert client.get(f'/api/speakers/{speaker.pk}/').status_code == 200


@pytest.mark.django_db
def test_speaker_detail_fields(client, speaker):
    data = client.get(f'/api/speakers/{speaker.pk}/').json()
    assert data['name'] == 'Jane Doe'
    assert data['country'] == 'Testland'
    assert data['country_iso3'] == 'TST'


@pytest.mark.django_db
def test_speaker_detail_404(client):
    assert client.get('/api/speakers/999999/').status_code == 404


# ── API root ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_api_root_returns_200(client):
    assert client.get('/api/').status_code == 200


@pytest.mark.django_db
def test_api_root_lists_endpoints(client):
    data = client.get('/api/').json()
    assert 'endpoints' in data
    urls = [e['url'] for e in data['endpoints']]
    assert any('speakers' in u and '<id>' not in u and 'search' not in u for u in urls)
    assert any('meetings' in u and '<slug>' not in u for u in urls)
    assert any('resolutions' in u and '<slug>' not in u for u in urls)


@pytest.mark.django_db
def test_api_root_endpoint_has_required_keys(client):
    endpoints = client.get('/api/').json()['endpoints']
    for ep in endpoints:
        assert 'url' in ep
        assert 'description' in ep
        assert 'parameters' in ep
