from django.shortcuts import render
from meetings.models import Document
from votes.models import Vote


def homepage(request):
    body = request.GET.get('body', '')

    meetings_qs = Document.objects.order_by('-date', '-meeting_number')
    votes_qs = Vote.objects.select_related('resolution', 'document').order_by('-document__date')

    if body in ('GA', 'SC'):
        meetings_qs = meetings_qs.filter(body=body)
        votes_qs = votes_qs.filter(document__body=body)

    return render(request, 'core/home.html', {
        'recent_meetings': meetings_qs[:10],
        'recent_votes': votes_qs[:10],
        'current_body': body,
    })
