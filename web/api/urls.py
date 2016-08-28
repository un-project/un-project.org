from django.conf.urls import patterns, include, url


urlpatterns = [
    url(r'^v1/', include('api.v1.urls')),
]
