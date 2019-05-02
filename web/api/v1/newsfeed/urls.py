from django.urls import path
from .views import public_newsfeed, private_newsfeed

urlpatterns = [
    path("public/", public_newsfeed, name="api-public-newfeed"),
    path("private/", private_newsfeed, name="api-private-newfeed"),
]
