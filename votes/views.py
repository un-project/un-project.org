import json
from collections import defaultdict

from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.http import Http404, JsonResponse
from django.db.models import Count, F, Min, Max

from django.db import connection

from countries.models import Country
from countries.constants import HISTORICAL_ISO3
from .coalitions import COALITIONS, COALITIONS_BY_SLUG
import json as _json
from .models import CountryVote, ISSUE_CODES, Resolution, ResolutionCitation, ResolutionSponsor, Veto, VetoCountry, Vote

ISSUE_CODES_JSON = _json.dumps([
    {'code': code, 'short': short, 'long': long}
    for code, short, long in ISSUE_CODES
])


def voting_map(request):
    countries = (
        Country.objects.filter(country_votes__isnull=False, iso3__isnull=False)
        .distinct().order_by('name')
    )
    countries_json = json.dumps([
        {'iso3': c.iso3, 'name': c.display_name} for c in countries
    ])
    categories = (
        Resolution.objects.exclude(category__isnull=True).exclude(category='')
        .values_list('category', flat=True).distinct().order_by('category')
    )
    year_range = (
        Resolution.objects.aggregate(min_year=Min('votes__document__date__year'),
                                     max_year=Max('votes__document__date__year'))
    )
    historical_iso3_json = json.dumps(sorted(HISTORICAL_ISO3))
    return render(request, 'votes/map.html', {
        'countries': countries,
        'countries_json': countries_json,
        'historical_iso3_json': historical_iso3_json,
        'categories': list(categories),
        'year_min': year_range['min_year'] or 1946,
        'year_max': year_range['max_year'] or 2024,
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Votes', 'url': '/votes/'},
            {'label': 'Voting Similarity Map', 'url': None},
        ],
    })


def resolution_list(request):
    body           = request.GET.get('body', '')
    session        = request.GET.get('session', '')
    year           = request.GET.get('year', '')
    category       = request.GET.get('category', '')
    important_only = request.GET.get('important', '') == '1'
    issue          = request.GET.get('issue', '')
    sponsor        = request.GET.get('sponsor', '')
    q              = request.GET.get('q', '').strip()
    valid_issues   = {code for code, _s, _l in ISSUE_CODES}

    qs = Resolution.objects.all()
    if body in ('GA', 'SC'):
        qs = qs.filter(body=body)
    if session and session.isdigit():
        qs = qs.filter(session=int(session))
    if year and year.isdigit():
        qs = qs.filter(votes__document__date__year=int(year)).distinct()
    if category:
        qs = qs.filter(category=category)
    if important_only:
        qs = qs.filter(important_vote=True)
    # Voeten issue codes only exist for GA resolutions
    if body != 'SC' and issue in valid_issues:
        qs = qs.filter(**{f'issue_{issue}': True})
    else:
        issue = ''
    # Sponsor filter: SC-only data from UNBench
    if body == 'SC' and sponsor:
        qs = qs.filter(sponsors__country__iso3=sponsor).distinct()
    else:
        sponsor = ''
    # Text search across title and symbol
    if q:
        from django.db.models import Q as DQ
        qs = qs.filter(
            DQ(title__icontains=q) |
            DQ(adopted_symbol__icontains=q) |
            DQ(draft_symbol__icontains=q)
        ).distinct()

    # Base queryset for sidebar (body-filtered only)
    filter_qs = Resolution.objects.all()
    if body in ('GA', 'SC'):
        filter_qs = filter_qs.filter(body=body)

    # Years sidebar: filtered to current session if one is selected
    year_qs = filter_qs.filter(votes__document__date__isnull=False)
    if session and session.isdigit():
        year_qs = year_qs.filter(session=int(session))
    years = (
        year_qs
        .values_list('votes__document__date__year', flat=True)
        .distinct()
        .order_by('-votes__document__date__year')
    )

    # Sessions sidebar: filtered to current year if one is selected
    session_qs = filter_qs
    if year and year.isdigit():
        session_qs = session_qs.filter(votes__document__date__year=int(year))
    session_rows = (
        session_qs
        .filter(session__isnull=False, votes__document__date__isnull=False)
        .values('session')
        .annotate(year_min=Min('votes__document__date__year'),
                  year_max=Max('votes__document__date__year'))
        .order_by('-session')
    )
    sessions = [
        {
            'session': row['session'],
            'label': (
                str(row['year_min']) if row['year_min'] == row['year_max']
                else f"{row['year_min']}–{row['year_max']}"
            ),
        }
        for row in session_rows
    ]

    # Category sidebar: counts scoped to body filter only
    categories = list(
        filter_qs
        .exclude(category__isnull=True).exclude(category='')
        .values('category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    important_count = filter_qs.filter(important_vote=True).count()

    # Voeten issue codes only exist for GA; omit sidebar entirely for SC
    issue_sidebar = [] if body == 'SC' else [
        {
            'code':  code,
            'short': short,
            'long':  long,
            'count': filter_qs.filter(**{f'issue_{code}': True}).count(),
        }
        for code, short, long in ISSUE_CODES
    ]

    # Sponsor sidebar: SC-only (UNBench data); top 30 by sponsorship count
    sponsor_sidebar = []
    if body == 'SC':
        sponsor_sidebar = list(
            ResolutionSponsor.objects
            .filter(resolution__body='SC', country__isnull=False)
            .values('country__iso3', 'country__short_name', 'country__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:30]
        )

    paginator = Paginator(qs.order_by('-session', '-adopted_symbol', '-draft_symbol'), 50)
    page = paginator.get_page(request.GET.get('page'))

    # P5 votes for the current page — one extra query for up to 50 resolutions
    page_ids = [r.pk for r in page]
    p5_rows = (
        CountryVote.objects
        .filter(vote__resolution_id__in=page_ids, country__iso3__in=P5_ISO3)
        .values('vote__resolution_id', 'country__iso3', 'vote_position')
    )
    p5_by_resolution = {}
    for row in p5_rows:
        p5_by_resolution.setdefault(row['vote__resolution_id'], {})[row['country__iso3']] = row['vote_position']

    return render(request, 'votes/resolutions.html', {
        'page':               page,
        'sessions':           sessions,
        'years':              years,
        'categories':         categories,
        'important_count':    important_count,
        'issue_sidebar':      issue_sidebar,
        'sponsor_sidebar':    sponsor_sidebar,
        'current_body':       body,
        'current_session':    session,
        'current_year':       year,
        'current_category':   category,
        'current_important':  important_only,
        'current_issue':      issue if issue in valid_issues else '',
        'current_sponsor':    sponsor,
        'current_q':          q,
        'p5_by_resolution':   p5_by_resolution,
        'P5':                 P5,
    })


def resolution_detail(request, slug):
    resolution = None
    for r in Resolution.objects.all():
        if r.slug == slug:
            resolution = r
            break
    if resolution is None:
        raise Http404('Resolution not found')

    votes = (
        resolution.votes
        .select_related('document')
        .prefetch_related('country_votes__country')
        .order_by('-document__date', 'position_in_item')
    )

    # Citations: what this resolution cites
    CITATION_CAP = 20
    outgoing_qs = (
        ResolutionCitation.objects
        .filter(citing=resolution)
        .select_related('cited')
        .order_by('cited_symbol')
    )
    outgoing_total = outgoing_qs.count()
    outgoing = outgoing_qs[:CITATION_CAP]

    # Cited by: what cites this resolution
    incoming_qs = (
        ResolutionCitation.objects
        .filter(cited=resolution)
        .select_related('citing')
        .order_by('citing__adopted_symbol', 'citing__draft_symbol')
    )
    incoming_total = incoming_qs.count()
    incoming = incoming_qs[:CITATION_CAP]

    # Related resolutions: most co-cited alongside this one
    related = []
    if resolution.pk:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT rc2.cited_id, COUNT(*) AS common_parents
                FROM resolution_citations rc1
                JOIN resolution_citations rc2
                  ON rc1.citing_id = rc2.citing_id
                WHERE rc1.cited_id = %s
                  AND rc2.cited_id IS NOT NULL
                  AND rc2.cited_id != %s
                GROUP BY rc2.cited_id
                ORDER BY common_parents DESC
                LIMIT 5
            """, [resolution.pk, resolution.pk])
            rows = cursor.fetchall()
        if rows:
            ids_ordered = [row[0] for row in rows]
            counts_map = {row[0]: row[1] for row in rows}
            related_qs = Resolution.objects.filter(pk__in=ids_ordered)
            related_map = {r.pk: r for r in related_qs}
            related = [
                {'resolution': related_map[rid], 'common': counts_map[rid]}
                for rid in ids_ordered
                if rid in related_map
            ]

    has_citations = outgoing_total > 0 or incoming_total > 0

    sponsors = list(
        resolution.sponsors.select_related('country').order_by('country_name')
    )

    # P5 positions — extracted from the already-prefetched country_votes
    p5_votes = {}
    for vote in votes:
        for cv in vote.country_votes.all():
            if cv.country and cv.country.iso3 in P5_ISO3:
                p5_votes[cv.country.iso3] = cv.vote_position

    return render(request, 'votes/resolution.html', {
        'resolution': resolution,
        'votes':      votes,
        'p5_votes':   p5_votes,
        'P5':         P5,
        'outgoing': outgoing,
        'outgoing_total': outgoing_total,
        'incoming': incoming,
        'incoming_total': incoming_total,
        'related': related,
        'has_citations': has_citations,
        'CITATION_CAP': CITATION_CAP,
        'sponsors': sponsors,
    })


def citation_network(request, slug):
    resolution = None
    for r in Resolution.objects.all():
        if r.slug == slug:
            resolution = r
            break
    if resolution is None:
        raise Http404('Resolution not found')

    return render(request, 'votes/citation_network.html', {
        'resolution': resolution,
        'api_url': f'/api/resolutions/{slug}/citations/',
    })


def _resolve_compare_entity(entity_type, value):
    """
    Resolve a selector (type + value) to a display entity dict, or None.
    Returns dict with: type, name, iso3, slug, flag_url, url, iso3_list
    """
    if entity_type == 'bloc':
        bloc = COALITIONS_BY_SLUG.get(value)
        if not bloc:
            return None
        return {
            'type': 'bloc',
            'name': bloc['name'],
            'label': bloc['label'],
            'iso3': None,
            'slug': bloc['slug'],
            'flag_url': None,
            'url': f"/votes/bloc/{bloc['slug']}/",
            'iso3_list': bloc['iso3'],
            'member_count': len(bloc['iso3']),
        }
    else:
        iso3 = value.upper()
        country = Country.objects.filter(iso3=iso3).first()
        if not country:
            return None
        return {
            'type': 'country',
            'name': country.display_name,
            'label': None,
            'iso3': iso3,
            'slug': None,
            'flag_url': country.flag_url,
            'url': country.get_absolute_url(),
            'iso3_list': [iso3],
            'member_count': None,
        }


def _get_entity_vote_positions(entity):
    """
    Return {vote_id: position} for an entity.
    For a country: each vote has exactly one position.
    For a bloc: plurality position among members on each vote.
    """
    if entity['type'] == 'country':
        return dict(
            CountryVote.objects
            .filter(country__iso3=entity['iso3'], vote__document__date__year__gt=1900)
            .exclude(vote_position='absent')
            .values_list('vote_id', 'vote_position')
        )
    else:
        # Bloc: compute plurality position per vote
        rows = (
            CountryVote.objects
            .filter(country__iso3__in=entity['iso3_list'],
                    vote__document__date__year__gt=1900)
            .exclude(vote_position='absent')
            .values('vote_id', 'vote_position')
            .annotate(n=Count('id'))
            .order_by('vote_id', '-n')
        )
        # First row per vote_id is plurality (ordered by -n)
        positions = {}
        for row in rows:
            if row['vote_id'] not in positions:
                positions[row['vote_id']] = row['vote_position']
        return positions


def country_compare(request):
    a_type = request.GET.get('a_type', 'country')
    b_type = request.GET.get('b_type', 'country')
    a_val  = request.GET.get('a', '').strip()
    b_val  = request.GET.get('b', '').strip()
    try:
        selected_year = int(request.GET.get('year', ''))
    except (ValueError, TypeError):
        selected_year = None

    countries = (
        Country.objects.filter(country_votes__isnull=False, iso3__isnull=False)
        .distinct().order_by('name')
    )

    entity_a = entity_b = comparison = None

    if a_val and b_val:
        entity_a = _resolve_compare_entity(a_type, a_val)
        entity_b = _resolve_compare_entity(b_type, b_val)
        # prevent comparing an entity with itself
        if entity_a and entity_b and entity_a['name'] == entity_b['name']:
            entity_b = None

    if entity_a and entity_b:
        POSITIONS = ['yes', 'no', 'abstain']

        votes_a = _get_entity_vote_positions(entity_a)
        votes_b = _get_entity_vote_positions(entity_b)

        shared_ids = set(votes_a) & set(votes_b)
        total = len(shared_ids)

        agree_count = sum(1 for vid in shared_ids if votes_a[vid] == votes_b[vid])
        agreement_rate = round(100 * agree_count / total) if total else 0

        # Position cross-matrix
        matrix = {pa: {pb: 0 for pb in POSITIONS} for pa in POSITIONS}
        for vid in shared_ids:
            pa, pb = votes_a[vid], votes_b[vid]
            if pa in matrix and pb in matrix[pa]:
                matrix[pa][pb] += 1

        # Agreement by year
        shared_vote_qs = (
            Vote.objects
            .filter(id__in=shared_ids)
            .select_related('resolution', 'document')
        )
        year_stats = defaultdict(lambda: {'agree': 0, 'total': 0})
        vote_map = {}
        for v in shared_vote_qs:
            vote_map[v.id] = v
            if not v.document.date:
                continue
            year = v.document.date.year
            year_stats[year]['total'] += 1
            if votes_a[v.id] == votes_b[v.id]:
                year_stats[year]['agree'] += 1

        by_session = sorted([
            {
                'year': year,
                'total': stats['total'],
                'agree': stats['agree'],
                'rate': round(100 * stats['agree'] / stats['total']) if stats['total'] else 0,
            }
            for year, stats in year_stats.items()
            if stats['total'] >= 2
        ], key=lambda x: x['year'])

        # Votes filtered to selected year
        year_votes = None
        if selected_year and selected_year in year_stats:
            year_rows = [
                {
                    'vote': vote_map[vid],
                    'pos_a': votes_a[vid],
                    'pos_b': votes_b[vid],
                    'agree': votes_a[vid] == votes_b[vid],
                }
                for vid in shared_ids
                if vid in vote_map
                and vote_map[vid].document.date
                and vote_map[vid].document.date.year == selected_year
            ]
            year_rows.sort(key=lambda x: (x['agree'], str(x['vote'].resolution)))
            year_votes = year_rows

        # Most divergent votes (disagreed, sorted by contestedness)
        divergent = [
            {'vote': vote_map[vid], 'pos_a': votes_a[vid], 'pos_b': votes_b[vid]}
            for vid in shared_ids
            if votes_a[vid] != votes_b[vid] and vid in vote_map
        ]
        divergent.sort(key=lambda x: -(x['vote'].no_count or 0))
        divergent = divergent[:12]

        # Rare agreements on contested votes (no_count > 10, both same)
        agreed_contested = [
            {'vote': vote_map[vid], 'position': votes_a[vid]}
            for vid in shared_ids
            if votes_a[vid] == votes_b[vid] and vid in vote_map
            and (vote_map[vid].no_count or 0) > 10
        ]
        agreed_contested.sort(key=lambda x: -(x['vote'].no_count or 0))
        agreed_contested = agreed_contested[:8]

        # Agreement breakdown by Voeten issue code
        by_issue = []
        for code, short, long in ISSUE_CODES:
            field = f'issue_{code}'
            ids = [vid for vid in shared_ids if vid in vote_map and getattr(vote_map[vid].resolution, field)]
            if len(ids) < 2:
                continue
            n_agree = sum(1 for vid in ids if votes_a[vid] == votes_b[vid])
            by_issue.append({
                'code':  code,
                'short': short,
                'long':  long,
                'total': len(ids),
                'agree': n_agree,
                'rate':  round(100 * n_agree / len(ids)),
            })

        # Restructure matrix as a list of rows for template rendering
        matrix_rows = [
            {
                'pos': pa,
                'cells': [
                    {'pos': pb, 'count': matrix[pa][pb], 'same': pa == pb}
                    for pb in POSITIONS
                ],
            }
            for pa in POSITIONS
        ]

        comparison = {
            'total': total,
            'agree_count': agree_count,
            'disagree_count': total - agree_count,
            'agreement_rate': agreement_rate,
            'matrix_rows': matrix_rows,
            'matrix_positions': POSITIONS,
            'by_session': by_session,
            'by_session_json': json.dumps(by_session),
            'by_issue': by_issue,
            'divergent': divergent,
            'agreed_contested': agreed_contested,
            'year_votes': year_votes,
            'selected_year': selected_year,
        }

    return render(request, 'votes/compare.html', {
        'countries':   countries,
        'blocs':       COALITIONS,
        'entity_a':    entity_a,
        'entity_b':    entity_b,
        'a_type':      a_type,
        'b_type':      b_type,
        'a_val':       a_val,
        'b_val':       b_val,
        'comparison':  comparison,
        'selected_year': selected_year,
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'Compare'},
        ],
    })


def votes_page(request):
    ctx = cache.get('votes_page_ctx')
    if ctx is None:
        # Summary counts
        total_resolutions = Resolution.objects.filter(votes__vote_type='recorded').distinct().count()
        total_recorded_votes = Vote.objects.filter(vote_type='recorded', yes_count__isnull=False).count()
        total_country_votes = CountryVote.objects.count()

        # Overall position breakdown
        pos_counts = {
            p['vote_position']: p['n']
            for p in CountryVote.objects.values('vote_position').annotate(n=Count('id'))
        }
        present_total = (
            pos_counts.get('yes', 0) + pos_counts.get('no', 0) + pos_counts.get('abstain', 0)
        )
        yes_pct     = round(100 * pos_counts.get('yes', 0)     / present_total) if present_total else 0
        no_pct      = round(100 * pos_counts.get('no', 0)      / present_total) if present_total else 0
        abstain_pct = round(100 * pos_counts.get('abstain', 0) / present_total) if present_total else 0

        # Most contested (highest no_count)
        most_contested = list(
            Vote.objects
            .filter(vote_type='recorded', no_count__isnull=False, no_count__gt=0,
                    document__date__year__gt=1900)
            .select_related('resolution', 'document')
            .order_by('-no_count')[:6]
        )

        # Voting blocs — ONE query for all coalitions instead of one per bloc
        countries_by_iso3 = {
            c.iso3: c
            for c in Country.objects.filter(iso3__isnull=False).exclude(iso3='')
        }
        all_bloc_iso3s = {iso3 for bloc in COALITIONS for iso3 in bloc['iso3']}
        # Fetch position counts per-country in a single query
        iso3_pos = defaultdict(lambda: defaultdict(int))
        for row in (
            CountryVote.objects
            .filter(country__iso3__in=all_bloc_iso3s)
            .exclude(vote_position='absent')
            .values('country__iso3', 'vote_position')
            .annotate(n=Count('id'))
        ):
            iso3_pos[row['country__iso3']][row['vote_position']] += row['n']

        coalition_blocs = []
        for bloc in COALITIONS:
            pc = defaultdict(int)
            for iso3 in bloc['iso3']:
                for pos, n in iso3_pos[iso3].items():
                    pc[pos] += n
            total = sum(pc.values())
            members = [countries_by_iso3[iso3] for iso3 in bloc['iso3'] if iso3 in countries_by_iso3]
            coalition_blocs.append({
                'name': bloc['name'],
                'slug': bloc.get('slug', ''),
                'label': bloc['label'],
                'members': members,
                'members_extra': max(0, len(members) - 8),
                'yes_pct':     round(100 * pc.get('yes',     0) / total) if total else 0,
                'no_pct':      round(100 * pc.get('no',      0) / total) if total else 0,
                'abstain_pct': round(100 * pc.get('abstain', 0) / total) if total else 0,
            })

        # Most recent votes
        recent_votes = list(
            Vote.objects
            .filter(vote_type='recorded', yes_count__isnull=False,
                    document__date__year__gt=1900)
            .select_related('resolution', 'document')
            .order_by('-document__date')[:8]
        )

        # Countries casting the most No votes
        top_no_voters = list(
            CountryVote.objects
            .filter(vote_position='no')
            .values('country__name', 'country__iso3', 'country__short_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:8]
        )

        # Countries voting Yes most on non-adopted resolutions
        top_yes_on_rejected = list(
            CountryVote.objects
            .filter(
                vote_position='yes',
                vote__vote_type='recorded',
                vote__resolution__adopted_symbol__isnull=True,
            )
            .values('country__name', 'country__iso3', 'country__short_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:8]
        )

        ctx = {
            'coalition_blocs':      coalition_blocs,
            'total_resolutions':    total_resolutions,
            'total_recorded_votes': total_recorded_votes,
            'total_country_votes':  total_country_votes,
            'yes_pct':              yes_pct,
            'no_pct':               no_pct,
            'abstain_pct':          abstain_pct,
            'most_contested':       most_contested,
            'recent_votes':         recent_votes,
            'top_no_voters':        top_no_voters,
            'top_yes_on_rejected':  top_yes_on_rejected,
        }
        cache.set('votes_page_ctx', ctx, 4 * 3600)

    return render(request, 'votes/index.html', {
        **ctx,
    })


def voting_blocs_page(request):
    ctx = cache.get('votes_page_ctx')
    coalition_blocs = ctx['coalition_blocs'] if ctx else None

    if coalition_blocs is None:
        countries_by_iso3 = {
            c.iso3: c
            for c in Country.objects.filter(iso3__isnull=False).exclude(iso3='')
        }
        all_bloc_iso3s = {iso3 for bloc in COALITIONS for iso3 in bloc['iso3']}
        iso3_pos = defaultdict(lambda: defaultdict(int))
        for row in (
            CountryVote.objects
            .filter(country__iso3__in=all_bloc_iso3s)
            .exclude(vote_position='absent')
            .values('country__iso3', 'vote_position')
            .annotate(n=Count('id'))
        ):
            iso3_pos[row['country__iso3']][row['vote_position']] += row['n']

        coalition_blocs = []
        for bloc in COALITIONS:
            pc = defaultdict(int)
            for iso3 in bloc['iso3']:
                for pos, n in iso3_pos[iso3].items():
                    pc[pos] += n
            total = sum(pc.values())
            members = [countries_by_iso3[iso3] for iso3 in bloc['iso3'] if iso3 in countries_by_iso3]
            coalition_blocs.append({
                'name': bloc['name'],
                'slug': bloc.get('slug', ''),
                'label': bloc['label'],
                'members': members,
                'members_extra': max(0, len(members) - 8),
                'yes_pct':     round(100 * pc.get('yes',     0) / total) if total else 0,
                'no_pct':      round(100 * pc.get('no',      0) / total) if total else 0,
                'abstain_pct': round(100 * pc.get('abstain', 0) / total) if total else 0,
            })

    return render(request, 'votes/blocs.html', {
        'coalition_blocs': coalition_blocs,
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'Voting Blocs'},
        ],
    })


def _doc_slug(symbol):
    import re
    s = symbol.replace('/', '-').replace('.', '-')
    s = re.sub(r'[^-a-zA-Z0-9_]', '-', s)
    return re.sub(r'-{2,}', '-', s).strip('-')


def country_votes_json(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)
    session_param = request.GET.get('session', '')
    try:
        session = int(session_param) if session_param else None
    except ValueError:
        session = None
    body_param = request.GET.get('body', '')
    body = body_param if body_param in ('GA', 'SC') else None

    cache_key = f'country_votes_json_{country.pk}_{session}_{body}'
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse(cached)

    qs = (
        CountryVote.objects
        .filter(country=country, vote__document__date__year__gt=1900)
        .order_by('-vote__document__date')
    )
    if session:
        qs = qs.filter(vote__document__session=session)
    if body:
        qs = qs.filter(vote__document__body=body)

    _ISSUE_FIELDS = [c for c, _s, _l in ISSUE_CODES]
    records = []
    for row in qs.values(
        'pk', 'vote_position',
        'vote__yes_count', 'vote__no_count', 'vote__abstain_count',
        'vote__document__date', 'vote__document__symbol',
        'vote__resolution__session', 'vote__resolution__category',
        'vote__resolution__title', 'vote__resolution__adopted_symbol',
        'vote__resolution__draft_symbol',
        *[f'vote__resolution__issue_{c}' for c in _ISSUE_FIELDS],
    ):
        date = row['vote__document__date']
        res_symbol = row['vote__resolution__adopted_symbol'] or row['vote__resolution__draft_symbol'] or ''
        doc_symbol = row['vote__document__symbol']
        records.append({
            'id': row['pk'],
            'position': row['vote_position'],
            'year': date.year if date else None,
            'date': date.isoformat() if date else '',
            'session': row['vote__resolution__session'],
            'category': row['vote__resolution__category'] or 'Uncategorized',
            'issues': [c for c in _ISSUE_FIELDS if row[f'vote__resolution__issue_{c}']],
            'resolution': res_symbol,
            'title': (row['vote__resolution__title'] or '')[:120],
            'yes_count': row['vote__yes_count'],
            'no_count': row['vote__no_count'],
            'abstain_count': row['vote__abstain_count'],
            'document': doc_symbol,
            'document_url': f'/meeting/{_doc_slug(doc_symbol)}/',
            'resolution_url': f'/votes/resolutions/{res_symbol.replace("/", "-").replace(".", "-")}/',
        })

    payload = {'country': country.name, 'iso3': iso3, 'votes': records}
    cache.set(cache_key, payload, 3600)
    return JsonResponse(payload)


def _compute_similarity(request, country):
    """Compute voting similarity scores for a country. Returns a JsonResponse."""
    MIN_SHARED = 10

    year_from = request.GET.get('year_from', '')
    year_to   = request.GET.get('year_to', '')
    body      = request.GET.get('body', '')
    category  = request.GET.get('category', '')

    # Build a cache key so identical requests are served without hitting the DB.
    cache_key = (
        f'similarity_{country.pk}_{year_from}_{year_to}_{body}_{category}'
        f'_{request.GET.get("all", "")}'
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse(cached)

    # Score formula: same=1.0, one-step-apart (yes/abstain or abstain/no)=0.5,
    # yes vs no=0.0.  Equivalent to 1 - abs(POS_MAP[a]-POS_MAP[b])/2 where
    # POS_MAP = {yes:1, abstain:2, no:3}.
    extra_joins = ''
    filters = [
        "cv1.country_id = %s",
        "cv2.country_id != %s",
        "cv1.vote_position != 'absent'",
        "cv2.vote_position != 'absent'",
        "d.date > '1900-01-01'",
    ]
    params = [country.pk, country.pk]

    if year_from and year_from.isdigit():
        filters.append("EXTRACT(YEAR FROM d.date) >= %s")
        params.append(int(year_from))
    if year_to and year_to.isdigit():
        filters.append("EXTRACT(YEAR FROM d.date) <= %s")
        params.append(int(year_to))
    if body in ('GA', 'SC'):
        filters.append("d.body = %s")
        params.append(body)
    if category:
        extra_joins = 'JOIN resolutions r ON v.resolution_id = r.id'
        filters.append("r.category = %s")
        params.append(category)

    where = ' AND '.join(filters)
    sql = f"""
        SELECT
            cv2.country_id,
            c.name,
            c.iso3,
            COUNT(*)::int AS shared,
            ROUND(AVG(
                CASE
                    WHEN cv1.vote_position = cv2.vote_position THEN 1.0
                    WHEN cv1.vote_position IN ('yes','no')
                     AND cv2.vote_position IN ('yes','no') THEN 0.0
                    ELSE 0.5
                END
            )::numeric, 3)::float AS score
        FROM country_votes cv1
        JOIN country_votes cv2 ON cv1.vote_id = cv2.vote_id
        JOIN countries c ON cv2.country_id = c.id
        JOIN votes v ON cv1.vote_id = v.id
        JOIN documents d ON v.document_id = d.id
        {extra_joins}
        WHERE {where}
        GROUP BY cv2.country_id, c.name, c.iso3
        HAVING COUNT(*) >= {MIN_SHARED}
        ORDER BY score DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    if not rows:
        payload = {'similar': [], 'dissimilar': [], 'countries': []}
        cache.set(cache_key, payload, 3600)
        return JsonResponse(payload)

    results = [
        {'iso3': row[2] or '', 'name': row[1], 'score': float(row[4]), 'shared': row[3]}
        for row in rows
    ]

    if request.GET.get('all'):
        payload = {'countries': results}
    else:
        payload = {
            'similar': results[:10],
            'dissimilar': list(reversed(results[-10:])),
        }

    cache.set(cache_key, payload, 3600)
    return JsonResponse(payload)


def country_votes_page(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)
    votes_api_url = f'/votes/api/{iso3}/'
    return render(request, 'votes/country_votes.html', {
        'country': country,
        'votes_api_url': votes_api_url,
        'issue_codes_json': ISSUE_CODES_JSON,
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Countries', 'url': '/country/'},
            {'label': country.display_name, 'url': f'/country/{iso3}/'},
            {'label': 'Voting Analysis', 'url': None},
        ],
    })


def country_similarity_json(request, iso3):
    """Return voting similarity scores for a country identified by ISO 3166-1 alpha-3."""
    country = get_object_or_404(Country, iso3=iso3)
    return _compute_similarity(request, country)


def country_similarity_json_by_pk(request, pk):
    """Return voting similarity scores for a country identified by primary key."""
    country = get_object_or_404(Country, pk=pk)
    return _compute_similarity(request, country)


P5 = [
    {'iso3': 'RUS', 'name': 'Russia',         'color': '#B71C1C'},
    {'iso3': 'USA', 'name': 'United States',  'color': '#1565C0'},
    {'iso3': 'GBR', 'name': 'United Kingdom', 'color': '#1A237E'},
    {'iso3': 'CHN', 'name': 'China',          'color': '#E65100'},
    {'iso3': 'FRA', 'name': 'France',         'color': '#6A1B9A'},
]
P5_ISO3 = [p['iso3'] for p in P5]


def veto_list(request):
    filter_iso3 = request.GET.get('country', '')
    if filter_iso3 not in P5_ISO3:
        filter_iso3 = ''

    qs = (
        Veto.objects
        .prefetch_related('veto_countries__country')
        .select_related('document')
        .order_by('-date')
    )
    if filter_iso3:
        qs = qs.filter(vetoing_countries__iso3=filter_iso3)

    # Per-P5 veto counts
    p5_counts = {
        row['country__iso3']: row['n']
        for row in VetoCountry.objects
            .filter(country__iso3__in=P5_ISO3)
            .values('country__iso3')
            .annotate(n=Count('id'))
    }
    p5_data = [
        {**p, 'count': p5_counts.get(p['iso3'], 0)}
        for p in P5
    ]

    # Timeline: vetoes per year per P5 member
    year_counts = defaultdict(lambda: {iso3: 0 for iso3 in P5_ISO3})
    for vc in (VetoCountry.objects
               .filter(country__iso3__in=P5_ISO3)
               .select_related('veto', 'country')
               .filter(veto__date__isnull=False)):
        year_counts[vc.veto.date.year][vc.country.iso3] += 1

    timeline_json = json.dumps([
        {'year': yr, **counts}
        for yr, counts in sorted(year_counts.items())
    ])

    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get('page'))

    # Map draft_symbol → resolution slug for vetoes on this page that have a stub
    page_symbols = {v.draft_symbol for v in page if v.draft_symbol}
    resolution_slugs = {
        r.draft_symbol: r.slug
        for r in Resolution.objects.filter(draft_symbol__in=page_symbols)
    }

    return render(request, 'votes/vetoes.html', {
        'page':             page,
        'P5':               p5_data,
        'P5_json':          json.dumps(P5),
        'timeline_json':    timeline_json,
        'filter_iso3':      filter_iso3,
        'total':            Veto.objects.count(),
        'resolution_slugs': resolution_slugs,
        'crumbs': [
            {'label': 'Home',            'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'SC Vetoes',       'url': None},
        ],
    })


def cohesion_heatmap(request):
    N = 60  # top N countries by votes cast

    with connection.cursor() as cur:
        cur.execute("""
            WITH top AS (
                SELECT cv.country_id, COUNT(*) AS n
                FROM country_votes cv
                WHERE cv.vote_position IN ('yes','no','abstain')
                GROUP BY cv.country_id
                ORDER BY n DESC
                LIMIT %s
            ),
            pairs AS (
                SELECT
                    cv1.country_id AS id_a,
                    cv2.country_id AS id_b,
                    COUNT(*)       AS shared,
                    SUM(CASE WHEN cv1.vote_position = cv2.vote_position THEN 1 ELSE 0 END) AS agree
                FROM country_votes cv1
                JOIN country_votes cv2
                    ON cv1.vote_id = cv2.vote_id
                    AND cv1.country_id < cv2.country_id
                WHERE cv1.vote_position IN ('yes','no','abstain')
                  AND cv2.vote_position IN ('yes','no','abstain')
                  AND cv1.country_id IN (SELECT country_id FROM top)
                  AND cv2.country_id IN (SELECT country_id FROM top)
                GROUP BY cv1.country_id, cv2.country_id
                HAVING COUNT(*) >= 20
            )
            SELECT id_a, id_b, shared, agree,
                   ROUND(100.0 * agree / shared)::int AS rate
            FROM pairs
        """, [N])
        pair_rows = cur.fetchall()

        # Ideal points: mean per country for ordering
        cur.execute("""
            SELECT ip.iso3, AVG(ip.ideal_point) AS mean_ip
            FROM country_ideal_points ip
            WHERE ip.ideal_point IS NOT NULL
            GROUP BY ip.iso3
        """)
        ideal_means = {row[0]: float(row[1]) for row in cur.fetchall()}

        # Country metadata for the top N
        country_ids = set()
        for id_a, id_b, *_ in pair_rows:
            country_ids.add(id_a)
            country_ids.add(id_b)

        if not country_ids:
            return render(request, 'votes/cohesion.html', {
                'matrix_json': '{"countries":[],"cells":[]}',
                'crumbs': [
                    {'label': 'Home', 'url': '/'},
                    {'label': 'Voting Analysis', 'url': '/votes/'},
                    {'label': 'Cohesion Heatmap', 'url': None},
                ],
            })

        cur.execute("""
            SELECT id, COALESCE(short_name, name), iso3
            FROM countries WHERE id = ANY(%s)
        """, [list(country_ids)])
        country_meta = {row[0]: {'name': row[1], 'iso3': row[2] or ''} for row in cur.fetchall()}

    # Sort by ideal point (descending = most Western first), unknowns last
    def sort_key(cid):
        iso3 = country_meta[cid]['iso3']
        ip = ideal_means.get(iso3)
        return (0 if ip is not None else 1, -(ip or 0))

    sorted_ids = sorted(country_ids, key=sort_key)
    idx = {cid: i for i, cid in enumerate(sorted_ids)}

    countries_out = [
        {'idx': idx[cid], 'iso3': country_meta[cid]['iso3'], 'name': country_meta[cid]['name']}
        for cid in sorted_ids
    ]

    # Build symmetric cell list (upper triangle only — JS mirrors it)
    cells = []
    for id_a, id_b, shared, agree, rate in pair_rows:
        cells.append({'a': idx[id_a], 'b': idx[id_b], 'rate': rate, 'shared': int(shared)})

    matrix_json = json.dumps({'countries': countries_out, 'cells': cells})

    return render(request, 'votes/cohesion.html', {
        'matrix_json': matrix_json,
        'country_count': len(sorted_ids),
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'Voting Cohesion Heatmap', 'url': None},
        ],
    })


def ideal_points_lines(request):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(c.short_name, c.name) AS name, c.iso3
            FROM countries c
            WHERE c.iso3 IN (SELECT DISTINCT iso3 FROM country_ideal_points)
            ORDER BY COALESCE(c.short_name, c.name)
        """)
        countries = [{'name': r[0], 'iso3': r[1]} for r in cur.fetchall()]

    return render(request, 'votes/ip_lines.html', {
        'countries_json': json.dumps(countries),
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'Ideal Point Lines', 'url': None},
        ],
    })


def ideal_points_timeline(request):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT ip.iso3, ip.year, ip.ideal_point,
                   COALESCE(c.short_name, c.name) AS label
            FROM country_ideal_points ip
            LEFT JOIN countries c ON c.iso3 = ip.iso3
            WHERE ip.ideal_point IS NOT NULL
            ORDER BY ip.iso3, ip.year
        """)
        rows = cur.fetchall()

    # Group by country
    country_data = {}
    for iso3, year, point, label in rows:
        if iso3 not in country_data:
            country_data[iso3] = {'iso3': iso3, 'name': label or iso3, 'points': {}}
        country_data[iso3]['points'][year] = round(float(point), 3)

    # Keep only countries with ≥10 years of data
    all_years = sorted({year for _, year, _, _ in rows})
    countries = [
        c for c in country_data.values()
        if len(c['points']) >= 10
    ]

    # Sort by mean ideal point descending (most Western at top)
    for c in countries:
        vals = list(c['points'].values())
        c['mean'] = sum(vals) / len(vals)
    countries.sort(key=lambda c: c['mean'], reverse=True)

    # Build flat points array (None for missing years)
    for c in countries:
        c['series'] = [c['points'].get(y) for y in all_years]
        del c['points']
        del c['mean']

    timeline_json = json.dumps({'years': all_years, 'countries': countries})

    return render(request, 'votes/ideal_points.html', {
        'timeline_json': timeline_json,
        'year_min': all_years[0] if all_years else 1946,
        'year_max': all_years[-1] if all_years else 2025,
        'country_count': len(countries),
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'Ideal Point Timeline', 'url': None},
        ],
    })


def vote_predict(request):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(c.short_name, c.name), c.iso3
            FROM countries c
            WHERE c.iso3 IN (SELECT DISTINCT iso3 FROM country_ideal_points)
            ORDER BY COALESCE(c.short_name, c.name)
        """)
        countries = [{'name': r[0], 'iso3': r[1]} for r in cur.fetchall()]

    return render(request, 'votes/predict.html', {
        'countries_json': json.dumps(countries),
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'Vote Prediction', 'url': None},
        ],
    })


def p5_divergence(request):
    P5 = [
        ('USA', 'United States',  '#1a6fa8', 'west'),
        ('GBR', 'United Kingdom', '#2196a0', 'west'),
        ('FRA', 'France',         '#3aab5c', 'west'),
        ('RUS', 'Russia',         '#c0392b', 'east'),
        ('CHN', 'China',          '#e67e22', 'east'),
        ('SUN', 'USSR',           '#922b21', 'east'),
    ]
    iso3s = [r[0] for r in P5]

    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT ip.iso3, ip.year,
                   ip.ideal_point - m.mean_ip AS centred
            FROM country_ideal_points ip
            JOIN (
                SELECT year, AVG(ideal_point) AS mean_ip
                FROM country_ideal_points
                WHERE ideal_point IS NOT NULL
                GROUP BY year
            ) m ON m.year = ip.year
            WHERE ip.iso3 = ANY(%s) AND ip.ideal_point IS NOT NULL
            ORDER BY ip.iso3, ip.year
            """,
            [iso3s],
        )
        rows = cur.fetchall()

    by_iso3 = {}
    for iso3, year, centred in rows:
        by_iso3.setdefault(iso3, []).append({'year': year, 'ip': round(float(centred), 4)})

    series = [
        {'iso3': iso3, 'label': label, 'color': color, 'group': group,
         'points': by_iso3.get(iso3, [])}
        for iso3, label, color, group in P5
    ]

    return render(request, 'votes/p5_divergence.html', {
        'series_json': json.dumps(series),
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'P5 Divergence', 'url': None},
        ],
    })


def bloc_detail(request, slug):
    bloc = COALITIONS_BY_SLUG.get(slug)
    if not bloc:
        raise Http404('Bloc not found')

    iso3_list = bloc['iso3']
    countries_by_iso3 = {
        c.iso3: c
        for c in Country.objects.filter(iso3__in=iso3_list)
    }
    members = [countries_by_iso3[iso3] for iso3 in iso3_list if iso3 in countries_by_iso3]

    # Overall breakdown
    pos_counts = {
        row['vote_position']: row['n']
        for row in (
            CountryVote.objects
            .filter(country__iso3__in=iso3_list)
            .exclude(vote_position='absent')
            .values('vote_position')
            .annotate(n=Count('id'))
        )
    }
    total_pos = sum(pos_counts.values())
    yes_pct     = round(100 * pos_counts.get('yes',     0) / total_pos) if total_pos else 0
    no_pct      = round(100 * pos_counts.get('no',      0) / total_pos) if total_pos else 0
    abstain_pct = round(100 * pos_counts.get('abstain', 0) / total_pos) if total_pos else 0

    # Voting trend by year: yes/no/abstain counts per year
    year_rows = (
        CountryVote.objects
        .filter(country__iso3__in=iso3_list, vote__document__date__year__gt=1900)
        .exclude(vote_position='absent')
        .values('vote__document__date__year', 'vote_position')
        .annotate(n=Count('id'))
        .order_by('vote__document__date__year')
    )
    trend_by_year = {}
    for row in year_rows:
        yr = row['vote__document__date__year']
        if yr not in trend_by_year:
            trend_by_year[yr] = {'year': yr, 'yes': 0, 'no': 0, 'abstain': 0}
        pos = row['vote_position']
        if pos in ('yes', 'no', 'abstain'):
            trend_by_year[yr][pos] = row['n']
    trend_json = json.dumps(sorted(trend_by_year.values(), key=lambda x: x['year']))

    # Cohesion by year: fraction of votes where bloc plurality position matches per year
    # For each vote, find the plurality position among bloc members, then measure agreement
    with connection.cursor() as cursor:
        cursor.execute("""
            WITH vote_positions AS (
                SELECT
                    cv.vote_id,
                    EXTRACT(YEAR FROM d.date)::int AS year,
                    cv.vote_position,
                    COUNT(*) AS cnt
                FROM country_votes cv
                JOIN countries c ON c.id = cv.country_id
                JOIN votes v ON v.id = cv.vote_id
                JOIN documents d ON d.id = v.document_id
                WHERE c.iso3 = ANY(%s)
                  AND cv.vote_position IN ('yes', 'no', 'abstain')
                  AND EXTRACT(YEAR FROM d.date) > 1900
                GROUP BY cv.vote_id, year, cv.vote_position
            ),
            vote_totals AS (
                SELECT vote_id, year, SUM(cnt) AS total_votes
                FROM vote_positions
                GROUP BY vote_id, year
            ),
            vote_plurality AS (
                SELECT DISTINCT ON (vp.vote_id)
                    vp.vote_id,
                    vp.year,
                    vp.cnt AS plurality_cnt,
                    vt.total_votes
                FROM vote_positions vp
                JOIN vote_totals vt ON vt.vote_id = vp.vote_id
                ORDER BY vp.vote_id, vp.cnt DESC
            )
            SELECT year,
                   ROUND(AVG(plurality_cnt::numeric / total_votes) * 100) AS cohesion_pct,
                   COUNT(*) AS vote_count
            FROM vote_plurality
            WHERE total_votes >= 2
            GROUP BY year
            ORDER BY year
        """, [iso3_list])
        cohesion_rows = cursor.fetchall()

    cohesion_json = json.dumps([
        {'year': row[0], 'cohesion': float(row[1]), 'votes': row[2]}
        for row in cohesion_rows
    ])

    # Most divisive votes: votes with highest internal disagreement (lowest cohesion)
    with connection.cursor() as cursor:
        cursor.execute("""
            WITH vote_positions AS (
                SELECT
                    cv.vote_id,
                    cv.vote_position,
                    COUNT(*) AS cnt
                FROM country_votes cv
                JOIN countries c ON c.id = cv.country_id
                WHERE c.iso3 = ANY(%s)
                  AND cv.vote_position IN ('yes', 'no', 'abstain')
                GROUP BY cv.vote_id, cv.vote_position
            ),
            vote_totals AS (
                SELECT vote_id, SUM(cnt) AS total_votes
                FROM vote_positions
                GROUP BY vote_id
            ),
            vote_plurality AS (
                SELECT DISTINCT ON (vp.vote_id)
                    vp.vote_id,
                    vp.cnt AS plurality_cnt,
                    vt.total_votes,
                    vp.cnt::numeric / vt.total_votes AS cohesion
                FROM vote_positions vp
                JOIN vote_totals vt ON vt.vote_id = vp.vote_id
                ORDER BY vp.vote_id, vp.cnt DESC
            )
            SELECT vote_id, cohesion, total_votes
            FROM vote_plurality
            WHERE total_votes >= %s
            ORDER BY cohesion ASC
            LIMIT 8
        """, [iso3_list, max(3, len(members) // 4)])
        divisive_vote_ids = [(row[0], float(row[1]), row[2]) for row in cursor.fetchall()]

    divisive_votes = []
    if divisive_vote_ids:
        vote_map = {v.pk: v for v in Vote.objects.filter(
            pk__in=[r[0] for r in divisive_vote_ids]
        ).select_related('resolution', 'document')}
        for vote_id, cohesion, participating in divisive_vote_ids:
            if vote_id in vote_map:
                divisive_votes.append({
                    'vote': vote_map[vote_id],
                    'cohesion': round(cohesion * 100),
                    'participating': participating,
                })

    # Most agreed contested votes (high no_count AND high internal cohesion)
    with connection.cursor() as cursor:
        cursor.execute("""
            WITH vote_positions AS (
                SELECT
                    cv.vote_id,
                    cv.vote_position,
                    COUNT(*) AS cnt
                FROM country_votes cv
                JOIN countries c ON c.id = cv.country_id
                WHERE c.iso3 = ANY(%s)
                  AND cv.vote_position IN ('yes', 'no', 'abstain')
                GROUP BY cv.vote_id, cv.vote_position
            ),
            vote_totals AS (
                SELECT vote_id, SUM(cnt) AS total_votes
                FROM vote_positions
                GROUP BY vote_id
            ),
            vote_plurality AS (
                SELECT DISTINCT ON (vp.vote_id)
                    vp.vote_id,
                    vp.cnt::numeric / vt.total_votes AS cohesion,
                    vt.total_votes
                FROM vote_positions vp
                JOIN vote_totals vt ON vt.vote_id = vp.vote_id
                ORDER BY vp.vote_id, vp.cnt DESC
            )
            SELECT vp.vote_id, vp.cohesion, v.no_count
            FROM vote_plurality vp
            JOIN votes v ON v.id = vp.vote_id
            WHERE vp.cohesion >= 0.8
              AND v.no_count >= 10
              AND vp.total_votes >= %s
            ORDER BY v.no_count DESC
            LIMIT 8
        """, [iso3_list, max(3, len(members) // 4)])
        contested_rows = cursor.fetchall()

    agreed_contested = []
    if contested_rows:
        cmap = {v.pk: v for v in Vote.objects.filter(
            pk__in=[r[0] for r in contested_rows]
        ).select_related('resolution', 'document')}
        for vote_id, cohesion, no_count in contested_rows:
            if vote_id in cmap:
                agreed_contested.append({
                    'vote': cmap[vote_id],
                    'cohesion': round(float(cohesion) * 100),
                    'no_count': no_count,
                })

    return render(request, 'votes/bloc.html', {
        'bloc': bloc,
        'members': members,
        'yes_pct': yes_pct,
        'no_pct': no_pct,
        'abstain_pct': abstain_pct,
        'trend_json': trend_json,
        'cohesion_json': cohesion_json,
        'divisive_votes': divisive_votes,
        'agreed_contested': agreed_contested,
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': bloc['name'], 'url': None},
        ],
    })


def cosponsor_network_json(request):
    """Return co-sponsorship network as nodes + edges JSON for D3 force graph."""
    TOP_N    = int(request.GET.get('top', 50))
    MIN_EDGE = int(request.GET.get('min_edge', 5))
    TOP_N    = min(max(TOP_N, 10), 100)
    MIN_EDGE = min(max(MIN_EDGE, 1), 50)

    with connection.cursor() as cur:
        # Top N countries by number of co-sponsored resolutions
        cur.execute("""
            SELECT rs.country_id, c.name, c.iso3, COUNT(*) AS total
            FROM resolution_sponsors rs
            JOIN countries c ON c.id = rs.country_id
            WHERE rs.country_id IS NOT NULL
            GROUP BY rs.country_id, c.name, c.iso3
            ORDER BY total DESC
            LIMIT %s
        """, [TOP_N])
        node_rows = cur.fetchall()

    top_ids = {row[0] for row in node_rows}
    nodes = [
        {'id': row[0], 'name': row[1], 'iso3': row[2] or '', 'count': row[3]}
        for row in node_rows
    ]

    with connection.cursor() as cur:
        cur.execute("""
            SELECT a.country_id, b.country_id, COUNT(*) AS weight
            FROM resolution_sponsors a
            JOIN resolution_sponsors b
              ON a.resolution_id = b.resolution_id
             AND a.country_id < b.country_id
            WHERE a.country_id = ANY(%s)
              AND b.country_id = ANY(%s)
            GROUP BY a.country_id, b.country_id
            HAVING COUNT(*) >= %s
            ORDER BY weight DESC
        """, [list(top_ids), list(top_ids), MIN_EDGE])
        edge_rows = cur.fetchall()

    edges = [
        {'source': row[0], 'target': row[1], 'weight': row[2]}
        for row in edge_rows
    ]

    return JsonResponse({'nodes': nodes, 'edges': edges})


def bubble_chart(request):
    return render(request, 'votes/bubble.html', {
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'Animated Bubble Chart', 'url': None},
        ],
    })


def cosponsor_network(request):
    top_n    = int(request.GET.get('top', 50))
    min_edge = int(request.GET.get('min_edge', 5))
    top_n    = min(max(top_n, 10), 100)
    min_edge = min(max(min_edge, 1), 50)

    api_url = f'/votes/api/cosponsor-network/?top={top_n}&min_edge={min_edge}'
    return render(request, 'votes/cosponsor_network.html', {
        'api_url':          api_url,
        'top_n':            top_n,
        'min_edge':         min_edge,
        'top_choices':      [10, 20, 30, 40, 50, 60, 75, 100],
        'min_edge_choices': [1, 3, 5, 10, 15, 20, 30],
        'crumbs': [
            {'label': 'Home',            'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'Co-sponsorship Network', 'url': None},
        ],
    })
