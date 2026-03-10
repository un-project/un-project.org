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

    sessions = Document.objects.order_by('-session').values_list('session', flat=True).distinct()
    years = (
        Document.objects.filter(date__isnull=False)
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

    items = DocumentItem.objects.filter(document=document).prefetch_related(
        'speeches__speaker__country',
        'stage_directions',
        'votes__resolution',
        'votes__country_votes__country',
    )

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
        transcript.append({'type': 'speech', 'pos': s.position_in_document, 'obj': s})
    for d in stage_dirs:
        transcript.append({'type': 'stage', 'pos': d.position_in_document, 'obj': d})
    for v in votes:
        # votes don't have position_in_document; use item position as fallback
        pos = getattr(v, 'position_in_item', 0)
        transcript.append({'type': 'vote', 'pos': pos, 'obj': v})

    transcript.sort(key=lambda x: x['pos'])

    return render(request, 'meetings/detail.html', {
        'document': document,
        'items': items,
        'transcript': transcript,
    })
