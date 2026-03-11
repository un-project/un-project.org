from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from .models import Document, DocumentItem
from speeches.models import Speech, StageDirection
from votes.models import Vote


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
        from django.http import Http404
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

    return render(request, 'meetings/detail.html', {
        'document': document,
        'items': items,
        'transcript': final_transcript,
    })
