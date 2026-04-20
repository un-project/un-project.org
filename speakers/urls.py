from django.urls import path
from . import views

app_name = 'speakers'

urlpatterns = [
    path('', views.speaker_list, name='list'),
    path('<int:pk>/', views.speaker_detail, name='detail'),
]
