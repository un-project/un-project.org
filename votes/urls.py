from django.urls import path
from . import views

app_name = 'votes'

urlpatterns = [
    path('', views.votes_page, name='index'),
    path('api/<str:iso3>/', views.country_votes_json, name='country_votes_json'),
    path('api/<str:iso3>/similarity/', views.country_similarity_json, name='country_similarity_json'),
]
