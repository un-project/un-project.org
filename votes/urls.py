from django.urls import path
from . import views

app_name = 'votes'

urlpatterns = [
    path('', views.votes_page, name='index'),
    path('map/', views.voting_map, name='map'),
    path('compare/', views.country_compare, name='compare'),
    path('resolutions/', views.resolution_list, name='resolution_list'),
    path('resolution/<str:slug>/', views.resolution_detail, name='resolution_detail'),
    path('resolution/<str:slug>/citations/', views.citation_network, name='citation_network'),
    path('country/<str:iso3>/', views.country_votes_page, name='country_votes'),
    path('api/<str:iso3>/', views.country_votes_json, name='country_votes_json'),
    path('api/<str:iso3>/similarity/', views.country_similarity_json, name='country_similarity_json'),
    path('api/pk/<int:pk>/similarity/', views.country_similarity_json_by_pk, name='country_similarity_json_by_pk'),
    path('bloc/<slug:slug>/', views.bloc_detail, name='bloc_detail'),
    path('ideal-points/', views.ideal_points_timeline, name='ideal_points'),
    path('cohesion/', views.cohesion_heatmap, name='cohesion'),
    path('vetoes/', views.veto_list, name='veto_list'),
]
