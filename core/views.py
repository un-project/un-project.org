from django.shortcuts import render
from meetings.models import Document
from votes.models import Vote


def homepage(request):
    recent_meetings = Document.objects.order_by('-date', '-meeting_number')[:10]
    recent_votes = (
        Vote.objects.select_related('resolution', 'document')
        .order_by('-document__date')[:10]
    )
    return render(request, 'core/home.html', {
        'recent_meetings': recent_meetings,
        'recent_votes': recent_votes,
    })
