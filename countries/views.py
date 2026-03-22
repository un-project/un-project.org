from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.conf import settings
from .models import Country
from speakers.models import Speaker
from speeches.models import Speech
from votes.models import CountryVote


def _render_country_detail(request, country):
    # Session filter
    session_param = request.GET.get('session', '')
    try:
        current_session = int(session_param) if session_param else None
    except ValueError:
        current_session = None

    # Representatives — scoped to session when active
    rep_qs = Speaker.objects.filter(country=country)
    if current_session:
        rep_qs = rep_qs.filter(speeches__document__session=current_session).distinct()
    rep_qs = rep_qs.order_by('name')
    rep_paginator = Paginator(rep_qs, 20)
    representatives_page = rep_paginator.get_page(request.GET.get('reps_page'))

    # Available sessions (union of speech sessions and vote sessions, descending)
    speech_sessions = set(
        Speech.objects.filter(speaker__country=country)
        .values_list('document__session', flat=True)
        .distinct()
    )
    vote_sessions = set(
        CountryVote.objects.filter(country=country)
        .values_list('vote__document__session', flat=True)
        .distinct()
    )
    sessions = sorted(speech_sessions | vote_sessions, reverse=True)

    # Speeches (filtered by session when active)
    recent_speeches = (
        Speech.objects.filter(speaker__country=country)
        .select_related('speaker', 'document')
        .order_by('-document__date', '-position_in_document')
    )
    if current_session:
        recent_speeches = recent_speeches.filter(document__session=current_session)
    paginator = Paginator(recent_speeches, getattr(settings, 'SPEECHES_PER_PAGE', 20))
    speeches_page = paginator.get_page(request.GET.get('page'))

    # Voting history (filtered by session when active)
    voting_history = (
        CountryVote.objects.filter(country=country)
        .select_related('vote__resolution', 'vote__document')
        .order_by('-vote__document__date')
    )
    if current_session:
        voting_history = voting_history.filter(vote__document__session=current_session)
    votes_paginator = Paginator(voting_history, 25)
    voting_history_page = votes_paginator.get_page(request.GET.get('votes_page'))

    # Vote stats (filtered by session when active)
    vote_qs = CountryVote.objects.filter(country=country)
    if current_session:
        vote_qs = vote_qs.filter(vote__document__session=current_session)
    vote_stats = {
        'yes':     vote_qs.filter(vote_position='yes').count(),
        'no':      vote_qs.filter(vote_position='no').count(),
        'abstain': vote_qs.filter(vote_position='abstain').count(),
    }

    crumbs = [
        {'label': 'Home', 'url': '/'},
        {'label': country.display_name, 'url': None},
    ]

    wc_base = f'/api/wordcloud/?country_id={country.pk}'
    wc_url = f'{wc_base}&session={current_session}' if current_session else wc_base

    return render(request, 'countries/detail.html', {
        'country': country,
        'representatives_page': representatives_page,
        'speeches_page': speeches_page,
        'voting_history_page': voting_history_page,
        'vote_stats': vote_stats,
        'sessions': sessions,
        'current_session': current_session,
        'crumbs': crumbs,
        'wc_url': wc_url,
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
