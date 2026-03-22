from django.shortcuts import render
from django.views.generic import TemplateView
from meetings.models import Document
from votes.models import Vote


def homepage(request):
    body = request.GET.get('body', '')

    meetings_qs = Document.objects.order_by('-date', '-meeting_number')
    votes_qs = Vote.objects.select_related('resolution', 'document').order_by('-document__date')

    if body in ('GA', 'SC'):
        meetings_qs = meetings_qs.filter(body=body)
        votes_qs = votes_qs.filter(document__body=body)

    wc_url = f'/api/wordcloud/?body={body}' if body in ('GA', 'SC') else ''

    return render(request, 'core/home.html', {
        'recent_meetings': meetings_qs[:10],
        'recent_votes': votes_qs[:10],
        'current_body': body,
        'wc_url': wc_url,
    })


about = TemplateView.as_view(template_name='core/about.html')
legal = TemplateView.as_view(template_name='core/legal.html')
