from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import index as sitemap_index, sitemap
from django.http import HttpResponse
from .sitemaps import sitemaps

def health(request):
    return HttpResponse('ok')

urlpatterns = [
    path('sitemap.xml', sitemap_index, {'sitemaps': sitemaps, 'sitemap_url_name': 'sitemap_section'}, name='sitemap_index'),
    path('sitemap-<section>.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap_section'),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('meeting/', include('meetings.urls')),
    path('country/', include('countries.urls')),
    path('speaker/', include('speakers.urls')),
    path('search/', include('search.urls')),
    path('votes/', include('votes.urls')),
    path('api/', include('api.urls')),
    path('health/', health),
]
