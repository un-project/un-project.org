"""Tests for the JSON API endpoints."""
import pytest
from django.test import Client

from countries.models import Country
from meetings.models import Document
from speakers.models import Speaker
from speeches.models import Speech
from votes.models import Resolution, ResolutionSponsor, Veto


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


# ── Country list/detail ────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_country_list_returns_200(client, country):
    assert client.get('/api/countries/').status_code == 200


@pytest.mark.django_db
def test_country_list_shape(client, country):
    data = client.get('/api/countries/').json()
    assert 'count' in data
    assert 'results' in data


@pytest.mark.django_db
def test_country_list_result_fields(client, country):
    result = client.get('/api/countries/').json()['results'][0]
    assert result['iso3'] == 'TST'
    assert result['name'] == 'Testland'
    assert 'flag_url' in result
    assert 'url' in result


@pytest.mark.django_db
def test_country_list_q_filter(client, country):
    Country.objects.create(name='Otherland', iso3='OTH', iso2='OT')
    data = client.get('/api/countries/?q=Test').json()
    names = [r['name'] for r in data['results']]
    assert 'Testland' in names
    assert 'Otherland' not in names


@pytest.mark.django_db
def test_country_detail_returns_200(client, country):
    assert client.get(f'/api/countries/{country.iso3}/').status_code == 200


@pytest.mark.django_db
def test_country_detail_fields(client, country):
    data = client.get(f'/api/countries/{country.iso3}/').json()
    assert data['iso3'] == 'TST'
    assert data['name'] == 'Testland'


@pytest.mark.django_db
def test_country_detail_404(client):
    assert client.get('/api/countries/ZZZ/').status_code == 404


# ── Ideal points ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_country_ideal_points_returns_200(client, country):
    assert client.get(f'/api/countries/{country.iso3}/ideal-points/').status_code == 200


@pytest.mark.django_db
def test_country_ideal_points_shape(client, country):
    data = client.get(f'/api/countries/{country.iso3}/ideal-points/').json()
    assert 'iso3' in data
    assert 'data' in data
    assert isinstance(data['data'], list)


@pytest.mark.django_db
def test_country_ideal_points_404(client):
    assert client.get('/api/countries/ZZZ/ideal-points/').status_code == 404


# ── Alignment ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_country_alignment_requires_params(client, country):
    assert client.get(f'/api/countries/{country.iso3}/alignment/').status_code == 400


@pytest.mark.django_db
def test_country_alignment_by_year(client, country):
    data = client.get(f'/api/countries/{country.iso3}/alignment/?year=2020').json()
    assert 'data' in data
    assert data['year'] == 2020


@pytest.mark.django_db
def test_country_alignment_by_partner(client, country):
    partner = Country.objects.create(name='Partnerland', iso3='PTN', iso2='PT')
    data = client.get(f'/api/countries/{country.iso3}/alignment/?partner={partner.iso3}').json()
    assert 'data' in data
    assert data['partner'] == 'PTN'


@pytest.mark.django_db
def test_country_alignment_404(client):
    assert client.get('/api/countries/ZZZ/alignment/?year=2020').status_code == 404


# ── Vetoes ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def veto(db, country):
    v = Veto.objects.create(dppa_id=42, draft_symbol='S/2020/100', date='2020-01-15')
    v.vetoing_countries.add(country)
    return v


@pytest.mark.django_db
def test_veto_list_returns_200(client):
    assert client.get('/api/vetoes/').status_code == 200


@pytest.mark.django_db
def test_veto_list_shape(client, veto):
    data = client.get('/api/vetoes/').json()
    assert 'count' in data
    assert 'results' in data


@pytest.mark.django_db
def test_veto_list_result_fields(client, veto):
    result = client.get('/api/vetoes/').json()['results'][0]
    assert result['dppa_id'] == 42
    assert result['draft_symbol'] == 'S/2020/100'
    assert result['date'] == '2020-01-15'
    assert len(result['vetoing_countries']) == 1
    assert result['vetoing_countries'][0]['iso3'] == 'TST'


@pytest.mark.django_db
def test_veto_list_country_filter(client, veto):
    other = Country.objects.create(name='Otherland', iso3='OTH', iso2='OT')
    data = client.get(f'/api/vetoes/?country=OTH').json()
    assert data['count'] == 0


@pytest.mark.django_db
def test_veto_list_year_filter(client, veto):
    data = client.get('/api/vetoes/?year=2020').json()
    assert data['count'] == 1
    data2 = client.get('/api/vetoes/?year=2019').json()
    assert data2['count'] == 0


# ── Resolution sponsors ────────────────────────────────────────────────────────

@pytest.fixture
def ga_resolution_with_sponsor(db, country):
    res = Resolution.objects.create(
        draft_symbol='A/C.1/79/L.5', adopted_symbol='79/55',
        body='GA', session=79, title='Sponsored resolution',
    )
    ResolutionSponsor.objects.create(resolution=res, country=country, country_name='Testland')
    return res


@pytest.mark.django_db
def test_resolution_sponsors_returns_200(client, ga_resolution_with_sponsor):
    assert client.get(f'/api/resolutions/{ga_resolution_with_sponsor.slug}/sponsors/').status_code == 200


@pytest.mark.django_db
def test_resolution_sponsors_fields(client, ga_resolution_with_sponsor):
    data = client.get(f'/api/resolutions/{ga_resolution_with_sponsor.slug}/sponsors/').json()
    assert 'sponsors' in data
    assert len(data['sponsors']) == 1
    assert data['sponsors'][0]['iso3'] == 'TST'
    assert data['sponsors'][0]['country_name'] == 'Testland'


@pytest.mark.django_db
def test_resolution_sponsors_404(client):
    assert client.get('/api/resolutions/nonexistent/sponsors/').status_code == 404


# ── Extended resolution list filters ──────────────────────────────────────────

@pytest.fixture
def important_sc_resolution(db):
    return Resolution.objects.create(
        draft_symbol='S/2021/200', adopted_symbol='2599(2021)',
        body='SC', session=76, title='Important SC resolution',
        important_vote=True, issue_me=True,
    )


@pytest.mark.django_db
def test_resolution_list_important_vote_filter(client, ga_resolution, important_sc_resolution):
    data = client.get('/api/resolutions/?important_vote=true').json()
    symbols = [r['adopted_symbol'] for r in data['results']]
    assert '2599(2021)' in symbols
    assert '78/100' not in symbols


@pytest.mark.django_db
def test_resolution_list_issue_filter(client, ga_resolution, important_sc_resolution):
    data = client.get('/api/resolutions/?issue=me').json()
    symbols = [r['adopted_symbol'] for r in data['results']]
    assert '2599(2021)' in symbols
    assert '78/100' not in symbols


@pytest.mark.django_db
def test_resolution_list_includes_important_vote_field(client, important_sc_resolution):
    result = client.get('/api/resolutions/').json()['results'][0]
    assert 'important_vote' in result
    assert result['important_vote'] is True


@pytest.mark.django_db
def test_resolution_list_includes_issue_codes(client, important_sc_resolution):
    result = client.get('/api/resolutions/').json()['results'][0]
    assert 'issue_codes' in result
    assert 'me' in result['issue_codes']


# ── Extended resolution detail fields ─────────────────────────────────────────

@pytest.mark.django_db
def test_resolution_detail_includes_sponsors(client, ga_resolution_with_sponsor):
    data = client.get(f'/api/resolutions/{ga_resolution_with_sponsor.slug}/').json()
    assert 'sponsors' in data
    assert len(data['sponsors']) == 1
    assert data['sponsors'][0]['iso3'] == 'TST'


@pytest.mark.django_db
def test_resolution_detail_includes_extended_fields(client, important_sc_resolution):
    data = client.get(f'/api/resolutions/{important_sc_resolution.slug}/').json()
    assert 'important_vote' in data
    assert 'issue_codes' in data
    assert 'draft_text' in data
    assert 'sponsors' in data


# ── Extended meeting detail: unattributed/duplicate flags ─────────────────────

@pytest.mark.django_db
def test_meeting_detail_unattributed_flag(client, ga_doc):
    speaker = Speaker.objects.create(name='Unknown')
    Speech.objects.create(
        document=ga_doc, speaker=speaker,
        text='Some speech.',
        position_in_document=1, position_in_item=1,
    )
    speech = client.get(f'/api/meetings/{ga_doc.slug}/').json()['speeches'][0]
    assert speech['unattributed'] is True
    assert 'duplicate' in speech


@pytest.mark.django_db
def test_meeting_detail_attributed_flag_false(client, ga_doc):
    country = Country.objects.create(name='Testland2', iso3='TS2', iso2='T2')
    speaker = Speaker.objects.create(name='Rep2', country=country)
    Speech.objects.create(
        document=ga_doc, speaker=speaker,
        text='A speech by a country rep.',
        position_in_document=1, position_in_item=1,
    )
    speech = client.get(f'/api/meetings/{ga_doc.slug}/').json()['speeches'][0]
    assert speech['unattributed'] is False


@pytest.mark.django_db
def test_meeting_detail_duplicate_flag(client, ga_doc):
    country = Country.objects.create(name='Testland3', iso3='TS3', iso2='T3')
    speaker = Speaker.objects.create(name='Rep3', country=country)
    identical_text = 'This is an important statement about peace.'
    Speech.objects.create(
        document=ga_doc, speaker=speaker, text=identical_text,
        position_in_document=1, position_in_item=1,
    )
    Speech.objects.create(
        document=ga_doc, speaker=speaker, text=identical_text,
        position_in_document=2, position_in_item=2,
    )
    speeches = client.get(f'/api/meetings/{ga_doc.slug}/').json()['speeches']
    assert len(speeches) == 2
    assert speeches[0]['duplicate'] is False
    assert speeches[1]['duplicate'] is True


# ── Search endpoint ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_search_requires_query(client):
    assert client.get('/api/search/').status_code == 400
    assert client.get('/api/search/?q=a').status_code == 400


@pytest.mark.django_db
def test_search_returns_200(client):
    assert client.get('/api/search/?q=peace').status_code == 200


@pytest.mark.django_db
def test_search_result_shape(client):
    data = client.get('/api/search/?q=nuclear').json()
    assert 'count' in data
    assert 'results' in data
