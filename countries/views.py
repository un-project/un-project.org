from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from .models import Country
from speakers.models import Speaker
from speeches.models import Speech
from votes.models import CountryVote


def country_detail(request, iso3):
    country = get_object_or_404(Country, iso3=iso3)

    representatives = Speaker.objects.filter(country=country).order_by('name')

    recent_speeches = (
        Speech.objects.filter(speaker__country=country)
        .select_related('speaker', 'document')
        .order_by('-document__date', '-position_in_document')
    )
    paginator = Paginator(recent_speeches, getattr(settings, 'SPEECHES_PER_PAGE', 20))
    speeches_page = paginator.get_page(request.GET.get('page'))

    voting_history = (
        CountryVote.objects.filter(country=country)
        .select_related('vote__resolution', 'vote__document')
        .order_by('-vote__document__date')[:20]
    )

    vote_stats = {
        'yes': CountryVote.objects.filter(country=country, vote_position='yes').count(),
        'no': CountryVote.objects.filter(country=country, vote_position='no').count(),
        'abstain': CountryVote.objects.filter(country=country, vote_position='abstain').count(),
    }

    return render(request, 'countries/detail.html', {
        'country': country,
        'representatives': representatives,
        'speeches_page': speeches_page,
        'voting_history': voting_history,
        'vote_stats': vote_stats,
    })


def country_detail_by_id(request, pk):
    country = get_object_or_404(Country, pk=pk)
    if country.iso3:
        from django.shortcuts import redirect
        return redirect('countries:detail', iso3=country.iso3)

    representatives = Speaker.objects.filter(country=country).order_by('name')
    recent_speeches = (
        Speech.objects.filter(speaker__country=country)
        .select_related('speaker', 'document')
        .order_by('-document__date', '-position_in_document')
    )
    paginator = Paginator(recent_speeches, getattr(settings, 'SPEECHES_PER_PAGE', 20))
    speeches_page = paginator.get_page(request.GET.get('page'))

    voting_history = (
        CountryVote.objects.filter(country=country)
        .select_related('vote__resolution', 'vote__document')
        .order_by('-vote__document__date')[:20]
    )

    vote_stats = {
        'yes': CountryVote.objects.filter(country=country, vote_position='yes').count(),
        'no': CountryVote.objects.filter(country=country, vote_position='no').count(),
        'abstain': CountryVote.objects.filter(country=country, vote_position='abstain').count(),
    }

    return render(request, 'countries/detail.html', {
        'country': country,
        'representatives': representatives,
        'speeches_page': speeches_page,
        'voting_history': voting_history,
        'vote_stats': vote_stats,
    })
