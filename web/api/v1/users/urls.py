from django.conf.urls import patterns, url
from .views import (profile_detail, profile_followings, profile_followers,
                    profile_follow, user_comments)

urlpatterns = [
    url(r'^(?P<username>[\w\._-]+)/$',
        profile_detail,
        name='api-profile-detail'),
    url(r'^(?P<username>[\w\._-]+)/follow/$',
        profile_follow,
        name='api-profile-follow'),
    url(r'^(?P<username>[\w\._-]+)/followers/$',
        profile_followers,
        name='api-profile-followers'),
    url(r'^(?P<username>[\w\._-]+)/followings/$',
        profile_followings,
        name='api-profile-followings'),
    url(r'^(?P<username>[\w\._-]+)/comments/owner/$',
        user_comments,
        name='api-user-comments'),
]
