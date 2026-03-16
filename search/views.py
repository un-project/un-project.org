from django.shortcuts import render
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchRank

from .models import SearchIndex


def search(request):
    query_str  = request.GET.get('q', '').strip()
    body       = request.GET.get('body', '')
    country_id = request.GET.get('country', '')
    speaker_id = request.GET.get('speaker', '')
    date_from  = request.GET.get('date_from', '').strip()
    date_to    = request.GET.get('date_to', '').strip()

    page = None

    if query_str:
        search_query = SearchQuery(query_str, config='english', search_type='websearch')

        qs = (
            SearchIndex.objects
            .annotate(
                rank=SearchRank(
                    'search_vector', search_query,
                    cover_density=True,
                    normalization=2,        # divide by document length
                ),
                headline=SearchHeadline(
                    'content', search_query,
                    config='english',
                    start_sel='<mark>',
                    stop_sel='</mark>',
                    max_words=50,
                    min_words=20,
                    max_fragments=3,
                    fragment_delimiter=' … ',
                ),
            )
            .filter(search_vector=search_query)
            .order_by('-rank')
        )

        if body in ('GA', 'SC'):
            qs = qs.filter(body=body)
        if country_id and country_id.isdigit():
            qs = qs.filter(country_id=int(country_id))
        if speaker_id and speaker_id.isdigit():
            qs = qs.filter(speaker_id=int(speaker_id))
        if date_from:
            try:
                from datetime import date
                y, m, d = date_from.split('-')
                qs = qs.filter(date__gte=date(int(y), int(m), int(d)))
            except (ValueError, AttributeError):
                date_from = ''
        if date_to:
            try:
                from datetime import date
                y, m, d = date_to.split('-')
                qs = qs.filter(date__lte=date(int(y), int(m), int(d)))
            except (ValueError, AttributeError):
                date_to = ''

        paginator = Paginator(qs, getattr(settings, 'SEARCH_RESULTS_PER_PAGE', 20))
        page = paginator.get_page(request.GET.get('page'))

    from countries.models import Country
    from speakers.models import Speaker
    countries        = Country.objects.filter(iso3__isnull=False).order_by('name')
    selected_speaker = None
    if speaker_id and speaker_id.isdigit():
        selected_speaker = Speaker.objects.filter(pk=int(speaker_id)).select_related('country').first()

    return render(request, 'search/results.html', {
        'query':            query_str,
        'page':             page,
        'current_body':     body,
        'current_country':  country_id,
        'current_speaker':  speaker_id,
        'date_from':        date_from,
        'date_to':          date_to,
        'countries':        countries,
        'selected_speaker': selected_speaker,
    })
