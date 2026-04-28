from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search, name='search'),
    path('timeline/', views.timeline, name='timeline'),
    path('topic-decades/', views.topic_decades, name='topic_decades'),
]
