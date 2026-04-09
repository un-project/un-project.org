from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('', views.api_root, name='api_root'),
    path('search/', views.api_search, name='search'),
    path('suggest/', views.suggest, name='suggest'),
    path('topic-timeline/', views.topic_timeline, name='topic_timeline'),
    path('wordcloud/', views.wordcloud, name='wordcloud'),
    # Speakers
    path('speakers/', views.speaker_list, name='speaker_list'),
    path('speakers/search/', views.speaker_search, name='speaker_search'),
    path('speakers/<int:pk>/', views.speaker_detail, name='speaker_detail'),
    path('speakers/<int:pk>/speeches/', views.speaker_speeches, name='speaker_speeches'),
    path('speakers/<int:pk>/meetings/', views.speaker_meetings, name='speaker_meetings'),
    # Countries
    path('countries/', views.country_list, name='country_list'),
    path('countries/<str:iso3>/', views.country_detail, name='country_detail'),
    path('countries/<str:iso3>/speeches/', views.country_speeches, name='country_speeches'),
    path('countries/<str:iso3>/representatives/', views.country_representatives, name='country_representatives'),
    path('countries/<str:iso3>/sc-reps/', views.country_sc_reps, name='country_sc_reps'),
    path('countries/<str:iso3>/ideal-points/', views.country_ideal_points, name='country_ideal_points'),
    path('countries/<str:iso3>/alignment/', views.country_alignment, name='country_alignment'),
    # Meetings
    path('meetings/', views.meeting_list, name='meeting_list'),
    path('meetings/<str:slug>/', views.meeting_detail, name='meeting_detail'),
    # Resolutions
    path('resolutions/', views.resolution_list, name='resolution_list'),
    path('resolutions/<str:slug>/', views.resolution_detail, name='resolution_detail'),
    path('resolutions/<str:slug>/citations/', views.resolution_citations, name='resolution_citations'),
    path('resolutions/<str:slug>/sponsors/', views.resolution_sponsors, name='resolution_sponsors'),
    # Vetoes
    path('vetoes/', views.veto_list, name='veto_list'),
]
