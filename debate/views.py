from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Min, Max

from countries.models import Country
from .models import GeneralDebateEntry


def debate_entry(request, session, pk):
    entry = get_object_or_404(
        GeneralDebateEntry.objects.select_related('country', 'speaker', 'document'),
        pk=pk, ga_session=session,
    )

    # Previous / next in same session (ordered by meeting_date, id)
    qs = GeneralDebateEntry.objects.filter(ga_session=session).order_by('meeting_date', 'id')
    ids = list(qs.values_list('id', flat=True))
    try:
        pos = ids.index(pk)
    except ValueError:
        pos = -1
    prev_entry = GeneralDebateEntry.objects.filter(pk=ids[pos - 1]).first() if pos > 0 else None
    next_entry = GeneralDebateEntry.objects.filter(pk=ids[pos + 1]).first() if 0 <= pos < len(ids) - 1 else None

    return render(request, 'debate/entry.html', {
        'entry':      entry,
        'prev_entry': prev_entry,
        'next_entry': next_entry,
        'crumbs': [
            {'label': 'Home',            'url': '/'},
            {'label': 'General Debate',  'url': '/debate/'},
            {'label': f'Session {session}', 'url': f'/debate/{session}/'},
            {'label': entry.speaker_name, 'url': None},
        ],
    })


def debate_index(request):
    # Per-session summary: session, first date, last date, entry count
    sessions = (
        GeneralDebateEntry.objects
        .values('ga_session')
        .annotate(
            count=Count('id'),
            first_date=Min('meeting_date'),
            last_date=Max('meeting_date'),
        )
        .order_by('-ga_session')
    )

    total_entries = GeneralDebateEntry.objects.count()
    total_countries = (
        GeneralDebateEntry.objects
        .filter(country__isnull=False)
        .values('country').distinct().count()
    )

    # Countries for the search selector
    countries = (
        Country.objects
        .filter(debate_entries__isnull=False, iso3__isnull=False)
        .distinct()
        .order_by('name')
    )

    return render(request, 'debate/index.html', {
        'sessions': sessions,
        'total_entries': total_entries,
        'total_countries': total_countries,
        'total_sessions': len(sessions),
        'countries': countries,
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'General Debate', 'url': None},
        ],
    })


def debate_session(request, session):
    entries = (
        GeneralDebateEntry.objects
        .filter(ga_session=session)
        .select_related('country', 'speaker', 'document')
        .order_by('meeting_date', 'country__name', 'id')
    )
    if not entries.exists():
        from django.http import Http404
        raise Http404('Session not found')

    # Summary for header
    agg = entries.aggregate(
        first_date=Min('meeting_date'),
        last_date=Max('meeting_date'),
        count=Count('id'),
    )

    # Country filter
    iso3 = request.GET.get('country', '').strip().upper()
    selected_country = None
    if iso3:
        selected_country = Country.objects.filter(iso3=iso3).first()
        if selected_country:
            entries = entries.filter(country=selected_country)

    paginator = Paginator(entries, 50)
    page = paginator.get_page(request.GET.get('page'))

    # Countries present in this session for the filter dropdown
    session_countries = (
        Country.objects
        .filter(debate_entries__ga_session=session, iso3__isnull=False)
        .distinct()
        .order_by('name')
    )

    return render(request, 'debate/session.html', {
        'session': session,
        'page': page,
        'agg': agg,
        'session_countries': session_countries,
        'selected_country': selected_country,
        'iso3': iso3,
        'crumbs': [
            {'label': 'Home', 'url': '/'},
            {'label': 'General Debate', 'url': '/debate/'},
            {'label': f'Session {session}', 'url': None},
        ],
    })
