import difflib

from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Min, Max
from django.http import Http404
from django.conf import settings
from .models import Document, DocumentItem
from speeches.models import Speech, StageDirection
from votes.models import Vote, Resolution


def meeting_list(request):
    qs = Document.objects.exclude(date__year__lte=1900)

    body = request.GET.get('body')
    if body in ('GA', 'SC'):
        qs = qs.filter(body=body)

    session = request.GET.get('session')
    if session and session.isdigit():
        qs = qs.filter(session=int(session))

    year = request.GET.get('year')
    if year and year.isdigit():
        qs = qs.filter(date__year=int(year))

    # Base queryset for sidebar lists (body-filtered only)
    filter_qs = Document.objects.all()
    if body in ('GA', 'SC'):
        filter_qs = filter_qs.filter(body=body)

    # Years: filtered to current session if one is selected
    year_qs = filter_qs.filter(date__isnull=False)
    if session and session.isdigit():
        year_qs = year_qs.filter(session=int(session))
    years = year_qs.dates('date', 'year', order='DESC')

    # Sessions with year ranges: filtered to current year if one is selected
    session_qs = filter_qs
    if year and year.isdigit():
        session_qs = session_qs.filter(date__year=int(year))

    session_rows = (
        session_qs
        .filter(date__isnull=False, session__isnull=False)
        .values('session')
        .annotate(year_min=Min('date__year'), year_max=Max('date__year'))
        .order_by('-session')
    )
    sessions = [
        {
            'session': row['session'],
            'year_min': row['year_min'],
            'year_max': row['year_max'],
            'label': (
                str(row['year_min']) if row['year_min'] == row['year_max']
                else f"{row['year_min']}–{row['year_max']}"
            ),
        }
        for row in session_rows
    ]

    paginator = Paginator(qs.order_by('-date', '-meeting_number'), getattr(settings, 'MEETINGS_PER_PAGE', 25))
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'meetings/list.html', {
        'page': page,
        'sessions': sessions,
        'years': years,
        'current_body': body or '',
        'current_session': session or '',
        'current_year': year or '',
    })


def meeting_detail(request, slug):
    # The slug is symbol with / replaced by - and . replaced by -
    # With ~2500 documents, iterating in Python is fast enough.
    document = None
    for doc in Document.objects.only('id', 'symbol', 'body', 'meeting_number', 'session', 'date', 'location'):
        if doc.slug == slug:
            document = doc
            break

    if document is None:
        raise Http404("Meeting not found")

    items = list(DocumentItem.objects.filter(document=document))
    item_map = {item.pk: item for item in items}

    # Build a flat list of transcript elements sorted by position_in_document
    speeches = list(
        Speech.objects.filter(document=document).select_related('speaker', 'speaker__country')
    )
    stage_dirs = list(
        StageDirection.objects.filter(document=document)
    )
    votes = list(
        Vote.objects.filter(document=document).select_related('resolution').prefetch_related(
            'country_votes__country'
        )
    )

    # Merge into a single timeline
    transcript = []
    for s in speeches:
        transcript.append({'type': 'speech', 'pos': s.position_in_document, 'item_id': s.item_id, 'obj': s})
    for d in stage_dirs:
        transcript.append({'type': 'stage', 'pos': d.position_in_document, 'item_id': d.item_id, 'obj': d})
    for v in votes:
        transcript.append({'type': 'vote', 'pos': v.position_in_item, 'item_id': v.item_id, 'obj': v})

    transcript.sort(key=lambda x: x['pos'])

    # Insert item_header markers on first appearance of each agenda item
    final_transcript = []
    seen_items = set()
    for entry in transcript:
        item_id = entry.get('item_id')
        if item_id and item_id not in seen_items:
            item = item_map.get(item_id)
            if item:
                final_transcript.append({'type': 'item_header', 'pos': entry['pos'], 'obj': item})
            seen_items.add(item_id)
        final_transcript.append(entry)

    unattributed_count = sum(
        1 for s in speeches
        if s.speaker.country_id is None and not s.speaker.organization
    )

    # Detect duplicate speeches: same speaker, same normalised opening text.
    # The later occurrence (higher position) is flagged.
    def _fp(text):
        return ' '.join(text.lower().split())[:100]

    seen_fps: dict[tuple, int] = {}
    duplicate_ids: set[int] = set()
    for s in sorted(speeches, key=lambda x: x.position_in_document):
        key = (s.speaker_id, _fp(s.text))
        if key in seen_fps:
            duplicate_ids.add(s.pk)
        else:
            seen_fps[key] = s.pk

    # At-a-glance stats — computed from already-loaded data, no extra queries
    glance_country_count = len({s.speaker.country_id for s in speeches if s.speaker.country_id})
    glance_resolutions = [v.resolution for v in votes if v.vote_scope == 'whole_resolution']

    body_label = document.body_display
    crumbs = [
        {'label': 'Home', 'url': f'/?body={document.body}'},
        {'label': f'{body_label} Meetings', 'url': f'/meeting/?body={document.body}'},
        {'label': document.symbol, 'url': None},
    ]

    return render(request, 'meetings/detail.html', {
        'document': document,
        'items': items,
        'transcript': final_transcript,
        'unattributed_count': unattributed_count,
        'duplicate_ids': duplicate_ids,
        'duplicate_count': len(duplicate_ids),
        'glance_speech_count': len(speeches),
        'glance_country_count': glance_country_count,
        'glance_resolutions': glance_resolutions,
        'crumbs': crumbs,
    })


_BODY_LABEL = {'GA': 'General Assembly', 'SC': 'Security Council'}


def session_detail(request, body, session):
    if body not in ('GA', 'SC'):
        raise Http404("Invalid body")

    documents = list(
        Document.objects
        .filter(body=body, session=session)
        .order_by('date', 'meeting_number')
    )
    if not documents:
        raise Http404("Session not found")

    resolutions = list(
        Resolution.objects
        .filter(body=body, session=session)
        .prefetch_related('votes')
        .order_by('adopted_symbol', 'draft_symbol')
    )

    # Attach the main whole-resolution vote (if any) to each resolution
    resolution_rows = []
    for res in resolutions:
        main_vote = next(
            (v for v in res.votes.all() if v.vote_scope == 'whole_resolution'),
            None,
        )
        resolution_rows.append({'resolution': res, 'vote': main_vote})

    # Year range for the session header
    dates = [d.date for d in documents if d.date]
    year_min = min(d.year for d in dates) if dates else None
    year_max = max(d.year for d in dates) if dates else None

    # Most active countries by speech count
    top_countries = list(
        Speech.objects
        .filter(document__body=body, document__session=session)
        .exclude(speaker__country=None)
        .values('speaker__country__id', 'speaker__country__name', 'speaker__country__iso3')
        .annotate(speech_count=Count('id'))
        .order_by('-speech_count')[:15]
    )
    country_count = (
        Speech.objects
        .filter(document__body=body, document__session=session)
        .exclude(speaker__country=None)
        .values('speaker__country__id')
        .distinct()
        .count()
    )
    total_speeches = Speech.objects.filter(document__body=body, document__session=session).count()

    # Top agenda items by number of meetings they appeared in
    top_items = list(
        DocumentItem.objects
        .filter(document__body=body, document__session=session, item_type=DocumentItem.ITEM_TYPE_AGENDA)
        .values('title')
        .annotate(meeting_count=Count('document_id', distinct=True))
        .order_by('-meeting_count')[:10]
    )

    # Most contested recorded votes (smallest winning margin)
    _recorded = [
        r for r in resolution_rows
        if r['vote'] and r['vote'].vote_type == 'recorded'
        and r['vote'].yes_count is not None and r['vote'].no_count is not None
        and r['vote'].no_count > 0
    ]
    contested_rows = [
        {**r, 'margin': r['vote'].yes_count - r['vote'].no_count}
        for r in sorted(_recorded, key=lambda r: r['vote'].yes_count - r['vote'].no_count)[:5]
    ]
    important_count = sum(1 for r in resolution_rows if r['resolution'].important_vote)

    body_label = _BODY_LABEL.get(body, body)
    crumbs = [
        {'label': 'Home', 'url': f'/?body={body}'},
        {'label': f'{body_label} Meetings', 'url': f'/meeting/?body={body}'},
        {'label': f'Session {session}', 'url': None},
    ]

    return render(request, 'sessions/detail.html', {
        'body': body,
        'body_label': body_label,
        'session': session,
        'documents': documents,
        'resolution_rows': resolution_rows,
        'year_min': year_min,
        'year_max': year_max,
        'top_countries': top_countries,
        'country_count': country_count,
        'total_speeches': total_speeches,
        'top_items': top_items,
        'contested_rows': contested_rows,
        'important_count': important_count,
        'crumbs': crumbs,
        'wc_url': f'/api/wordcloud/?body={body}&session={session}',
    })


# ── Agenda item pages ────────────────────────────────────────────────────────

def agenda_list(request):
    body = request.GET.get('body', '')
    cache_key = f'agenda_list_{body}'
    items = cache.get(cache_key)
    if items is None:
        qs = (
            DocumentItem.objects
            .filter(item_type=DocumentItem.ITEM_TYPE_AGENDA)
            .values('title')
            .annotate(
                meeting_count=Count('document_id', distinct=True),
                canonical_pk=Min('id'),
                session_min=Min('document__session'),
                session_max=Max('document__session'),
            )
            .filter(meeting_count__gte=2)
            .order_by('-meeting_count')
        )
        if body in ('GA', 'SC'):
            qs = qs.filter(document__body=body)
        items = list(qs[:300])
        cache.set(cache_key, items, 4 * 3600)

    return render(request, 'meetings/agenda_list.html', {
        'items': items,
        'current_body': body,
    })


def _all_agenda_titles():
    cached = cache.get('all_agenda_titles')
    if cached is not None:
        return cached
    items = list(
        DocumentItem.objects
        .filter(item_type=DocumentItem.ITEM_TYPE_AGENDA)
        .values('title')
        .annotate(meeting_count=Count('document_id', distinct=True), canonical_pk=Min('id'))
        .filter(meeting_count__gte=2)
        .order_by('-meeting_count')
    )
    cache.set('all_agenda_titles', items, 12 * 3600)
    return items


def _related_agenda_items(title, exclude_pk, threshold=0.72, limit=5):
    title_norm = title.lower().strip()
    related = []
    for item in _all_agenda_titles():
        if item['canonical_pk'] == exclude_pk:
            continue
        t_norm = item['title'].lower().strip()
        ratio = difflib.SequenceMatcher(None, title_norm, t_norm).ratio()
        if ratio >= threshold:
            related.append({**item, 'similarity': ratio})
    related.sort(key=lambda x: -x['similarity'])
    return related[:limit]


def agenda_detail(request, pk):
    canonical = get_object_or_404(DocumentItem, pk=pk, item_type=DocumentItem.ITEM_TYPE_AGENDA)
    title = canonical.title

    meetings = list(
        Document.objects
        .filter(items__title=title, items__item_type=DocumentItem.ITEM_TYPE_AGENDA)
        .annotate(speech_count=Count('speeches', distinct=True))
        .order_by('-date')
        .distinct()
    )

    countries = list(
        Speech.objects
        .filter(item__title=title, item__item_type=DocumentItem.ITEM_TYPE_AGENDA)
        .exclude(speaker__country=None)
        .values('speaker__country__id', 'speaker__country__name', 'speaker__country__iso3')
        .annotate(speech_count=Count('id'))
        .order_by('-speech_count')[:60]
    )

    sessions = sorted({m.session for m in meetings})
    related_items = _related_agenda_items(title, pk)

    return render(request, 'meetings/agenda_detail.html', {
        'title': title,
        'canonical_pk': pk,
        'meetings': meetings,
        'countries': countries,
        'sessions': sessions,
        'related_items': related_items,
    })
