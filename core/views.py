import datetime

from django.db.models.expressions import RawSQL
from django.db.models.functions import Length
from django.shortcuts import render
from django.views.generic import TemplateView
from meetings.models import Document
from speeches.models import Speech
from votes.models import Vote


def homepage(request):
    body = request.GET.get('body', '')

    meetings_qs = Document.objects.filter(date__year__gt=1900).order_by('-date', '-meeting_number')
    votes_qs = Vote.objects.filter(document__date__year__gt=1900).select_related('resolution', 'document').order_by('-document__date')

    if body in ('GA', 'SC'):
        meetings_qs = meetings_qs.filter(body=body)
        votes_qs = votes_qs.filter(document__body=body)

    # Speech of the day — deterministic: changes daily, stable within a day.
    # Order by md5(id || daily_seed) so the effective order reshuffles each day,
    # preventing consecutive days from landing on speeches from the same meeting.
    speech_of_day = None
    if not body:
        daily_seed = str(datetime.date.today().toordinal())
        speech_of_day = (
            Speech.objects
            .filter(document__date__year__gt=1900)
            .annotate(tlen=Length('text'))
            .filter(tlen__gte=500)
            .annotate(daily_rand=RawSQL("md5(speeches.id::text || %s)", (daily_seed,)))
            .select_related('speaker__country', 'document')
            .order_by('daily_rand')
            .first()
        )

    return render(request, 'core/home.html', {
        'recent_meetings': meetings_qs[:10],
        'recent_votes': votes_qs[:10],
        'current_body': body,
        'speech_of_day': speech_of_day,
        'today': datetime.date.today(),
    })


about = TemplateView.as_view(template_name='core/about.html')
legal = TemplateView.as_view(template_name='core/legal.html')
