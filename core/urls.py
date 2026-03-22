from django.urls import path
from . import views
from .feeds import MeetingsFeed, ResolutionsFeed

app_name = 'core'

urlpatterns = [
    path('', views.homepage, name='home'),
    path('about/', views.about, name='about'),
    path('legal/', views.legal, name='legal'),
    path('feed/meetings/', MeetingsFeed(), name='feed_meetings'),
    path('feed/resolutions/', ResolutionsFeed(), name='feed_resolutions'),
]
