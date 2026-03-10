from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from .models import Speaker
from speeches.models import Speech
from meetings.models import Document


def speaker_detail(request, pk):
    speaker = get_object_or_404(Speaker.objects.select_related('country'), pk=pk)

    speeches = (
        Speech.objects.filter(speaker=speaker)
        .select_related('document')
        .order_by('-document__date', '-position_in_document')
    )
    paginator = Paginator(speeches, getattr(settings, 'SPEECHES_PER_PAGE', 20))
    speeches_page = paginator.get_page(request.GET.get('page'))

    meetings_attended = (
        Document.objects.filter(speeches__speaker=speaker)
        .distinct()
        .order_by('-date')
    )

    return render(request, 'speakers/detail.html', {
        'speaker': speaker,
        'speeches_page': speeches_page,
        'speech_count': speeches.count(),
        'meetings_count': meetings_attended.count(),
        'recent_meetings': meetings_attended[:5],
    })
