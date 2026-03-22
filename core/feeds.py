import datetime

from django.contrib.syndication.views import Feed
from django.db.models import Min
from django.utils.feedgenerator import Atom1Feed

from meetings.models import Document
from votes.models import Resolution

_BODY = {'GA': 'General Assembly', 'SC': 'Security Council'}


class MeetingsFeed(Feed):
    feed_type = Atom1Feed
    title = 'UN Project — Latest Meetings'
    link = '/meeting/'
    description = 'New General Assembly and Security Council meeting transcripts.'

    def items(self):
        return (
            Document.objects
            .filter(date__isnull=False)
            .order_by('-date')[:30]
        )

    def item_title(self, item):
        return f'{item.symbol} — {_BODY.get(item.body, item.body)}'

    def item_description(self, item):
        parts = [f'Session {item.session}, Meeting {item.meeting_number}']
        if item.date:
            parts.append(item.date.strftime('%B %-d, %Y'))
        if item.location:
            parts.append(item.location)
        return ' — '.join(parts)

    def item_pubdate(self, item):
        return datetime.datetime.combine(item.date, datetime.time.min,
                                         tzinfo=datetime.timezone.utc)

    def item_link(self, item):
        return item.get_absolute_url()


class ResolutionsFeed(Feed):
    feed_type = Atom1Feed
    title = 'UN Project — Latest Resolutions'
    link = '/votes/resolutions/'
    description = 'New General Assembly and Security Council resolutions.'

    def items(self):
        return (
            Resolution.objects
            .annotate(vote_date=Min('votes__document__date'))
            .filter(vote_date__isnull=False)
            .order_by('-vote_date')[:30]
        )

    def item_title(self, item):
        symbol = item.adopted_symbol or item.draft_symbol
        return f'{symbol} — {item.title[:80]}' if item.title else symbol

    def item_description(self, item):
        body = _BODY.get(item.body, item.body)
        parts = [body]
        if item.session:
            parts.append(f'Session {item.session}')
        if item.title:
            parts.append(item.title)
        return ', '.join(parts)

    def item_pubdate(self, item):
        return datetime.datetime.combine(item.vote_date, datetime.time.min,
                                         tzinfo=datetime.timezone.utc)

    def item_link(self, item):
        return item.get_absolute_url()
