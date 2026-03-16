from django.contrib.sitemaps import Sitemap

from meetings.models import Document
from countries.models import Country
from speakers.models import Speaker
from votes.models import Resolution


class MeetingSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return Document.objects.only('symbol', 'date').order_by('-date')

    def lastmod(self, obj):
        if obj.date and obj.date.year <= 2100:
            return obj.date
        return None


class CountrySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Country.objects.filter(iso3__isnull=False).order_by('name')


class SpeakerSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return Speaker.objects.order_by('name')


class ResolutionSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return Resolution.objects.order_by('-session', 'adopted_symbol')


sitemaps = {
    'meetings':    MeetingSitemap,
    'countries':   CountrySitemap,
    'speakers':    SpeakerSitemap,
    'resolutions': ResolutionSitemap,
}
