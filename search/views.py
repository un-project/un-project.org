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

        paginator = Paginator(qs, getattr(settings, 'SEARCH_RESULTS_PER_PAGE', 20))
        page = paginator.get_page(request.GET.get('page'))

    from countries.models import Country
    from speakers.models import Speaker
    countries     = Country.objects.order_by('name')
    speakers_list = Speaker.objects.select_related('country').order_by('name')[:200]

    return render(request, 'search/results.html', {
        'query':           query_str,
        'page':            page,
        'current_body':    body,
        'current_country': country_id,
        'current_speaker': speaker_id,
        'countries':       countries,
        'speakers':        speakers_list,
    })
