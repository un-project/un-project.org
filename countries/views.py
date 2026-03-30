import json

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Min, Max, Count, Q, F
from .models import Country
from .constants import HISTORICAL_ISO3, HISTORICAL_INFO
from debate.models import GeneralDebateEntry
from speakers.models import Speaker
from speeches.models import Speech
from votes.models import CountryVote


def _render_country_detail(request, country):
    # Representatives — annotated with career year range
    rep_qs = (
        Speaker.objects.filter(country=country)
        .annotate(
            first_year=Min('speeches__document__date__year'),
            last_year=Max('speeches__document__date__year'),
        )
        .order_by('name')
    )
    rep_paginator = Paginator(rep_qs, 20)
    representatives_page = rep_paginator.get_page(request.GET.get('reps_page'))

    # Vote stats (all-time totals)
    vote_stats = (
        CountryVote.objects
        .filter(country=country, vote__document__date__year__gt=1900)
        .aggregate(
            yes=Count('pk', filter=Q(vote_position='yes')),
            no=Count('pk', filter=Q(vote_position='no')),
            abstain=Count('pk', filter=Q(vote_position='abstain')),
            total=Count('pk'),
        )
    )

    # Speech count for stat box
    speech_count = Speech.objects.filter(
        speaker__country=country, document__date__year__gt=1900
    ).count()

    # Speeches by year for the sidebar chart
    speeches_by_year = json.dumps(list(
        Speech.objects.filter(speaker__country=country, document__date__year__gt=1900)
        .values(year=F('document__date__year'), body=F('document__body'))
        .annotate(count=Count('pk'))
        .order_by('year', 'body')
    ))

    reps_by_year = json.dumps(list(
        Speech.objects.filter(speaker__country=country, document__date__year__gt=1900)
        .values(year=F('document__date__year'), body=F('document__body'))
        .annotate(count=Count('speaker_id', distinct=True))
        .order_by('year', 'body')
    ))

    crumbs = [
        {'label': 'Home', 'url': '/'},
        {'label': 'Countries', 'url': '/country/'},
        {'label': country.display_name, 'url': None},
    ]

    wc_url = f'/api/wordcloud/?country_id={country.pk}'
    votes_api_url = f'/votes/api/{country.iso3}/'

    # General Debate entries for this country
    debate_entries = (
        GeneralDebateEntry.objects
        .filter(country=country)
        .select_related('speaker', 'document')
        .order_by('-ga_session', 'meeting_date')
    )

    return render(request, 'countries/detail.html', {
        'country':              country,
        'representatives_page': representatives_page,
        'vote_stats':           vote_stats,
        'speech_count':         speech_count,
        'speeches_by_year':     speeches_by_year,
        'reps_by_year':         reps_by_year,
        'crumbs':               crumbs,
        'wc_url':               wc_url,
        'votes_api_url':        votes_api_url,
        'debate_entries':       debate_entries,
        'historical_info':      HISTORICAL_INFO.get(country.iso3),
    })


def country_list(request):
    qs = Country.objects.filter(iso3__isnull=False).order_by('name')
    current    = qs.exclude(iso3__in=HISTORICAL_ISO3)
    historical = qs.filter(iso3__in=HISTORICAL_ISO3)
    return render(request, 'countries/list.html', {
        'current': current,
        'historical': historical,
    })


def country_detail(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)
    return _render_country_detail(request, country)


def country_detail_by_id(request, pk):
    country = get_object_or_404(Country, pk=pk)
    if country.iso3:
        return redirect('countries:detail', iso3=country.iso3)
    return _render_country_detail(request, country)
