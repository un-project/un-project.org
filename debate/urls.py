from django.urls import path
from . import views

app_name = 'debate'

urlpatterns = [
    path('', views.debate_index, name='index'),
    path('<int:session>/', views.debate_session, name='session'),
    path('<int:session>/<int:pk>/', views.debate_entry, name='entry'),
]
