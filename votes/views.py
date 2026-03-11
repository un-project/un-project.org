from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from countries.models import Country
from .models import CountryVote


def votes_page(request):
    countries = (
        Country.objects.filter(country_votes__isnull=False, iso3__isnull=False)
        .distinct()
        .order_by('name')
    )
    return render(request, 'votes/index.html', {'countries': countries})


def country_votes_json(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)
    session_param = request.GET.get('session', '')
    try:
        session = int(session_param) if session_param else None
    except ValueError:
        session = None
    cvotes = (
        CountryVote.objects
        .filter(country=country)
        .select_related('vote__resolution', 'vote__document')
        .order_by('-vote__document__date')
    )
    if session:
        cvotes = cvotes.filter(vote__document__session=session)
    records = []
    for cv in cvotes:
        v = cv.vote
        doc = v.document
        res = v.resolution
        records.append({
            'id': cv.pk,
            'position': cv.vote_position,
            'year': doc.date.year if doc.date else None,
            'date': doc.date.isoformat() if doc.date else '',
            'session': res.session,
            'category': res.category or 'Uncategorized',
            'resolution': str(res),
            'title': (res.title or '')[:120],
            'yes_count': v.yes_count,
            'no_count': v.no_count,
            'abstain_count': v.abstain_count,
            'document': doc.symbol,
            'document_url': doc.get_absolute_url(),
        })
    return JsonResponse({'country': country.name, 'iso3': iso3, 'votes': records})
