import json

from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, F, Min, Max
from .models import Speaker
from speeches.models import Speech
from meetings.models import Document


def speaker_list(request):
    q       = request.GET.get('q', '').strip()
    country = request.GET.get('country', '').strip()

    qs = Speaker.objects.select_related('country').annotate(
        speech_count=Count('speeches', distinct=True)
    )

    if q:
        qs = qs.filter(name__icontains=q)
    else:
        qs = qs.filter(speech_count__gt=0)

    if country:
        qs = qs.filter(country__iso3=country)

    qs = qs.order_by('name' if q else '-speech_count')

    # Countries sidebar: distinct countries that have speakers with speeches,
    # ordered by speaker count descending.
    country_list = list(
        Speaker.objects
        .filter(speeches__isnull=False, country__iso3__isnull=False)
        .values('country__iso3', 'country__name', 'country__short_name')
        .annotate(count=Count('id', distinct=True))
        .order_by('-count')
    )

    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'speakers/list.html', {
        'page':            page,
        'current_q':       q,
        'current_country': country,
        'country_list':    country_list,
    })


def speaker_detail(request, pk):
    speaker = get_object_or_404(Speaker.objects.select_related('country'), pk=pk)

    all_speeches = Speech.objects.filter(speaker=speaker, document__date__year__gt=1900)

    speech_count = all_speeches.count()

    meetings_count = (
        Document.objects.filter(speeches__speaker=speaker)
        .distinct().count()
    )

    speeches_by_year = json.dumps(list(
        all_speeches
        .values(year=F('document__date__year'), body=F('document__body'))
        .annotate(count=Count('id'))
        .order_by('year', 'body')
    ))

    meetings_by_year = json.dumps(list(
        Document.objects.filter(speeches__speaker=speaker, date__year__gt=1900)
        .distinct()
        .values('body', year=F('date__year'))
        .annotate(count=Count('pk'))
        .order_by('year', 'body')
    ))

    wc_url = f'/api/wordcloud/?speaker_id={speaker.pk}'

    crumbs = [{'label': 'Home', 'url': '/'}]
    if speaker.country:
        crumbs.append({'label': speaker.country.display_name, 'url': speaker.country.get_absolute_url()})
    crumbs.append({'label': speaker.name, 'url': None})

    return render(request, 'speakers/detail.html', {
        'speaker':          speaker,
        'speech_count':     speech_count,
        'meetings_count':   meetings_count,
        'speeches_by_year':  speeches_by_year,
        'meetings_by_year':  meetings_by_year,
        'crumbs':           crumbs,
        'wc_url':           wc_url,
    })
