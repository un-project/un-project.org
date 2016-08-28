from django.contrib.sitemaps import Sitemap
from django.utils.translation import get_language
from i18n.utils import normalize_language_code

from declarations.models import Resolution, Declaration


class ResolutionSitemap(Sitemap):
    changefreq = "never"
    priority = 0.9

    def items(self):
        language = normalize_language_code(get_language())
        return Resolution.objects.filter(
            language=language,
            is_published=True
        )

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.date_modification


class DeclarationSitemap(Sitemap):
    changefreq = "never"
    priority = 0.8

    def items(self):
        language = normalize_language_code(get_language())
        return Declaration.objects.filter(
            resolution__language=language,
            is_approved=True
        )

    def location(self, obj):
        return obj.get_list_url()
