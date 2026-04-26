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

    # Ideal point time series — re-centred by yearly global mean so 0 = world
    # average that year (removes the IRT anchor effect where USA is pinned at 0).
    ideal_points_json = '[]'
    consistency_stats = None
    if country.iso3:
        with connection.cursor() as cur:
            cur.execute(
                '''SELECT ip.year, ip.ideal_point, ip.se, m.mean_ip
                   FROM canonical_ideal_points_norm ip
                   JOIN (
                       SELECT year, AVG(ideal_point) AS mean_ip
                       FROM canonical_ideal_points_norm
                       WHERE ideal_point IS NOT NULL
                       GROUP BY year
                   ) m ON m.year = ip.year
                   WHERE ip.iso3 = %s
                   ORDER BY ip.year''',
                [country.iso3],
            )
            ideal_points_json = json.dumps([
                {
                    'year':  row[0],
                    'point': round(float(row[1]) - float(row[3]), 4),
                    'se':    round(float(row[2]), 4) if row[2] is not None else None,
                }
                for row in cur.fetchall()
            ])

            # Consistency: std dev of re-centred ideal point + global percentile
            cur.execute("""
                WITH cs AS (
                    SELECT ip.iso3,
                           STDDEV(ip.ideal_point - m.mean_ip) AS stddev_ip
                    FROM canonical_ideal_points_norm ip
                    JOIN (
                        SELECT year, AVG(ideal_point) AS mean_ip
                        FROM canonical_ideal_points_norm
                        WHERE ideal_point IS NOT NULL
                        GROUP BY year
                    ) m ON m.year = ip.year
                    WHERE ip.ideal_point IS NOT NULL
                    GROUP BY ip.iso3
                    HAVING COUNT(*) >= 10
                ),
                ranked AS (
                    SELECT iso3, stddev_ip,
                           ROUND(PERCENT_RANK() OVER (ORDER BY stddev_ip DESC) * 100)::int AS pct,
                           COUNT(*) OVER () AS n
                    FROM cs
                )
                SELECT stddev_ip, pct, n FROM ranked WHERE iso3 = %s
            """, [country.iso3])
            row = cur.fetchone()
        if row:
            consistency_stats = {
                'stddev': round(float(row[0]), 2),
                'pct':    int(row[1]),
                'n':      int(row[2]),
            }

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

    # All-time most/least aligned countries (weighted avg over country_alignment_series)
    similar_most = []
    similar_least = []
    if country.iso3:
        _alignment_sql = """
            SELECT c.iso3, COALESCE(c.short_name, c.name) AS label,
                   SUM(cas.agreement_rate * cas.n_votes) / SUM(cas.n_votes) AS rate
            FROM country_alignment_series cas
            JOIN countries c ON (
                CASE WHEN cas.country_id_a = %s THEN cas.country_id_b
                     ELSE cas.country_id_a END = c.id
            )
            WHERE (cas.country_id_a = %s OR cas.country_id_b = %s)
              AND cas.n_votes >= 5
              AND c.iso3 IS NOT NULL
            GROUP BY c.iso3, c.short_name, c.name
            HAVING SUM(cas.n_votes) >= 50
            ORDER BY rate {order}
            LIMIT 5
        """
        with connection.cursor() as cur:
            cur.execute(_alignment_sql.format(order='DESC'),
                        [country.pk, country.pk, country.pk])
            similar_most = [
                {'iso3': r[0], 'name': r[1], 'rate': round(r[2] * 100, 1)}
                for r in cur.fetchall()
            ]
            cur.execute(_alignment_sql.format(order='ASC'),
                        [country.pk, country.pk, country.pk])
            similar_least = [
                {'iso3': r[0], 'name': r[1], 'rate': round(r[2] * 100, 1)}
                for r in cur.fetchall()
            ]

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
        'similar_most':         similar_most,
        'similar_least':        similar_least,
        'consistency_stats':    consistency_stats,
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
