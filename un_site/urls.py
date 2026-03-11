from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('meeting/', include('meetings.urls')),
    path('country/', include('countries.urls')),
    path('speaker/', include('speakers.urls')),
    path('search/', include('search.urls')),
    path('votes/', include('votes.urls')),
]
