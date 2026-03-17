from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q

from meetings.models import Document
from speakers.models import Speaker
from votes.models import Resolution
from un_site.ratelimit import ratelimit

PAGE_SIZE = 50


# ── API root ────────────────────────────────────────────────────────────────────

@ratelimit(60, key_prefix='rl:api', json=True)
def api_root(request):
    base = request.build_absolute_uri('/api')
    return JsonResponse({
        'endpoints': [
            {
                'url': f'{base}/speakers/',
                'description': 'List all speakers (paginated)',
                'parameters': {'country': 'ISO3 code or numeric ID to filter by country', 'page': 'Page number'},
            },
            {
                'url': f'{base}/speakers/<id>/',
                'description': 'Retrieve a single speaker by ID',
                'parameters': {},
            },
            {
                'url': f'{base}/speakers/search/',
                'description': 'Autocomplete speaker search',
                'parameters': {'q': 'Name fragment (min 2 characters)'},
            },
            {
                'url': f'{base}/meetings/',
                'description': 'List all meetings (paginated)',
                'parameters': {'body': 'GA or SC', 'session': 'Session number', 'year': 'Year', 'page': 'Page number'},
            },
            {
                'url': f'{base}/meetings/<slug>/',
                'description': 'Retrieve a single meeting with full speech list',
                'parameters': {},
            },
            {
                'url': f'{base}/resolutions/',
                'description': 'List all resolutions (paginated)',
                'parameters': {'body': 'GA or SC', 'session': 'Session number', 'page': 'Page number'},
            },
            {
                'url': f'{base}/resolutions/<slug>/',
                'description': 'Retrieve a single resolution with vote breakdown',
                'parameters': {},
            },
        ]
    })


def _paginate(request, qs, serializer):
    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page', 1))
    base = request.build_absolute_uri(request.path)

    def page_url(n):
        params = request.GET.copy()
        params['page'] = n
        return f"{base}?{params.urlencode()}"

    return JsonResponse({
        'count': paginator.count,
        'next': page_url(page.next_page_number()) if page.has_next() else None,
        'previous': page_url(page.previous_page_number()) if page.has_previous() else None,
        'results': [serializer(obj) for obj in page],
    })


# ── Speakers ───────────────────────────────────────────────────────────────────

def _speaker_summary(s):
    return {
        'id': s.pk,
        'name': s.name,
        'country': s.country.display_name if s.country else None,
        'country_iso3': s.country.iso3 if s.country else None,
        'organization': s.organization,
        'role': s.role,
        'title': s.title,
        'url': s.get_absolute_url(),
    }


@ratelimit(60, key_prefix='rl:api', json=True)
def speaker_list(request):
    qs = Speaker.objects.select_related('country').order_by('name')

    country = request.GET.get('country', '')
    if country:
        if country.isdigit():
            qs = qs.filter(country_id=int(country))
        elif len(country) == 3:
            qs = qs.filter(country__iso3__iexact=country)

    return _paginate(request, qs, _speaker_summary)


@ratelimit(60, key_prefix='rl:api', json=True)
def speaker_detail(request, pk):
    try:
        speaker = Speaker.objects.select_related('country').get(pk=pk)
    except Speaker.DoesNotExist:
        return JsonResponse({'error': 'Speaker not found'}, status=404)
    return JsonResponse(_speaker_summary(speaker))


@ratelimit(60, key_prefix='rl:api', json=True)
def speaker_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    from speakers.models import Speaker
    qs = (
        Speaker.objects
        .filter(Q(name__icontains=q) | Q(organization__icontains=q))
        .select_related('country')
        .order_by('name')[:30]
    )
    results = [
        {
            'id': s.pk,
            'name': s.name,
            'detail': s.country.display_name if s.country else (s.organization or ''),
        }
        for s in qs
    ]
    return JsonResponse(results, safe=False)


# ── Meetings ───────────────────────────────────────────────────────────────────

def _meeting_summary(doc):
    return {
        'symbol': doc.symbol,
        'body': doc.body,
        'session': doc.session,
        'meeting_number': doc.meeting_number,
        'date': doc.date.isoformat() if doc.date else None,
        'location': doc.location,
        'url': doc.get_absolute_url(),
        'docs_un_url': doc.docs_un_url,
    }


@ratelimit(60, key_prefix='rl:api', json=True)
def meeting_list(request):
    qs = Document.objects.all()

    body = request.GET.get('body', '')
    if body in ('GA', 'SC'):
        qs = qs.filter(body=body)

    session = request.GET.get('session', '')
    if session and session.isdigit():
        qs = qs.filter(session=int(session))

    year = request.GET.get('year', '')
    if year and year.isdigit():
        qs = qs.filter(date__year=int(year))

    return _paginate(request, qs, _meeting_summary)


@ratelimit(60, key_prefix='rl:api', json=True)
def meeting_detail(request, slug):
    document = None
    for doc in Document.objects.only('id', 'symbol', 'body', 'meeting_number', 'session', 'date', 'location'):
        if doc.slug == slug:
            document = doc
            break

    if document is None:
        return JsonResponse({'error': 'Meeting not found'}, status=404)

    speeches = (
        document.speeches
        .select_related('speaker', 'speaker__country')
        .order_by('position_in_document')
    )

    return JsonResponse({
        **_meeting_summary(document),
        'speeches': [
            {
                'id': s.pk,
                'speaker': s.speaker.name,
                'country': s.speaker.country.display_name if s.speaker.country else None,
                'country_iso3': s.speaker.country.iso3 if s.speaker.country else None,
                'organization': s.speaker.organization,
                'language': s.language,
                'on_behalf_of': s.on_behalf_of,
                'text': s.text,
            }
            for s in speeches
        ],
    })


# ── Resolutions ────────────────────────────────────────────────────────────────

def _resolution_summary(res):
    votes = list(res.votes.select_related('document'))
    vote_data = []
    for v in votes:
        vote_data.append({
            'vote_type': v.vote_type,
            'vote_scope': v.vote_scope,
            'yes_count': v.yes_count,
            'no_count': v.no_count,
            'abstain_count': v.abstain_count,
            'document': v.document.symbol,
            'date': v.document.date.isoformat() if v.document.date else None,
        })
    return {
        'id': res.pk,
        'draft_symbol': res.draft_symbol,
        'adopted_symbol': res.adopted_symbol,
        'body': res.body,
        'session': res.session,
        'title': res.title,
        'category': res.category,
        'url': res.get_absolute_url(),
        'docs_un_url': res.docs_un_url,
        'votes': vote_data,
    }


@ratelimit(60, key_prefix='rl:api', json=True)
def resolution_list(request):
    qs = Resolution.objects.prefetch_related('votes__document')

    body = request.GET.get('body', '')
    if body in ('GA', 'SC'):
        qs = qs.filter(body=body)

    session = request.GET.get('session', '')
    if session and session.isdigit():
        qs = qs.filter(session=int(session))

    qs = qs.order_by('-session', 'adopted_symbol', 'draft_symbol')
    return _paginate(request, qs, _resolution_summary)


@ratelimit(60, key_prefix='rl:api', json=True)
def resolution_detail(request, slug):
    resolution = None
    for r in Resolution.objects.prefetch_related('votes__document', 'votes__country_votes__country'):
        if r.slug == slug:
            resolution = r
            break

    if resolution is None:
        return JsonResponse({'error': 'Resolution not found'}, status=404)

    votes = []
    for v in resolution.votes.select_related('document').prefetch_related('country_votes__country'):
        country_votes = [
            {
                'country': cv.country.display_name,
                'iso3': cv.country.iso3,
                'position': cv.vote_position,
            }
            for cv in v.country_votes.select_related('country').all()
        ]
        votes.append({
            'vote_type': v.vote_type,
            'vote_scope': v.vote_scope,
            'yes_count': v.yes_count,
            'no_count': v.no_count,
            'abstain_count': v.abstain_count,
            'document': v.document.symbol,
            'date': v.document.date.isoformat() if v.document.date else None,
            'country_votes': country_votes,
        })

    return JsonResponse({
        'id': resolution.pk,
        'draft_symbol': resolution.draft_symbol,
        'adopted_symbol': resolution.adopted_symbol,
        'body': resolution.body,
        'session': resolution.session,
        'title': resolution.title,
        'category': resolution.category,
        'docs_un_url': resolution.docs_un_url,
        'votes': votes,
    })
