from django.urls import re_path
from .views import (
    profile_detail,
    profile_followings,
    profile_followers,
    profile_follow,
    user_comments,
)

urlpatterns = [
    re_path(r"^(?P<username>[\w\._-]+)/$", profile_detail, name="api-profile-detail"),
    re_path(
        r"^(?P<username>[\w\._-]+)/follow/$", profile_follow, name="api-profile-follow"
    ),
    re_path(
        r"^(?P<username>[\w\._-]+)/followers/$",
        profile_followers,
        name="api-profile-followers",
    ),
    re_path(
        r"^(?P<username>[\w\._-]+)/followings/$",
        profile_followings,
        name="api-profile-followings",
    ),
    re_path(
        r"^(?P<username>[\w\._-]+)/comments/owner/$",
        user_comments,
        name="api-user-comments",
    ),
]
