from django.urls import path, re_path
from .views import (
    resolution_list,
    resolution_detail,
    declaration_detail,
    declarations_list,
    declaration_report,
    declaration_support,
    declaration_supporters,
)

urlpatterns = [
    path("", resolution_list, name="api-resolution-list"),
    re_path(r"^(?P<pk>[0-9]+)/$", resolution_detail, name="api-resolution-detail"),
    re_path(
        r"^(?P<pk>[0-9]+)/declarations/$",
        declarations_list,
        name="api-resolution-declarations",
    ),
    re_path(
        r"^(?P<pk>[0-9]+)/declarations/(?P<declaration_id>[0-9]+)/$",
        declaration_detail,
        name="api-declaration-detail",
    ),
    re_path(
        r"^(?P<pk>[0-9]+)/declarations/(?P<declaration_id>[0-9]+)/report/$",
        declaration_report,
        name="api-declaration-detail",
    ),
    re_path(
        r"^(?P<pk>[0-9]+)/declarations/(?P<declaration_id>[0-9]+)/support/$",
        declaration_support,
        name="api-declaration-detail",
    ),
    re_path(
        r"^(?P<pk>[0-9]+)/declarations/(?P<declaration_id>[0-9]+)/supporters/$",
        declaration_supporters,
        name="api-declaration-supporters",
    ),
]
