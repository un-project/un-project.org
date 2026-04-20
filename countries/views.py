import json

from django.core.cache import cache
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Min, Max, Count, Q, F
from .models import Country
from .constants import HISTORICAL_ISO3, HISTORICAL_INFO
from debate.models import GeneralDebateEntry
from speakers.models import Speaker, SCRepresentative
from speeches.models import Speech
import json as _json
from votes.models import CountryVote, ISSUE_CODES, ResolutionSponsor


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

    # Ideal point time series (Bailey–Strezhnev–Voeten IRT model)
    ideal_points_json = '[]'
    if country.iso3:
        with connection.cursor() as cur:
            cur.execute(
                'SELECT year, ideal_point, se FROM country_ideal_points '
                'WHERE iso3=%s ORDER BY year',
                [country.iso3],
            )
            ideal_points_json = json.dumps([
                {
                    'year':  row[0],
                    'point': round(float(row[1]), 4),
                    'se':    round(float(row[2]), 4) if row[2] is not None else None,
                }
                for row in cur.fetchall()
            ])

    issue_codes_json = _json.dumps([
        {'code': c, 'short': s, 'long': l} for c, s, l in ISSUE_CODES
    ])

    # Co-sponsored SC resolutions (UNBench dataset)
    sponsored_qs = (
        ResolutionSponsor.objects
        .filter(country=country)
        .select_related('resolution')
        .order_by('-resolution__session', 'resolution__draft_symbol')
    )
    sponsored_paginator = Paginator(sponsored_qs, 25)
    sponsored_page = sponsored_paginator.get_page(request.GET.get('sp_page'))
    sponsored_count = sponsored_paginator.count

    wc_url = f'/api/wordcloud/?country_id={country.pk}'
    debate_wc_url = f'/api/wordcloud/?source=debate&country_id={country.pk}'
    votes_api_url = f'/votes/api/{country.iso3}/' if country.iso3 else ''
    has_sc_reps = (
        country.iso3 and
        SCRepresentative.objects.filter(country=country).exists()
    )

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
        'ideal_points_json':    ideal_points_json,
        'wc_url':               wc_url,
        'votes_api_url':        votes_api_url,
        'issue_codes_json':     issue_codes_json,
        'sponsored_page':       sponsored_page,
        'sponsored_count':      sponsored_count,
        'has_sc_reps':          has_sc_reps,
        'debate_entries':       debate_entries,
        'debate_wc_url':        debate_wc_url,
        'historical_info':      HISTORICAL_INFO.get(country.iso3),
    })


def country_list(request):
    cached = cache.get('country_list')
    if cached is None:
        qs = Country.objects.filter(iso3__isnull=False).order_by('name')
        cached = {
            'current':    list(qs.exclude(iso3__in=HISTORICAL_ISO3)),
            'historical': list(qs.filter(iso3__in=HISTORICAL_ISO3)),
        }
        cache.set('country_list', cached, 24 * 3600)
    return render(request, 'countries/list.html', cached)


def country_detail(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)
    return _render_country_detail(request, country)


def country_detail_by_id(request, pk):
    country = get_object_or_404(Country, pk=pk)
    if country.iso3:
        return redirect('countries:detail', iso3=country.iso3)
    return _render_country_detail(request, country)
