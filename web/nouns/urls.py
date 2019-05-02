from django.urls import re_path
from nouns.views import NounDetail, RelationCreate, ChannelDetail

urlpatterns = [
    re_path(r"^(?P<slug>[-\w]+)/$", NounDetail.as_view(), name="nouns_detail"),
    re_path(
        r"^(?P<slug>[-\w]+)/new-relation$",
        RelationCreate.as_view(),
        name="new_relation",
    ),
]
