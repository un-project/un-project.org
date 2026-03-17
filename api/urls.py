from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('', views.api_root, name='api_root'),
    path('speakers/', views.speaker_list, name='speaker_list'),
    path('speakers/<int:pk>/', views.speaker_detail, name='speaker_detail'),
    path('speakers/search/', views.speaker_search, name='speaker_search'),
    path('meetings/', views.meeting_list, name='meeting_list'),
    path('meetings/<str:slug>/', views.meeting_detail, name='meeting_detail'),
    path('resolutions/', views.resolution_list, name='resolution_list'),
    path('resolutions/<str:slug>/', views.resolution_detail, name='resolution_detail'),
]
