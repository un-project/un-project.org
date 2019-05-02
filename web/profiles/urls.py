from django.urls import path, re_path
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

from profiles.views import (
    RegistrationView,
    LoginView,
    LogoutView,
    ProfileDetailView,
    ProfileUpdateView,
    ProfileChannelsGraphView,
    ProfileResolutionsView,
    ProfileDeclarationsView,
    ProfileFallaciesView,
    SpeakerDetailView,
)


urlpatterns = [
    path(
        "login/", LoginView.as_view(template_name="auth/login.html"), name="auth_login"
    ),
    path("logout/", LogoutView.as_view(), name="auth_logout"),
    path(
        "auth/profile",
        ProfileUpdateView.as_view(template_name="auth/update.html"),
        name="auth_profile_update",
    ),
    path(
        "register/",
        RegistrationView.as_view(template_name="auth/register.html"),
        name="auth_registration",
    ),
    path(
        "complete/",
        TemplateView.as_view(template_name="auth/complete.html"),
        name="auth_registration_complete",
    ),
    re_path(
        r"^users/(?P<username>[\w\._-]+)$",
        ProfileDetailView.as_view(template_name="auth/profile.html"),
        name="auth_profile",
    ),
    re_path(
        r"^users/(?P<username>[\w\._-]+)/resolutions$",
        ProfileResolutionsView.as_view(),
        name="auth_profile_resolutions",
    ),
    re_path(
        r"^users/(?P<username>[\w\._-]+)/declarations$",
        ProfileDeclarationsView.as_view(),
        name="auth_profile_declarations",
    ),
    re_path(
        r"^users/(?P<username>[\w\._-]+)/fallacies$",
        ProfileFallaciesView.as_view(),
        name="auth_profile_fallacies",
    ),
    re_path(
        r"^users/(?P<username>[\w\._-]+)/channels.json$",
        ProfileChannelsGraphView.as_view(),
        name="auth_profile_channels",
    ),
    # path(r'^password_reset/$', views.password_reset,
    #    {'template_name': 'auth/password_reset_form.html',
    #    'email_template_name': 'auth/password_reset_email.html'},
    #    name='password_reset'),
    # path(r'^password_reset/done/$', views.password_reset_done,
    #    {'template_name': 'auth/password_reset_done.html'},
    #    name='password_reset_done'),
    # path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    #    views.password_reset_confirm,
    #    {'template_name': 'auth/password_reset_confirm.html'},
    #    name='password_reset_confirm'),
    # path(r'^reset/done/$', views.password_reset_complete,
    #    {'template_name': 'auth/password_reset_complete.html'},
    #    name='password_reset_complete'),
    path(
        "password_reset/",
        auth_views.PasswordChangeView.as_view(
            template_name="auth/password_reset_form.html"
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="auth/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    re_path(
        r"^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    re_path(
        r"^speaker/(?P<slug>[\w-]+)$",
        SpeakerDetailView.as_view(),
        name="speaker_detail",
    ),
]
