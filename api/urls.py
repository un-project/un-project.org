from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('meetings/', views.meeting_list, name='meeting_list'),
    path('meetings/<str:slug>/', views.meeting_detail, name='meeting_detail'),
    path('resolutions/', views.resolution_list, name='resolution_list'),
    path('resolutions/<str:slug>/', views.resolution_detail, name='resolution_detail'),
]
