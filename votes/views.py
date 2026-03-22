from collections import defaultdict

from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.http import Http404, JsonResponse
from django.db.models import Count, F

from countries.models import Country
from .models import CountryVote, Resolution, Vote


def resolution_list(request):
    body = request.GET.get('body', '')
    session = request.GET.get('session', '')

    qs = Resolution.objects.all()
    if body in ('GA', 'SC'):
        qs = qs.filter(body=body)
    if session and session.isdigit():
        qs = qs.filter(session=int(session))

    filter_qs = Resolution.objects.all()
    if body in ('GA', 'SC'):
        filter_qs = filter_qs.filter(body=body)
    sessions = filter_qs.order_by('-session').values_list('session', flat=True).distinct()

    paginator = Paginator(qs.order_by('-session', 'adopted_symbol', 'draft_symbol'), 50)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'votes/resolutions.html', {
        'page': page,
        'sessions': sessions,
        'current_body': body,
        'current_session': session,
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
        .order_by('position_in_item')
    )

    return render(request, 'votes/resolution.html', {
        'resolution': resolution,
        'votes': votes,
    })


def country_compare(request):
    iso3_a = request.GET.get('a', '').strip().upper()
    iso3_b = request.GET.get('b', '').strip().upper()

    countries = (
        Country.objects.filter(country_votes__isnull=False, iso3__isnull=False)
        .distinct().order_by('name')
    )

    country_a = country_b = comparison = None

    if iso3_a and iso3_b and iso3_a != iso3_b:
        country_a = Country.objects.filter(iso3=iso3_a).first()
        country_b = Country.objects.filter(iso3=iso3_b).first()

    if country_a and country_b:
        POSITIONS = ['yes', 'no', 'abstain']

        votes_a = dict(
            CountryVote.objects
            .filter(country=country_a).exclude(vote_position='absent')
            .values_list('vote_id', 'vote_position')
        )
        votes_b = dict(
            CountryVote.objects
            .filter(country=country_b, vote_id__in=votes_a.keys())
            .exclude(vote_position='absent')
            .values_list('vote_id', 'vote_position')
        )
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

        # Agreement by session
        shared_vote_qs = (
            Vote.objects
            .filter(id__in=shared_ids)
            .select_related('resolution', 'document')
        )
        session_stats = defaultdict(lambda: {'agree': 0, 'total': 0, 'years': set()})
        vote_map = {}
        for v in shared_vote_qs:
            vote_map[v.id] = v
            sess = v.resolution.session
            if not sess:
                continue
            if v.document.date:
                session_stats[sess]['years'].add(v.document.date.year)
            session_stats[sess]['total'] += 1
            if votes_a[v.id] == votes_b[v.id]:
                session_stats[sess]['agree'] += 1

        by_session = sorted([
            {
                'session': sess,
                'year': min(stats['years']) if stats['years'] else None,
                'total': stats['total'],
                'agree': stats['agree'],
                'rate': round(100 * stats['agree'] / stats['total']) if stats['total'] else 0,
            }
            for sess, stats in session_stats.items()
            if stats['total'] >= 2
        ], key=lambda x: x['session'])

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
            'divergent': divergent,
            'agreed_contested': agreed_contested,
        }

    return render(request, 'votes/compare.html', {
        'countries':  countries,
        'country_a':  country_a,
        'country_b':  country_b,
        'iso3_a':     iso3_a,
        'iso3_b':     iso3_b,
        'comparison': comparison,
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'Voting Analysis', 'url': '/votes/'},
            {'label': 'Compare'},
        ],
    })


def votes_page(request):
    countries = (
        Country.objects.filter(country_votes__isnull=False, iso3__isnull=False)
        .distinct()
        .order_by('name')
    )

    # Summary counts
    total_resolutions = Resolution.objects.filter(votes__vote_type='recorded').distinct().count()
    total_recorded_votes = Vote.objects.filter(vote_type='recorded', yes_count__isnull=False).count()
    total_country_votes = CountryVote.objects.count()

    # Overall position breakdown (exclude absent from percentages)
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
    most_contested = (
        Vote.objects
        .filter(vote_type='recorded', no_count__isnull=False, no_count__gt=0)
        .select_related('resolution', 'document')
        .order_by('-no_count')[:6]
    )

    # Most recent votes
    recent_votes = (
        Vote.objects
        .filter(vote_type='recorded', yes_count__isnull=False)
        .select_related('resolution', 'document')
        .order_by('-document__date')[:8]
    )

    # Countries casting the most No votes (politically revealing)
    top_no_voters = list(
        CountryVote.objects
        .filter(vote_position='no')
        .values('country__name', 'country__iso3', 'country__short_name')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )

    return render(request, 'votes/index.html', {
        'countries':           countries,
        'total_resolutions':   total_resolutions,
        'total_recorded_votes': total_recorded_votes,
        'total_country_votes': total_country_votes,
        'yes_pct':             yes_pct,
        'no_pct':              no_pct,
        'abstain_pct':         abstain_pct,
        'most_contested':      most_contested,
        'recent_votes':        recent_votes,
        'top_no_voters':       top_no_voters,
    })


def country_votes_json(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)
    session_param = request.GET.get('session', '')
    try:
        session = int(session_param) if session_param else None
    except ValueError:
        session = None
    cvotes = (
        CountryVote.objects
        .filter(country=country)
        .select_related('vote__resolution', 'vote__document')
        .order_by('-vote__document__date')
    )
    if session:
        cvotes = cvotes.filter(vote__document__session=session)
    records = []
    for cv in cvotes:
        v = cv.vote
        doc = v.document
        res = v.resolution
        records.append({
            'id': cv.pk,
            'position': cv.vote_position,
            'year': doc.date.year if doc.date else None,
            'date': doc.date.isoformat() if doc.date else '',
            'session': res.session,
            'category': res.category or 'Uncategorized',
            'resolution': str(res),
            'title': (res.title or '')[:120],
            'yes_count': v.yes_count,
            'no_count': v.no_count,
            'abstain_count': v.abstain_count,
            'document': doc.symbol,
            'document_url': doc.get_absolute_url(),
        })
    return JsonResponse({'country': country.name, 'iso3': iso3, 'votes': records})


def country_similarity_json(request, iso3):
    """Return top-10 most and least similar countries by voting pattern."""
    country = get_object_or_404(Country, iso3=iso3)

    POS_MAP = {'yes': 1, 'abstain': 2, 'no': 3}
    MIN_SHARED = 10

    # Fetch all non-absent votes for the reference country: vote_id → position
    a_votes = dict(
        CountryVote.objects
        .filter(country=country)
        .exclude(vote_position='absent')
        .values_list('vote_id', 'vote_position')
    )

    if not a_votes:
        return JsonResponse({'similar': [], 'dissimilar': []})

    # Fetch all other countries' non-absent votes on the same vote_ids
    other_votes = (
        CountryVote.objects
        .filter(vote_id__in=a_votes.keys())
        .exclude(country=country)
        .exclude(vote_position='absent')
        .values('country_id', 'country__name', 'country__iso3', 'vote_id', 'vote_position')
    )

    # Accumulate per-country absolute differences (scale 0–2)
    cdata = defaultdict(lambda: {'name': '', 'iso3': '', 'diffs': []})
    for row in other_votes:
        cid = row['country_id']
        pos_a = POS_MAP.get(a_votes.get(row['vote_id']))
        pos_b = POS_MAP.get(row['vote_position'])
        if pos_a is None or pos_b is None:
            continue
        cdata[cid]['name'] = row['country__name']
        cdata[cid]['iso3'] = row['country__iso3'] or ''
        cdata[cid]['diffs'].append(abs(pos_a - pos_b))

    results = []
    for d in cdata.values():
        if len(d['diffs']) < MIN_SHARED:
            continue
        mean_diff = sum(d['diffs']) / len(d['diffs'])
        # similarity: 1 = identical, 0 = always opposite
        results.append({
            'iso3': d['iso3'],
            'name': d['name'],
            'score': round(1.0 - mean_diff / 2.0, 3),
            'shared': len(d['diffs']),
        })

    results.sort(key=lambda x: x['score'], reverse=True)

    return JsonResponse({
        'similar': results[:10],
        'dissimilar': list(reversed(results[-10:])),
    })
