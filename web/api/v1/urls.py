from django.urls import include, path
from api.v1.users.views import profile_me


urlpatterns = [
    path("auth/", include("api.v1.auth.urls")),
    path("user/", profile_me, name="api-me"),
    path("users/", include("api.v1.users.urls")),
    path("resolutons/", include("api.v1.resolutions.urls")),
    path("newsfeed/", include("api.v1.newsfeed.urls")),
    path("notifications/", include("api.v1.notifications.urls")),
]
