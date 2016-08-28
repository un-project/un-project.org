from django.conf.urls import patterns, url
from django.contrib.sitemaps.views import sitemap

from blog.sitemaps import BlogSitemap
from blog.views import BlogDetailView, BlogIndexView, \
                        BlogPostsRssFeed, BlogPostsAtomFeed


urlpatterns = [
    # blog urls
    url(r'^$', BlogIndexView.as_view(), name="blog"),
    url(r'^(?P<slug>[-\w]+)/$', BlogDetailView.as_view(), name="blog_detail"),

    # rss & atom feed
    url(r'^feed/rss$', BlogPostsRssFeed(), name="blog_rss_feed"),
    url(r'^feed/atom', BlogPostsAtomFeed(), name="blog_atom_feed"),

    # sitemap
    url(r'^sitemap\.xml$', sitemap,
        {'sitemaps': {
            "blog": BlogSitemap()
        }}, name="blog_sitemap"),
]
