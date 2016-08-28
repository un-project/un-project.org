from django.conf.urls import url

from newsfeed.views import NewsfeedView, PublicNewsfeedView


urlpatterns = [
    url(r'^newsfeed$', NewsfeedView.as_view(),
        name='newsfeed'),
    url(r'^newsfeed/public$', PublicNewsfeedView.as_view(),
        name='public_newsfeed'),
]
