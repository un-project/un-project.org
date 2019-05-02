from django.urls import path, re_path
from declarations.views import HomeView, SearchView
from declarations.views import (
    ResolutionDetailView,
    HomeView,
    ResolutionCreationView,
    DeclarationCreationView,
    DeclarationDeleteView,
    ResolutionJsonView,
    DeclarationEditView,
    ResolutionUpdateView,
    ResolutionPublishView,
    ResolutionUnpublishView,
    ResolutionDeleteView,
    AboutView,
    NewsView,
    UpdatedResolutionsView,
    ReportView,
    RemoveReportView,
    ControversialResolutionsView,
    TosView,
    SearchView,
    NotificationsView,
    DeclarationSupportView,
    DeclarationUnsupportView,
    StatsView,
    FallaciesView,
    FeaturedJSONView,
    NewsJSONView,
    RandomResolutionView,
)


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("notifications", NotificationsView.as_view(), name="notifications"),
    path("featured.json", FeaturedJSONView.as_view(), name="resolutions_featured_json"),
    path("news.json", NewsJSONView.as_view(), name="resolutions_latest_json"),
    path("news", NewsView.as_view(), name="resolutions_latest"),
    path("search", SearchView.as_view(), name="resolutions_search"),
    path("random", RandomResolutionView.as_view(), name="resolutions_random"),
    path("updated", UpdatedResolutionsView.as_view(), name="resolutions_updated"),
    path(
        "controversial",
        ControversialResolutionsView.as_view(),
        name="resolutions_controversial",
    ),
    path("stats", StatsView.as_view(), name="resolutions_stats"),
    path("fallacies", FallaciesView.as_view(), name="fallacies"),
    path("about", AboutView.as_view(), name="about"),
    path("tos", TosView.as_view(), name="tos"),
    path("new-resolution", ResolutionCreationView.as_view(), name="new_resolution"),
    re_path(
        r"^(?P<slug>[\w-]+)/edit$",
        ResolutionUpdateView.as_view(),
        name="resolution_edit",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)\.json$",
        ResolutionJsonView.as_view(),
        name="resolution_detail_json",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)$", ResolutionDetailView.as_view(), name="resolution_detail"
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/(?P<declaration_id>[\d+]+)$",
        ResolutionDetailView.as_view(),
        name="declaration_detail",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/declarations/(?P<pk>[0-9]+)/unsupport",
        DeclarationUnsupportView.as_view(),
        name="unsupport_declaration",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/declarations/(?P<pk>[0-9]+)/support",
        DeclarationSupportView.as_view(),
        name="support_declaration",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/declarations/(?P<pk>[0-9]+)/delete",
        DeclarationDeleteView.as_view(),
        name="delete_declaration",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/declarations/(?P<pk>[0-9]+)/report",
        ReportView.as_view(),
        name="report_declaration",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/declarations/(?P<pk>[0-9]+)/unreport",
        RemoveReportView.as_view(),
        name="unreport_declaration",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/declarations/(?P<pk>[0-9]+)/new",
        DeclarationCreationView.as_view(),
        name="insert_declaration",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/declarations/(?P<pk>[0-9]+)",
        DeclarationEditView.as_view(),
        name="edit_declaration",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/declarations/new",
        DeclarationCreationView.as_view(),
        name="new_declaration",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/publish",
        ResolutionPublishView.as_view(),
        name="resolution_publish",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/unpublish",
        ResolutionUnpublishView.as_view(),
        name="resolution_unpublish",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/delete",
        ResolutionDeleteView.as_view(),
        name="resolution_delete",
    ),
]
