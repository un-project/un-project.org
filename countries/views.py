from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.conf import settings
from .models import Country
from speakers.models import Speaker
from speeches.models import Speech
from votes.models import CountryVote


def _render_country_detail(request, country):
    # Session filter
    session_param = request.GET.get('session', '')
    try:
        current_session = int(session_param) if session_param else None
    except ValueError:
        current_session = None

    # Representatives — scoped to session when active
    rep_qs = Speaker.objects.filter(country=country)
    if current_session:
        rep_qs = rep_qs.filter(speeches__document__session=current_session).distinct()
    representatives = rep_qs.order_by('name')

    # Available sessions (union of speech sessions and vote sessions, descending)
    speech_sessions = set(
        Speech.objects.filter(speaker__country=country)
        .values_list('document__session', flat=True)
        .distinct()
    )
    vote_sessions = set(
        CountryVote.objects.filter(country=country)
        .values_list('vote__document__session', flat=True)
        .distinct()
    )
    sessions = sorted(speech_sessions | vote_sessions, reverse=True)

    # Speeches (filtered by session when active)
    recent_speeches = (
        Speech.objects.filter(speaker__country=country)
        .select_related('speaker', 'document')
        .order_by('-document__date', '-position_in_document')
    )
    if current_session:
        recent_speeches = recent_speeches.filter(document__session=current_session)
    paginator = Paginator(recent_speeches, getattr(settings, 'SPEECHES_PER_PAGE', 20))
    speeches_page = paginator.get_page(request.GET.get('page'))

    # Voting history (filtered by session when active)
    voting_history = (
        CountryVote.objects.filter(country=country)
        .select_related('vote__resolution', 'vote__document')
        .order_by('-vote__document__date')
    )
    if current_session:
        voting_history = voting_history.filter(vote__document__session=current_session)
    voting_history = voting_history[:20]

    # Vote stats (filtered by session when active)
    vote_qs = CountryVote.objects.filter(country=country)
    if current_session:
        vote_qs = vote_qs.filter(vote__document__session=current_session)
    vote_stats = {
        'yes':     vote_qs.filter(vote_position='yes').count(),
        'no':      vote_qs.filter(vote_position='no').count(),
        'abstain': vote_qs.filter(vote_position='abstain').count(),
    }

    return render(request, 'countries/detail.html', {
        'country': country,
        'representatives': representatives,
        'speeches_page': speeches_page,
        'voting_history': voting_history,
        'vote_stats': vote_stats,
        'sessions': sessions,
        'current_session': current_session,
    })


def country_detail(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)
    return _render_country_detail(request, country)


def country_detail_by_id(request, pk):
    country = get_object_or_404(Country, pk=pk)
    if country.iso3:
        return redirect('countries:detail', iso3=country.iso3)
    return _render_country_detail(request, country)
