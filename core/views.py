from django.shortcuts import render
from meetings.models import Document
from speeches.models import Speech


def homepage(request):
    recent_meetings = Document.objects.order_by('-date', '-meeting_number')[:10]
    recent_speeches = (
        Speech.objects.select_related('speaker', 'speaker__country', 'document')
        .order_by('-document__date', '-position_in_document')[:10]
    )
    return render(request, 'core/home.html', {
        'recent_meetings': recent_meetings,
        'recent_speeches': recent_speeches,
    })
