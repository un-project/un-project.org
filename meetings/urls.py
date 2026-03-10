from django.urls import path
from . import views

app_name = 'meetings'

urlpatterns = [
    path('', views.meeting_list, name='list'),
    path('<slug:slug>/', views.meeting_detail, name='detail'),
]
