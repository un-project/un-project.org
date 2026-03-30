from django.urls import path
from . import views

app_name = 'meetings'

urlpatterns = [
    path('', views.meeting_list, name='list'),
    path('agenda/', views.agenda_list, name='agenda_list'),
    path('agenda/<int:pk>/', views.agenda_detail, name='agenda_detail'),
    path('<slug:slug>/', views.meeting_detail, name='detail'),
]
