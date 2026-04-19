import datetime

from django.core.cache import cache
from django.db.models.expressions import RawSQL
from django.db.models.functions import Length
from django.shortcuts import render
from django.views.generic import TemplateView
from meetings.models import Document
from speeches.models import Speech
from votes.models import Vote


def _get_speech_of_day():
    today = datetime.date.today()
    cache_key = f'speech_of_day_{today.isoformat()}'
    speech = cache.get(cache_key)
    if speech is None:
        daily_seed = str(today.toordinal())
        speech = (
            Speech.objects
            .filter(document__date__year__gt=1900)
            .annotate(tlen=Length('text'))
            .filter(tlen__gte=500)
            .annotate(daily_rand=RawSQL("md5(speeches.id::text || %s)", (daily_seed,)))
            .select_related('speaker__country', 'document')
            .order_by('daily_rand')
            .first()
        )
        # Cache until midnight so it stays stable all day.
        now = datetime.datetime.now()
        midnight = datetime.datetime.combine(today + datetime.timedelta(days=1), datetime.time.min)
        cache.set(cache_key, speech, int((midnight - now).total_seconds()))
    return speech


def homepage(request):
    body = request.GET.get('body', '')

    meetings_qs = Document.objects.filter(date__year__gt=1900).order_by('-date', '-meeting_number')
    votes_qs = Vote.objects.filter(document__date__year__gt=1900).select_related('resolution', 'document').order_by('-document__date')

    if body in ('GA', 'SC'):
        meetings_qs = meetings_qs.filter(body=body)
        votes_qs = votes_qs.filter(document__body=body)

    speech_of_day = _get_speech_of_day() if not body else None

    return render(request, 'core/home.html', {
        'recent_meetings': meetings_qs[:10],
        'recent_votes': votes_qs[:10],
        'current_body': body,
        'speech_of_day': speech_of_day,
        'today': datetime.date.today(),
    })


about = TemplateView.as_view(template_name='core/about.html')
legal = TemplateView.as_view(template_name='core/legal.html')
