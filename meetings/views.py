from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import Http404
from django.conf import settings
from .models import Document, DocumentItem
from speeches.models import Speech, StageDirection
from votes.models import Vote, Resolution


def meeting_list(request):
    qs = Document.objects.all()

    body = request.GET.get('body')
    if body in ('GA', 'SC'):
        qs = qs.filter(body=body)

    session = request.GET.get('session')
    if session and session.isdigit():
        qs = qs.filter(session=int(session))

    year = request.GET.get('year')
    if year and year.isdigit():
        qs = qs.filter(date__year=int(year))

    filter_qs = Document.objects.all()
    if body in ('GA', 'SC'):
        filter_qs = filter_qs.filter(body=body)

    sessions = filter_qs.order_by('-session').values_list('session', flat=True).distinct()
    years = (
        filter_qs.filter(date__isnull=False)
        .order_by('-date__year')
        .dates('date', 'year')
    )

    paginator = Paginator(qs, getattr(settings, 'MEETINGS_PER_PAGE', 25))
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
        'crumbs': crumbs,
    })
