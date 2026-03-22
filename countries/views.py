from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Min, Max, Count, Q
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

    # Representatives — scoped to session when active, annotated with career year range
    rep_qs = Speaker.objects.filter(country=country)
    if current_session:
        rep_qs = rep_qs.filter(speeches__document__session=current_session)
    rep_qs = rep_qs.annotate(
        first_year=Min('speeches__document__date__year'),
        last_year=Max('speeches__document__date__year'),
    ).order_by('name')
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
    speech_qs = (
        Speech.objects.filter(speaker__country=country)
        .select_related('speaker', 'document')
        .order_by('-document__date', '-position_in_document')
    )
    if current_session:
        speech_qs = speech_qs.filter(document__session=current_session)
    paginator = Paginator(speech_qs, getattr(settings, 'SPEECHES_PER_PAGE', 20))
    speeches_page = paginator.get_page(request.GET.get('page'))

    # Vote stats — single aggregate query (filtered by session when active)
    vote_qs = CountryVote.objects.filter(country=country)
    if current_session:
        vote_qs = vote_qs.filter(vote__document__session=current_session)
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

    wc_base = f'/api/wordcloud/?country_id={country.pk}'
    wc_url = f'{wc_base}&session={current_session}' if current_session else wc_base

    return render(request, 'countries/detail.html', {
        'country': country,
        'representatives_page': representatives_page,
        'speeches_page': speeches_page,
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
