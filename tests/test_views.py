"""Integration tests for views using the Django test client."""
import pytest
from django.test import Client

from countries.models import Country
from meetings.models import Document
from speakers.models import Speaker


@pytest.fixture
def client():
    return Client()


# ── Smoke tests ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_homepage(client):
    assert client.get('/').status_code == 200


@pytest.mark.django_db
def test_homepage_ga_filter(client):
    assert client.get('/?body=GA').status_code == 200


@pytest.mark.django_db
def test_homepage_sc_filter(client):
    assert client.get('/?body=SC').status_code == 200


@pytest.mark.django_db
def test_meeting_list(client):
    assert client.get('/meeting/').status_code == 200


@pytest.mark.django_db
def test_search_page_no_query(client):
    assert client.get('/search/').status_code == 200


@pytest.mark.django_db
def test_search_page_with_query(client):
    assert client.get('/search/?q=disarmament').status_code == 200


@pytest.mark.django_db
def test_votes_page(client):
    assert client.get('/votes/').status_code == 200


# ── Meeting list filters ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_meeting_list_body_filter(client):
    Document.objects.create(symbol='A/PV.1', body='GA', meeting_number=1, session=1)
    Document.objects.create(symbol='S/PV.1', body='SC', meeting_number=1, session=1)

    response = client.get('/meeting/?body=GA')
    assert response.status_code == 200
    assert b'A/PV.1' in response.content
    assert b'S/PV.1' not in response.content


@pytest.mark.django_db
def test_meeting_list_session_filter(client):
    Document.objects.create(symbol='A/PV.10', body='GA', meeting_number=10, session=70)
    Document.objects.create(symbol='A/PV.11', body='GA', meeting_number=11, session=71)

    response = client.get('/meeting/?session=70')
    assert b'A/PV.10' in response.content
    assert b'A/PV.11' not in response.content


@pytest.mark.django_db
def test_meeting_list_body_filter_on_view_all_link(client):
    """Regression: 'View all meetings' from GA homepage must stay scoped to GA."""
    response = client.get('/meeting/?body=GA')
    assert b'body=GA' in response.content


# ── Country detail ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_country_detail(client):
    country = Country.objects.create(name='Testland', iso3='TST', iso2='TS')
    response = client.get(f'/country/{country.iso3}/')
    assert response.status_code == 200
    assert b'Testland' in response.content


@pytest.mark.django_db
def test_country_votes_json(client):
    country = Country.objects.create(name='Voteria', iso3='VOT', iso2='VO')
    response = client.get(f'/votes/api/{country.iso3}/')
    assert response.status_code == 200
    data = response.json()
    assert data['iso3'] == 'VOT'
    assert data['votes'] == []


# ── Speaker detail ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_speaker_detail_with_country(client):
    country = Country.objects.create(name='Speakland', iso3='SPK', iso2='SK')
    speaker = Speaker.objects.create(name='Jane Doe', country=country)
    response = client.get(f'/speaker/{speaker.pk}/')
    assert response.status_code == 200
    assert b'Jane Doe' in response.content
    assert b'Speakland' in response.content


@pytest.mark.django_db
def test_speaker_detail_with_organization(client):
    speaker = Speaker.objects.create(
        name='UN Official',
        organization='United Nations Secretariat',
    )
    response = client.get(f'/speaker/{speaker.pk}/')
    assert response.status_code == 200
    assert b'UN Official' in response.content
    assert b'United Nations Secretariat' in response.content


@pytest.mark.django_db
def test_speaker_list_page(client):
    assert client.get('/speaker/').status_code == 200


@pytest.mark.django_db
def test_votes_blocs_page(client):
    assert client.get('/votes/blocs/').status_code == 200
