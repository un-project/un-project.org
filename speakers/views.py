from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from .models import Speaker
from speeches.models import Speech
from meetings.models import Document


def speaker_detail(request, pk):
    speaker = get_object_or_404(Speaker.objects.select_related('country'), pk=pk)

    body_param = request.GET.get('body', '')
    current_body = body_param if body_param in ('GA', 'SC') else ''

    speeches = (
        Speech.objects.filter(speaker=speaker)
        .select_related('document')
        .order_by('-document__date', '-position_in_document')
    )
    if current_body:
        speeches = speeches.filter(document__body=current_body)

    paginator = Paginator(speeches, getattr(settings, 'SPEECHES_PER_PAGE', 20))
    speeches_page = paginator.get_page(request.GET.get('page'))

    meetings_attended = (
        Document.objects.filter(speeches__speaker=speaker)
        .distinct()
        .order_by('-date')
    )
    if current_body:
        meetings_attended = meetings_attended.filter(body=current_body)

    wc_url = f'/api/wordcloud/?speaker_id={speaker.pk}'
    if current_body:
        wc_url += f'&body={current_body}'

    crumbs = [{'label': 'Home', 'url': '/'}]
    if speaker.country:
        crumbs.append({'label': speaker.country.display_name, 'url': speaker.country.get_absolute_url()})
    crumbs.append({'label': speaker.name, 'url': None})

    return render(request, 'speakers/detail.html', {
        'speaker': speaker,
        'speeches_page': speeches_page,
        'speech_count': speeches.count(),
        'meetings_count': meetings_attended.count(),
        'recent_meetings': meetings_attended[:5],
        'current_body': current_body,
        'crumbs': crumbs,
        'wc_url': wc_url,
    })
