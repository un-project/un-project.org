from django.urls import path
from . import views

app_name = 'countries'

urlpatterns = [
    path('<str:iso3>/', views.country_detail, name='detail'),
    path('id/<int:pk>/', views.country_detail_by_id, name='detail_by_id'),
]
