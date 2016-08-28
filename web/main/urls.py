from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.sitemaps import views as sitemaps_views
from django.views.decorators.cache import cache_page

from blog.sitemaps import BlogSitemap
from profiles.sitemaps import ProfileSitemap
from declarations.sitemaps import DeclarationSitemap

admin.autodiscover()

sitemaps = {
    'blog': BlogSitemap(),
    'user': ProfileSitemap(),
    'declaration': DeclarationSitemap()
}

urlpatterns = [
    url(r'^', include('newsfeed.urls')),
    url(r'^', include('declarations.urls')),
    url(r'^', include('profiles.urls')),
    url(r'^blog/', include('blog.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('api.urls')),

    # Sitemap
    url(r'^sitemap\.xml$',
        cache_page(86400)(sitemaps_views.index),
        {'sitemaps': sitemaps, 'sitemap_url_name': 'sitemaps'}),
    url(r'^sitemap-(?P<section>.+)\.xml$',
        cache_page(86400)(sitemaps_views.sitemap),
        {'sitemaps': sitemaps}, name='sitemaps'),
]
