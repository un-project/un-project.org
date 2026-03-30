import math

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max

from meetings.models import Document
from speakers.models import Speaker
from speeches.models import Speech
from votes.models import Resolution, ResolutionCitation
from countries.models import Country
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
    country_id = request.GET.get('country', '')
    from speakers.models import Speaker
    qs = (
        Speaker.objects
        .filter(Q(name__icontains=q) | Q(organization__icontains=q))
        .select_related('country')
        .order_by('name')
    )
    if country_id and country_id.isdigit():
        qs = qs.filter(country_id=int(country_id))
    qs = qs[:30]
    results = [
        {
            'id': s.pk,
            'name': s.name,
            'detail': s.country.display_name if s.country else (s.organization or ''),
            'country_iso3': s.country.iso3 if s.country else None,
        }
        for s in qs
    ]
    return JsonResponse(results, safe=False)


def topic_timeline(request):
    """
    For a search query, return per-country-per-year speech counts.
    Used by the /search/timeline/ heatmap page.
    """
    from django.contrib.postgres.search import SearchQuery
    from django.db.models import Count, F
    from search.models import SearchIndex

    q    = request.GET.get('q', '').strip()
    body = request.GET.get('body', '')

    if len(q) < 2:
        return JsonResponse({'years': [], 'countries': [], 'cells': []})

    search_query = SearchQuery(q, config='english', search_type='websearch')
    qs = (
        SearchIndex.objects
        .filter(search_vector=search_query, item_type='speech')
        .filter(country_iso3__isnull=False)
        .exclude(country_iso3='')
        .filter(date__isnull=False)
    )
    if body in ('GA', 'SC'):
        qs = qs.filter(body=body)

    rows = list(
        qs.values('country_name', 'country_iso3', 'country_id', year=F('date__year'))
        .annotate(count=Count('id'))
        .order_by('country_name', 'year')
    )

    if not rows:
        return JsonResponse({'years': [], 'countries': [], 'cells': []})

    # Aggregate per country — keep one country_id per iso3
    from collections import defaultdict
    country_totals = defaultdict(int)
    country_id_map = {}
    for r in rows:
        key = (r['country_iso3'], r['country_name'])
        country_totals[key] += r['count']
        if r['country_iso3'] not in country_id_map and r['country_id']:
            country_id_map[r['country_iso3']] = r['country_id']

    # Top 40 countries by total speech count
    top = sorted(country_totals.items(), key=lambda x: -x[1])[:40]
    top_iso3 = {iso3 for (iso3, _), _ in top}

    years = sorted({r['year'] for r in rows if r['country_iso3'] in top_iso3})
    countries = [
        {'iso3': iso3, 'name': name, 'total': total, 'pk': country_id_map.get(iso3)}
        for (iso3, name), total in top
    ]
    cells = [
        {'iso3': r['country_iso3'], 'year': r['year'], 'count': r['count']}
        for r in rows
        if r['country_iso3'] in top_iso3
    ]

    return JsonResponse({'years': years, 'countries': countries, 'cells': cells})


def suggest(request):
    """Autocomplete suggestions: countries + speakers matching a query."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'countries': [], 'speakers': []})

    countries = list(
        Country.objects
        .filter(Q(name__icontains=q) | Q(short_name__icontains=q))
        .filter(iso3__isnull=False)
        .exclude(iso3='')
        .order_by('name')[:6]
    )
    speakers = list(
        Speaker.objects
        .filter(Q(name__icontains=q) | Q(organization__icontains=q))
        .select_related('country')
        .order_by('name')[:6]
    )

    return JsonResponse({
        'countries': [
            {
                'name': c.display_name,
                'iso3': c.iso3,
                'url': f'/country/{c.iso3}/',
            }
            for c in countries
        ],
        'speakers': [
            {
                'name': s.name,
                'detail': s.country.display_name if s.country else (s.organization or ''),
                'iso3': s.country.iso3 if s.country else None,
                'url': f'/speaker/{s.pk}/',
            }
            for s in speakers
        ],
    })


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


@ratelimit(60, key_prefix='rl:api', json=True)
def resolution_citations(request, slug):
    """
    Return a depth-1 citation neighbourhood as nodes + edges for D3 force graph.
    Nodes: the resolution itself, all it cites, all that cite it.
    Edges: directed citation links (source → target by resolution id).
    """
    resolution = None
    for r in Resolution.objects.all():
        if r.slug == slug:
            resolution = r
            break
    if resolution is None:
        return JsonResponse({'error': 'Resolution not found'}, status=404)

    # Outgoing: what this resolution cites
    outgoing = list(
        ResolutionCitation.objects
        .filter(citing=resolution)
        .select_related('cited')
    )
    # Incoming: what cites this resolution
    incoming = list(
        ResolutionCitation.objects
        .filter(cited=resolution)
        .select_related('citing')
    )

    nodes = {}  # id → node dict; use string keys for unresolved citations

    def add_node(res, is_center=False):
        nodes[res.pk] = {
            'id': res.pk,
            'symbol': str(res),
            'title': res.title or '',
            'url': res.get_absolute_url(),
            'is_center': is_center,
        }

    add_node(resolution, is_center=True)

    edges = []

    for cit in outgoing:
        if cit.cited_id:
            add_node(cit.cited)
            edges.append({'source': resolution.pk, 'target': cit.cited_id, 'weight': cit.weight})
        else:
            # Unresolved citation — use a synthetic negative id derived from symbol
            synthetic_id = f'sym:{cit.cited_symbol}'
            nodes[synthetic_id] = {
                'id': synthetic_id,
                'symbol': cit.cited_symbol,
                'title': '',
                'url': None,
                'is_center': False,
            }
            edges.append({'source': resolution.pk, 'target': synthetic_id, 'weight': cit.weight})

    for cit in incoming:
        add_node(cit.citing)
        edges.append({'source': cit.citing_id, 'target': resolution.pk, 'weight': cit.weight})

    return JsonResponse({
        'nodes': list(nodes.values()),
        'edges': edges,
    })


# ── Word cloud ──────────────────────────────────────────────────────────────────

# Common English words + UN procedural boilerplate to exclude.
# Raw (unstemmed) forms because we count words directly with regexp_matches.
_WC_STOPWORDS = frozenset([
    # ── English function words (≥4 chars; shorter ones cut by SQL) ──────────
    'that', 'this', 'with', 'have', 'from', 'they', 'been', 'were',
    'will', 'what', 'when', 'whom', 'your', 'also', 'each', 'such',
    'into', 'over', 'more', 'most', 'only', 'very', 'just', 'even',
    'then', 'than', 'some', 'well', 'here', 'both', 'once', 'back',
    'many', 'must', 'does', 'said', 'says', 'like', 'make', 'made',
    'take', 'took', 'know', 'come', 'came', 'need', 'want', 'look',
    'them', 'time', 'year', 'call', 'upon', 'thus', 'goes', 'done',
    'used', 'seem', 'help', 'work', 'long', 'note', 'part', 'case',
    'side', 'ways', 'give', 'gave', 'gets', 'puts', 'left', 'keep',
    'held', 'sent', 'seen', 'felt', 'told', 'said', 'much', 'less',
    'able', 'away', 'among', 'open', 'full', 'high', 'wide', 'deep',
    'free', 'true', 'real', 'main', 'next', 'last', 'same', 'good',
    'best', 'held', 'show', 'find', 'move', 'turn', 'play', 'lead',
    # ── English words 5+ chars ──────────────────────────────────────────────
    'being', 'about', 'after', 'again', 'these', 'those', 'there',
    'their', 'while', 'where', 'which', 'under', 'other', 'every',
    'given', 'going', 'three', 'still', 'since', 'before', 'could',
    'would', 'should', 'might', 'shall', 'years', 'times', 'makes',
    'taken', 'comes', 'needs', 'looks', 'seems', 'through', 'without',
    'between', 'during', 'further', 'however', 'therefore', 'although',
    'including', 'already', 'always', 'within', 'toward', 'towards',
    'having', 'taking', 'making', 'working', 'possible', 'following',
    'itself', 'himself', 'herself', 'themselves', 'yourself', 'ourselves',
    'cannot', 'truly', 'fully', 'highly', 'deeply', 'widely', 'clearly',
    'strongly', 'broadly', 'largely', 'mainly', 'really', 'rather',
    'quite', 'indeed', 'often', 'ahead', 'today', 'forth', 'hence',
    'whole', 'means', 'point', 'basis', 'level', 'areas', 'great',
    'small', 'large', 'major', 'right', 'close', 'clear', 'short',
    'early', 'known', 'their', 'where', 'given', 'taken', 'given',
    'whether', 'together', 'forward', 'already', 'continue', 'continued',
    'continuing', 'continues', 'remain', 'remains', 'remaining',
    'ensure', 'ensures', 'ensuring', 'ensured', 'certain', 'number',
    'important', 'general', 'special', 'various', 'certain', 'common',
    'address', 'addressed', 'addressing', 'consider', 'considered',
    'focus', 'focused', 'focusing', 'achieve', 'achieved', 'achieving',
    'provide', 'provided', 'providing', 'reflect', 'support', 'supported',
    'supporting', 'emphasize', 'emphasizing', 'emphasize', 'stress',
    'stressed', 'stressing', 'highlight', 'highlighted', 'welcome',
    'welcomed', 'welcoming', 'commit', 'commits', 'committed',
    'commitment', 'commitments', 'invite', 'invited', 'inviting',
    'invites', 'decide', 'decided', 'decides', 'deciding',
    'wish', 'wishes', 'wishing', 'hope', 'hopes', 'hoping',
    'believe', 'believes', 'believed', 'believing', 'think', 'thought',
    'efforts', 'effort', 'goals', 'items', 'item', 'needs',
    # ── Number words (session ordinals: "seventy-ninth session") ────────────
    'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh',
    'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', 'twentieth',
    'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty',
    'ninety', 'hundred', 'thousand',
    # ── UN structural / procedural ──────────────────────────────────────────
    'united', 'nations', 'assembly', 'council', 'security',
    'president', 'presidents', 'presidency', 'chair', 'chairman',
    'chairperson', 'madam', 'mister', 'excellency', 'excellencies',
    'honour', 'honored', 'honoured', 'behalf', 'behalf',
    'delegation', 'delegations', 'representative', 'representatives',
    'statement', 'statements', 'speaker', 'speakers', 'speaking',
    'thank', 'thanks', 'please', 'floor', 'member', 'members',
    'session', 'sessions', 'meeting', 'meetings', 'agenda', 'item',
    'plenary', 'committee', 'committees', 'credentials',
    'resolution', 'resolutions', 'paragraph', 'paragraphs',
    'article', 'articles', 'draft', 'drafts', 'adopted', 'adopt',
    'document', 'documents', 'order', 'orders', 'record', 'recorded',
    'vote', 'votes', 'voting', 'voted', 'cent', 'percent',
    'noted', 'noting', 'notes', 'recall', 'recalls', 'recalling',
    'reaffirm', 'reaffirms', 'reaffirming', 'reaffirmed',
    'affirm', 'affirms', 'affirming', 'affirmed',
    'recognize', 'recognizes', 'recognizing', 'recognized',
    'concern', 'concerned', 'concerns', 'urge', 'urges', 'urging',
    'request', 'requests', 'requesting', 'requested',
    'secretary', 'secretariat', 'rapporteur',
    # ── Generic adjectives / prepositions that slipped through ──────────────
    'against', 'behind', 'entire', 'across', 'above', 'below',
    'role', 'roles', 'kind', 'kinds', 'type', 'types', 'form', 'forms',
    'aspect', 'aspects', 'issue', 'issues', 'matter', 'matters',
    'strengthening', 'strengthen', 'strengthened', 'strengthens',
    'highest', 'lower', 'upper', 'least', 'greater', 'lesser',
])


@ratelimit(60, key_prefix='rl:api', json=True)
def wordcloud(request):
    body = request.GET.get('body', '')
    session = request.GET.get('session', '')
    speaker_id = request.GET.get('speaker_id', '')
    country_id = request.GET.get('country_id', '')

    year_from = request.GET.get('year_from', '')
    year_to   = request.GET.get('year_to',   '')

    conditions = ["item_type = 'speech'"]
    if body in ('GA', 'SC'):
        conditions.append(f"body = '{body}'")
    if session and session.isdigit():
        conditions.append(f"session = {int(session)}")
    if speaker_id and speaker_id.isdigit():
        conditions.append(f"speaker_id = {int(speaker_id)}")
    if country_id and country_id.isdigit():
        conditions.append(f"country_id = {int(country_id)}")
    if year_from and year_from.isdigit():
        conditions.append(f"EXTRACT(YEAR FROM date) >= {int(year_from)}")
    if year_to and year_to.isdigit():
        conditions.append(f"EXTRACT(YEAR FROM date) <= {int(year_to)}")

    where = ' AND '.join(conditions)
    limit = 3000 if (speaker_id or country_id) else 5000

    # Count raw (unstemmed) words directly from speech text using regexp_matches.
    # ORDER BY id makes the inner LIMIT deterministic across requests.
    sql = f"""
        SELECT word, count(*) AS n
        FROM (
            SELECT lower(m[1]) AS word
            FROM   search_index,
                   LATERAL regexp_matches(content, '[a-zA-Z]{{4,}}', 'g') AS m
            WHERE  {where}
            ORDER BY id
            LIMIT  {limit}
        ) sub
        GROUP BY word
        ORDER BY n DESC
        LIMIT  80
    """

    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()

    # Build dynamic exclusions from the country/speaker name so the entity's
    # own name doesn't dominate its own word cloud.
    # Exclude the country's own name so it doesn't dominate its word cloud.
    dynamic_stop = set()
    if country_id and country_id.isdigit():
        try:
            name = Country.objects.get(pk=int(country_id)).name
            dynamic_stop.update(w.lower() for w in name.split() if len(w) >= 4)
        except Country.DoesNotExist:
            pass

    words = [
        {'word': word, 'count': n}
        for word, n in rows
        if word not in _WC_STOPWORDS and word not in dynamic_stop
    ][:40]
    # Raw counts are returned; the JS scales them linearly between the
    # actual min and max so the most-frequent words are always largest.

    resp = JsonResponse({'words': words})
    resp['Cache-Control'] = 'public, max-age=3600'
    return resp


@ratelimit(60, key_prefix='rl:api', json=True)
def speaker_speeches(request, pk):
    speaker = get_object_or_404(Speaker, pk=pk)
    body = request.GET.get('body', '')
    year_from = request.GET.get('year_from', '')
    year_to   = request.GET.get('year_to', '')
    try:
        page_num = max(1, int(request.GET.get('page', '1')))
    except ValueError:
        page_num = 1

    qs = (
        Speech.objects.filter(speaker=speaker, document__date__year__gt=1900)
        .select_related('document')
        .order_by('-document__date', '-position_in_document')
    )
    if body in ('GA', 'SC'):
        qs = qs.filter(document__body=body)
    if year_from and year_from.isdigit():
        qs = qs.filter(document__date__year__gte=int(year_from))
    if year_to and year_to.isdigit():
        qs = qs.filter(document__date__year__lte=int(year_to))

    paginator = Paginator(qs, 20)
    page = paginator.get_page(page_num)

    speeches = []
    for speech in page:
        speeches.append({
            'url':             speech.get_absolute_url(),
            'document_symbol': speech.document.symbol,
            'document_url':    speech.document.get_absolute_url(),
            'date':            speech.document.date.isoformat() if speech.document.date else '',
            'body':            speech.document.body or '',
            'excerpt':         speech.excerpt,
        })

    return JsonResponse({
        'speeches':  speeches,
        'page':      page.number,
        'total':     paginator.count,
        'num_pages': paginator.num_pages,
        'has_next':  page.has_next(),
        'has_prev':  page.has_previous(),
    })


@ratelimit(60, key_prefix='rl:api', json=True)
def country_speeches(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)
    body = request.GET.get('body', '')
    year_from = request.GET.get('year_from', '')
    year_to   = request.GET.get('year_to', '')
    try:
        page_num = max(1, int(request.GET.get('page', '1')))
    except ValueError:
        page_num = 1

    qs = (
        Speech.objects.filter(speaker__country=country, document__date__year__gt=1900)
        .select_related('speaker', 'document')
        .order_by('-document__date', '-position_in_document')
    )
    if body in ('GA', 'SC'):
        qs = qs.filter(document__body=body)
    if year_from and year_from.isdigit():
        qs = qs.filter(document__date__year__gte=int(year_from))
    if year_to and year_to.isdigit():
        qs = qs.filter(document__date__year__lte=int(year_to))

    paginator = Paginator(qs, 20)
    page = paginator.get_page(page_num)

    speeches = []
    for speech in page:
        speeches.append({
            'url':             speech.get_absolute_url(),
            'speaker_name':    speech.speaker.name,
            'speaker_url':     speech.speaker.get_absolute_url(),
            'speaker_pk':      speech.speaker.pk,
            'document_symbol': speech.document.symbol,
            'document_url':    speech.document.get_absolute_url(),
            'date':            speech.document.date.isoformat() if speech.document.date else '',
            'body':            speech.document.body or '',
            'excerpt':         speech.excerpt,
        })

    return JsonResponse({
        'speeches':  speeches,
        'page':      page.number,
        'total':     paginator.count,
        'num_pages': paginator.num_pages,
        'has_next':  page.has_next(),
        'has_prev':  page.has_previous(),
    })


@ratelimit(60, key_prefix='rl:api', json=True)
def country_representatives(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)
    body = request.GET.get('body', '')
    year_from = request.GET.get('year_from', '')
    year_to   = request.GET.get('year_to', '')
    try:
        page_num = max(1, int(request.GET.get('page', '1')))
    except ValueError:
        page_num = 1

    qs = Speech.objects.filter(speaker__country=country, document__date__year__gt=1900)
    if body in ('GA', 'SC'):
        qs = qs.filter(document__body=body)
    if year_from and year_from.isdigit():
        qs = qs.filter(document__date__year__gte=int(year_from))
    if year_to and year_to.isdigit():
        qs = qs.filter(document__date__year__lte=int(year_to))

    rep_qs = (
        qs.values('speaker_id', 'speaker__name', 'speaker__role')
        .annotate(
            first_year=Min('document__date__year'),
            last_year=Max('document__date__year'),
        )
        .order_by('speaker__name')
    )

    paginator = Paginator(rep_qs, 20)
    page = paginator.get_page(page_num)

    reps = [
        {
            'name':       r['speaker__name'],
            'url':        f'/speaker/{r["speaker_id"]}/',
            'role':       r['speaker__role'] or '',
            'first_year': r['first_year'],
            'last_year':  r['last_year'],
        }
        for r in page
    ]

    return JsonResponse({
        'representatives': reps,
        'page':            page.number,
        'total':           paginator.count,
        'num_pages':       paginator.num_pages,
        'has_next':        page.has_next(),
        'has_prev':        page.has_previous(),
    })


@ratelimit(60, key_prefix='rl:api', json=True)
def speaker_meetings(request, pk):
    speaker = get_object_or_404(Speaker, pk=pk)
    body = request.GET.get('body', '')
    year_from = request.GET.get('year_from', '')
    year_to   = request.GET.get('year_to', '')
    try:
        page_num = max(1, int(request.GET.get('page', '1')))
    except ValueError:
        page_num = 1

    qs = (
        Document.objects.filter(speeches__speaker=speaker)
        .distinct()
        .order_by('-date')
    )
    if body in ('GA', 'SC'):
        qs = qs.filter(body=body)
    if year_from and year_from.isdigit():
        qs = qs.filter(date__year__gte=int(year_from))
    if year_to and year_to.isdigit():
        qs = qs.filter(date__year__lte=int(year_to))

    paginator = Paginator(qs, 20)
    page = paginator.get_page(page_num)

    return JsonResponse({
        'meetings':  [_meeting_summary(doc) for doc in page],
        'page':      page.number,
        'total':     paginator.count,
        'num_pages': paginator.num_pages,
        'has_next':  page.has_next(),
        'has_prev':  page.has_previous(),
    })
