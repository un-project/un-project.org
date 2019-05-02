from django.urls import path

from newsfeed.views import NewsfeedView, PublicNewsfeedView

urlpatterns = [
    path("newsfeed", NewsfeedView.as_view(), name="newsfeed"),
    path("newsfeed/public", PublicNewsfeedView.as_view(), name="public_newsfeed"),
]
