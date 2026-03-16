"""Unit tests for model properties — no database required."""
from meetings.models import Document
from countries.models import Country
from speeches.models import Speech
from search.models import SearchIndex


# ── Document ───────────────────────────────────────────────────────────────────

def test_document_slug_replaces_slashes_and_dots():
    assert Document(symbol='A/PV.100').slug == 'A-PV-100'
    assert Document(symbol='S/PV.4321').slug == 'S-PV-4321'


def test_document_body_display():
    assert Document(body='GA').body_display == 'General Assembly'
    assert Document(body='SC').body_display == 'Security Council'


def test_document_body_display_unknown_falls_back():
    assert Document(body='XX').body_display == 'XX'


# ── Country ────────────────────────────────────────────────────────────────────

def test_country_flag_url_with_iso3():
    assert Country(iso3='FRA').flag_url == '/static/flags/FRA.svg'


def test_country_flag_url_without_iso3():
    assert Country().flag_url is None


def test_country_display_name_uses_short_name():
    c = Country(name='United States of America', short_name='United States')
    assert c.display_name == 'United States'


def test_country_display_name_falls_back_to_name():
    assert Country(name='France').display_name == 'France'


# ── Speech ─────────────────────────────────────────────────────────────────────

def test_speech_excerpt_truncates_at_300():
    s = Speech(text='x' * 400)
    assert s.excerpt == 'x' * 300 + '…'


def test_speech_excerpt_keeps_short_text():
    s = Speech(text='Hello world')
    assert s.excerpt == 'Hello world'


def test_speech_excerpt_exact_boundary():
    s = Speech(text='y' * 300)
    assert s.excerpt == 'y' * 300  # no ellipsis


# ── SearchIndex ────────────────────────────────────────────────────────────────

def test_search_index_document_slug():
    assert SearchIndex(document_symbol='A/PV.100').document_slug == 'A-PV-100'


def test_search_index_document_slug_none_when_no_symbol():
    assert SearchIndex().document_slug is None


# ── Resolution ─────────────────────────────────────────────────────────────────

def test_resolution_docs_un_url_ga():
    from votes.models import Resolution
    r = Resolution(body='GA', adopted_symbol='78/100')
    assert r.docs_un_url == 'https://docs.un.org/en/a/res/78/100'


def test_resolution_docs_un_url_sc():
    from votes.models import Resolution
    r = Resolution(body='SC', adopted_symbol='2503(2019)')
    assert r.docs_un_url == 'https://docs.un.org/en/S/RES/2503(2019)'


def test_resolution_docs_un_url_none_without_adopted_symbol():
    from votes.models import Resolution
    assert Resolution(body='GA', draft_symbol='A/C.1/78/L.1').docs_un_url is None
