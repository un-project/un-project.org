from collections import defaultdict

from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.http import Http404, JsonResponse

from countries.models import Country
from .models import CountryVote, Resolution


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


def votes_page(request):
    countries = (
        Country.objects.filter(country_votes__isnull=False, iso3__isnull=False)
        .distinct()
        .order_by('name')
    )
    return render(request, 'votes/index.html', {'countries': countries})


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
