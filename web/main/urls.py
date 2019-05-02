from django.urls import include, path, re_path
from django.contrib import admin
from django.contrib.sitemaps import views as sitemaps_views
from django.views.decorators.cache import cache_page

from blog.sitemaps import BlogSitemap
from profiles.sitemaps import ProfileSitemap
from declarations.sitemaps import DeclarationSitemap

admin.autodiscover()

sitemaps = {
    "blog": BlogSitemap(),
    "user": ProfileSitemap(),
    "declaration": DeclarationSitemap(),
}

urlpatterns = [
    path("", include("newsfeed.urls")),
    path("", include("declarations.urls")),
    path("", include("profiles.urls")),
    path("blog/", include("blog.urls")),
    path("accounts/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    # Sitemap
    re_path(
        r"^sitemap\.xml$",
        cache_page(86400)(sitemaps_views.index),
        {"sitemaps": sitemaps, "sitemap_url_name": "sitemaps"},
    ),
    re_path(
        r"^sitemap-(?P<section>.+)\.xml$",
        cache_page(86400)(sitemaps_views.sitemap),
        {"sitemaps": sitemaps},
        name="sitemaps",
    ),
]
