from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Min, Max, Count, Q
from .models import Country
from speakers.models import Speaker
from speeches.models import Speech
from votes.models import CountryVote


def _render_country_detail(request, country):
    # Session and body filters
    session_param = request.GET.get('session', '')
    try:
        current_session = int(session_param) if session_param else None
    except ValueError:
        current_session = None
    body_param = request.GET.get('body', '')
    current_body = body_param if body_param in ('GA', 'SC') else ''

    # Representatives — scoped to session when active, annotated with career year range
    rep_qs = Speaker.objects.filter(country=country)
    if current_session:
        rep_qs = rep_qs.filter(speeches__document__session=current_session)
    if current_body:
        rep_qs = rep_qs.filter(speeches__document__body=current_body)
    rep_qs = rep_qs.annotate(
        first_year=Min('speeches__document__date__year'),
        last_year=Max('speeches__document__date__year'),
    ).order_by('name')
    rep_paginator = Paginator(rep_qs, 20)
    representatives_page = rep_paginator.get_page(request.GET.get('reps_page'))

    # Available sessions (union of speech/vote sessions, filtered by body, descending)
    speech_session_qs = Speech.objects.filter(speaker__country=country, document__date__year__gt=1900)
    vote_session_qs = CountryVote.objects.filter(country=country, vote__document__date__year__gt=1900)
    if current_body:
        speech_session_qs = speech_session_qs.filter(document__body=current_body)
        vote_session_qs = vote_session_qs.filter(vote__document__body=current_body)
    speech_sessions = set(speech_session_qs.values_list('document__session', flat=True).distinct())
    vote_sessions = set(vote_session_qs.values_list('vote__document__session', flat=True).distinct())
    sessions = sorted((speech_sessions | vote_sessions) - {None}, reverse=True)

    # Speeches (filtered by session and body)
    speech_qs = (
        Speech.objects.filter(speaker__country=country, document__date__year__gt=1900)
        .select_related('speaker', 'document')
        .order_by('-document__date', '-position_in_document')
    )
    if current_session:
        speech_qs = speech_qs.filter(document__session=current_session)
    if current_body:
        speech_qs = speech_qs.filter(document__body=current_body)
    paginator = Paginator(speech_qs, getattr(settings, 'SPEECHES_PER_PAGE', 20))
    speeches_page = paginator.get_page(request.GET.get('page'))

    # Vote stats — filtered by session and body
    vote_qs = CountryVote.objects.filter(country=country, vote__document__date__year__gt=1900)
    if current_session:
        vote_qs = vote_qs.filter(vote__document__session=current_session)
    if current_body:
        vote_qs = vote_qs.filter(vote__document__body=current_body)
    vote_stats = vote_qs.aggregate(
        yes=Count('pk', filter=Q(vote_position='yes')),
        no=Count('pk', filter=Q(vote_position='no')),
        abstain=Count('pk', filter=Q(vote_position='abstain')),
        total=Count('pk'),
    )

    crumbs = [
        {'label': 'Home', 'url': '/'},
        {'label': 'Countries', 'url': '/country/'},
        {'label': country.display_name, 'url': None},
    ]

    wc_parts = [f'country_id={country.pk}']
    if current_session:
        wc_parts.append(f'session={current_session}')
    if current_body:
        wc_parts.append(f'body={current_body}')
    wc_url = '/api/wordcloud/?' + '&'.join(wc_parts)

    votes_api_parts = []
    if current_session:
        votes_api_parts.append(f'session={current_session}')
    if current_body:
        votes_api_parts.append(f'body={current_body}')
    votes_api_url = f'/votes/api/{country.iso3}/'
    if votes_api_parts:
        votes_api_url += '?' + '&'.join(votes_api_parts)

    return render(request, 'countries/detail.html', {
        'country': country,
        'representatives_page': representatives_page,
        'speeches_page': speeches_page,
        'vote_stats': vote_stats,
        'sessions': sessions,
        'current_session': current_session,
        'current_body': current_body,
        'crumbs': crumbs,
        'wc_url': wc_url,
        'votes_api_url': votes_api_url,
    })


def country_list(request):
    countries = Country.objects.filter(iso3__isnull=False).order_by('name')
    return render(request, 'countries/list.html', {'countries': countries})


def country_detail(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)
    return _render_country_detail(request, country)


def country_detail_by_id(request, pk):
    country = get_object_or_404(Country, pk=pk)
    if country.iso3:
        return redirect('countries:detail', iso3=country.iso3)
    return _render_country_detail(request, country)
