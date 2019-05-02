# -*- coding:utf-8 -*-

import json
from datetime import timedelta
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from markdown import markdown

from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Max, Sum
from django.utils.timezone import now
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.generic import (
    DetailView,
    TemplateView,
    CreateView,
    View,
    RedirectView,
)
from django.views.generic.edit import UpdateView
from django.utils.translation import get_language
from django.db.models import Count
from django.shortcuts import render

from blog.models import Post
from declarations.models import Resolution, Declaration, Report
from declarations.forms import (
    ResolutionCreationForm,
    DeclarationCreationForm,
    DeclarationEditForm,
    ReportForm,
)
from declarations.signals import (
    added_declaration_for_declaration,
    added_declaration_for_resolution,
    reported_as_fallacy,
    supported_a_declaration,
)
from declarations.templatetags.declaration_tags import check_content_deletion
from declarations.mixins import PaginationMixin, NextURLMixin
from declarations.constants import MAX_DECLARATION_CONTENT_LENGTH
from newsfeed.models import Entry
from profiles.mixins import LoginRequiredMixin
from profiles.models import Profile, Speaker
from nouns.models import Channel

from i18n.utils import normalize_language_code


def get_ip_address(request):
    return request.META.get("REMOTE_ADDR")


class ResolutionDetailView(DetailView):
    queryset = Resolution.objects.select_related("user").prefetch_related(
        "declarations"
    )
    context_object_name = "resolution"

    def get_template_names(self):
        view = self.request.GET.get("view")
        name = settings.DEFAULT_DECLARATION_VIEW + "_view"
        if view in ["list", "tree"]:
            name = view + "_view"

        return ["declarations/%s.html" % name]

    def get_parent(self):
        declaration_id = self.kwargs.get("declaration_id")
        if declaration_id:
            return get_object_or_404(Declaration, id=declaration_id)

    def get_declarations(self):
        resolution = self.get_parent() or self.get_object()
        return resolution.published_children()

    def get_context_data(self, **kwargs):
        resolution = self.get_object()
        edit_mode = (
            self.request.user.is_superuser
            or self.request.user.is_staff
            or resolution.user == self.request.user
        )

        parent = self.get_parent()
        serialized = resolution.serialize(self.request.user)
        description = resolution.title

        if parent:
            description = parent.text
        elif serialized["declarations"]:
            description = serialized["declarations"][0]["text"]

        return super().get_context_data(
            declarations=self.get_declarations(),
            parent_declaration=parent,
            description=description,
            path=resolution.get_absolute_url(),
            edit_mode=edit_mode,
            serialized=serialized,
            maxlength=MAX_DECLARATION_CONTENT_LENGTH,
            **kwargs
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        host = request.META["HTTP_HOST"]

        if not host.startswith(settings.AVAILABLE_LANGUAGES):
            return redirect(self.object.get_full_url(), permanent=True)

        if not normalize_language_code(get_language()) == self.object.language:
            return redirect(self.object.get_full_url(), permanent=True)

        partial = request.GET.get("partial")
        level = request.GET.get("level")

        if partial:
            resolution = self.object

            try:
                serialized = resolution.partial_serialize(
                    int(partial), self.request.user
                )
            except (StopIteration, ValueError):
                raise Http404

            return render(
                request,
                "declarations/tree.html",
                {
                    "declarations": serialized["declarations"],
                    "serialized": serialized,
                    "level": int(level),
                },
            )

        return super().get(request, *args, **kwargs)


class ResolutionJsonView(DetailView):
    model = Resolution

    def render_to_response(self, context, **response_kwargs):
        resolution = self.get_object(self.get_queryset())
        return HttpResponse(
            json.dumps({"nodes": self.build_tree(resolution, self.request.user)}),
            content_type="application/json",
        )

    def build_tree(self, resolution, user):
        return {
            "name": resolution.title,
            "parent": None,
            "pk": resolution.pk,
            "owner": resolution.owner,
            "sources": resolution.sources,
            "is_singular": self.is_singular(resolution),
            "children": self.get_declarations(resolution, user),
        }

    def get_declarations(self, resolution, user, parent=None):
        children = [
            {
                "pk": declaration.pk,
                "name": declaration.text,
                "parent": parent.text if parent else None,
                "reportable_by_authenticated_user": self.user_can_report(
                    declaration, user
                ),
                "report_count": declaration.reports.count(),
                "speaker": {
                    "id": declaration.speaker.id,
                    # "username": declaration.user.username,
                    "absolute_url": reverse(
                        "auth_profile", args=[declaration.speaker.slug]
                    ),
                },
                "sources": declaration.sources,
                "declaration_type": declaration.declaration_class(),
                "children": (
                    self.get_declarations(resolution, user, parent=declaration)
                    if declaration.published_children().exists()
                    else []
                ),
            }
            for declaration in resolution.published_declarations(parent)
        ]
        return children

    def user_can_report(self, declaration, user):
        if user.is_authenticated:
            return not declaration.reported_by(user)

        return False

    def is_singular(self, resolution):
        result = resolution.declarations.all().aggregate(
            max_sibling=Max("sibling_count")
        )
        return result["max_sibling"] <= 1


class HomeView(TemplateView, PaginationMixin):
    template_name = "index.html"
    tab_class = "featured"

    paginate_by = 20

    def get_context_data(self, **kwargs):
        resolutions = self.get_resolutions()
        if self.request.user.is_authenticated:
            notifications_qs = self.get_unread_notifications()
            notifications = list(notifications_qs)
            self.mark_as_read(notifications_qs)
        else:
            notifications = None
        return super().get_context_data(
            channels=self.get_channels(),
            next_page_url=self.get_next_page_url(),
            tab_class=self.tab_class,
            notifications=notifications,
            has_next_page=self.has_next_page(),
            announcements=self.get_announcements(),
            resolutions=resolutions,
            **kwargs
        )

    def get_announcements(self):
        return Post.objects.filter(is_announcement=True)

    def get_unread_notifications(self):
        return self.request.user.notifications.filter(is_read=False)[:5]

    def mark_as_read(self, notifications):
        pks = notifications.values_list("id", flat=True)
        (self.request.user.notifications.filter(id__in=pks).update(is_read=True))

    def get_resolutions(self, paginate=True):
        resolutions = (
            Resolution.objects.language()
            .filter(is_featured=True)
            .order_by("-date_modification")
        )

        if not resolutions.exists():
            resolutions = (
                Resolution.objects.language()
                .annotate(declaration_count=Sum("declarations"))
                .order_by("-declaration_count")
            )

        if paginate:
            resolutions = resolutions[self.get_offset() : self.get_limit()]

        return resolutions

    def get_channels(self):
        return Channel.objects.filter(
            language=normalize_language_code(get_language())
        ).order_by("order")


class NotificationsView(LoginRequiredMixin, HomeView):
    template_name = "notifications.html"

    def get_context_data(self, **kwargs):
        notifications_qs = self.request.user.notifications.all()[:40]
        notifications = list(notifications_qs)
        self.mark_as_read(notifications_qs)
        return super().get_context_data(notifications=notifications, **kwargs)


class FallaciesView(HomeView, PaginationMixin):
    tab_class = "fallacies"
    template_name = "fallacies.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        language = normalize_language_code(get_language())
        fallacies = Report.objects.filter(
            reason__isnull=False, resolution__language=language
        ).order_by("-id")[self.get_offset() : self.get_limit()]
        return super().get_context_data(fallacies=fallacies, **kwargs)


class SearchView(HomeView):
    tab_class = "search"
    template_name = "search/search.html"
    partial_templates = {
        "resolutions": "search/resolution.html",
        "speakers": "search/speaker.html",
        "users": "search/profile.html",
        "declarations": "search/declaration.html",
    }

    method_mapping = {
        "resolutions": "get_resolutions",
        "speakers": "get_speakers",
        "users": "get_users",
        "declarations": "get_declarations",
    }

    def dispatch(self, request, *args, **kwargs):
        self.type = request.GET.get("type", "resolutions")
        if not self.method_mapping.get(self.type):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get_keywords(self):
        return self.request.GET.get("keywords") or ""

    def is_json(self):
        return self.request.is_ajax() or self.request.GET.get("json")

    def has_next_page(self):
        method = getattr(self, self.method_mapping[self.type])
        total = method().count()
        return total > (self.get_offset() + self.paginate_by)

    def get_search_bundle(self):
        method = getattr(self, self.method_mapping[self.type])
        return [
            {"template": self.partial_templates[self.type], "object": item}
            for item in method()
        ]

    def get_context_data(self, **kwargs):
        return super().get_context_data(results=self.get_search_bundle(), **kwargs)

    def get_next_page_url(self):
        offset = self.get_offset() + self.paginate_by
        return "?offset=%(offset)s&keywords=%(keywords)s&type=%(type)s" % {
            "offset": offset,
            "type": self.type,
            "keywords": self.get_keywords(),
        }

    def get_declarations(self, paginate=True):
        keywords = self.request.GET.get("keywords")
        if not keywords or len(keywords) < 3:
            result = Declaration.objects.none()
        else:
            result = Declaration.objects.filter(
                resolution__language=normalize_language_code(get_language()),
                text__contains=keywords,
            )
            if paginate:
                result = result[self.get_offset() : self.get_limit()]
        return result

    def get_speakers(self, paginate=True):
        keywords = self.request.GET.get("keywords")
        if not keywords or len(keywords) < 2:
            result = Speaker.objects.none()
        else:
            result = Speaker.objects.filter(last_name__icontains=keywords)
            if paginate:
                result = result[self.get_offset() : self.get_limit()]
        return result

    def get_users(self, paginate=True):
        keywords = self.request.GET.get("keywords")
        if not keywords or len(keywords) < 2:
            result = Profile.objects.none()
        else:
            result = Profile.objects.filter(last_name__icontains=keywords)
            if paginate:
                result = result[self.get_offset() : self.get_limit()]
        return result

    def get_resolutions(self, paginate=True):
        keywords = self.request.GET.get("keywords")
        if not keywords or len(keywords) < 2:
            result = Resolution.objects.none()
        else:
            result = Resolution.objects.filter(
                title__icontains=keywords,
                language=normalize_language_code(get_language()),
            )

            if paginate:
                result = result[self.get_offset() : self.get_limit()]

        return result

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        if not self.is_json():
            return super().render_to_response(context, **response_kwargs)

        results = [
            {"id": result["object"].id, "label": unicode(result["object"])}
            for result in context["results"]
        ]

        return HttpResponse(
            json.dumps(results),
            dict(content_type="application/json", **response_kwargs),
        )


class NewsView(HomeView):
    tab_class = "news"

    def get_resolutions(self, paginate=True):
        resolutions = (
            Resolution.objects.language()
            .filter(is_published=True)
            .order_by("-date_modification")
        )

        if paginate:
            resolutions = resolutions[self.get_offset() : self.get_limit()]

        return resolutions


class FeaturedJSONView(HomeView):
    def render_to_response(self, context, **response_kwargs):
        resolutions = [
            resolution.get_overview_bundle() for resolution in self.get_resolutions()
        ]
        return HttpResponse(
            json.dumps({"resolutions": resolutions}, cls=DjangoJSONEncoder),
            content_type="application/json",
        )


class NewsJSONView(NewsView):
    def render_to_response(self, context, **response_kwargs):
        resolutions = [
            resolution.get_overview_bundle() for resolution in self.get_resolutions()
        ]
        return HttpResponse(
            json.dumps({"resolutions": resolutions}, cls=DjangoJSONEncoder),
            content_type="application/json",
        )


class StatsView(HomeView):
    tab_class = "stats"
    template_name = "stats.html"
    partial_templates = {
        Speaker: "stats/speaker.html",
        Profile: "stats/profile.html",
        Resolution: "stats/resolution.html",
        Declaration: "stats/declaration.html",
    }

    method_mapping = {
        "active_speakers": "get_active_speakers",
        "user_karma": "get_user_karma",
        "disgraced_speakers": "get_disgraced_speakers",
        "supported_declarations": "get_supported_declarations",
        "fallacy_declarations": "get_fallacy_declarations",
        "crowded_resolutions": "get_crowded_resolutions",
    }

    time_ranges = [7, 30]

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            stats=self.get_stats_bundle(),
            stats_type=self.get_stats_type(),
            days=self.days,
            **kwargs
        )

    def get_stats_type(self):
        return self.request.GET.get("what")

    def build_time_filters(self, date_field="date_creation"):
        days = self.request.GET.get("days")

        if not days or days == "all":
            self.days = None
            return {}

        try:
            days = int(days)
        except (TypeError, ValueError):
            days = None

        if not days or days not in self.time_ranges:
            raise Http404()

        self.days = days

        field_expression = "%s__gt" % date_field

        return {field_expression: timezone.now() - timedelta(days=days)}

    def get_stats_bundle(self):
        stat_type = self.get_stats_type()
        if stat_type not in self.method_mapping:
            raise Http404()
        method = getattr(self, self.method_mapping[stat_type])
        return [
            {"template": self.partial_templates[type(item)], "object": item}
            for item in method()
        ]

    def get_active_speakers(self):
        return (
            Speaker.objects.annotate(declaration_count=Sum("speaker_declarations"))
            .filter(
                declaration_count__gt=0,
                **self.build_time_filters(
                    date_field="speaker_declarations__date_creation"
                )
            )
            .order_by("-declaration_count")[:10]
        )

    def get_user_karma(self):
        return (
            Profile.objects.filter(
                karma__gt=0,
                **self.build_time_filters(date_field="user_declarations__date_creation")
            )
            .order_by("-karma", "id")
            .distinct()[:10]
        )

    def get_disgraced_speakers(self):
        return (
            Speaker.objects.annotate(report_count=Sum("speaker_declarations__reports"))
            .filter(
                report_count__gt=0,
                **self.build_time_filters(
                    date_field="speaker_declarations__date_creation"
                )
            )
            .order_by("-report_count")[:10]
        )

    def get_supported_declarations(self):
        return (
            Declaration.objects.annotate(supporter_count=Sum("supporters"))
            .filter(
                resolution__language=get_language(),
                supporter_count__gt=0,
                **self.build_time_filters(date_field="date_creation")
            )
            .order_by("-supporter_count")[:50]
        )

    def get_fallacy_declarations(self):
        return (
            Declaration.objects.annotate(report_count=Sum("reports"))
            .filter(
                report_count__gt=0,
                **self.build_time_filters(date_field="date_creation")
            )
            .order_by("-report_count")[:10]
        )

    def get_crowded_resolutions(self):
        return (
            Resolution.objects.annotate(declaration_count=Sum("declarations"))
            .filter(
                language=normalize_language_code(get_language()),
                declaration_count__gt=0,
                **self.build_time_filters(date_field="date_creation")
            )
            .order_by("-declaration_count")[:10]
        )


class UpdatedResolutionsView(HomeView):
    tab_class = "updated"

    def get_resolutions(self, paginate=True):
        resolutions = Resolution.objects.filter(is_published=True).order_by(
            "-date_modification"
        )

        if paginate:
            resolutions = resolutions[self.get_offset() : self.get_limit()]

        return resolutions


class ControversialResolutionsView(HomeView):
    tab_class = "controversial"

    def get_resolutions(self, paginate=True):
        last_week = now() - timedelta(days=3)
        resolutions = (
            Resolution.objects.annotate(num_children=Count("declarations"))
            .order_by("-num_children")
            .filter(date_modification__gte=last_week)
        )
        if paginate:
            return resolutions[self.get_offset() : self.get_limit()]

        return resolutions


class AboutView(TemplateView):
    template_name = "about.html"

    def get_text_file(self):
        language = get_language()
        return render_to_string("about-%s.md" % language)

    def get_context_data(self, **kwargs):
        content = markdown(self.get_text_file())
        return super().get_context_data(content=content, **kwargs)


class TosView(TemplateView):
    template_name = "tos.html"

    def get_context_data(self, **kwargs):
        content = markdown(render_to_string("tos.md"))
        return super().get_context_data(content=content, **kwargs)


class ResolutionCreationView(LoginRequiredMixin, CreateView):
    template_name = "declarations/new_resolution.html"
    form_class = ResolutionCreationForm

    help_texts = {
        "title": "declarations/examples/resolution.html",
        "owner": "declarations/examples/owner.html",
        "sources": "declarations/examples/sources.html",
    }

    def get_form_class(self):
        form_class = self.form_class
        for key, value in self.help_texts.items():
            help_text = render_to_string(value)
            form_class.base_fields[key].help_text = help_text
        return form_class

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.ip_address = get_ip_address(self.request)
        form.instance.language = normalize_language_code(get_language())
        form.instance.is_published = True
        response = super().form_valid(form)
        form.instance.update_sibling_counts()
        form.instance.save_nouns()
        form.instance.save()
        return response


class ResolutionUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "declarations/edit_resolution.html"
    form_class = ResolutionCreationForm

    def get_queryset(self):
        resolutions = Resolution.objects.all()
        if self.request.user.is_superuser:
            return resolutions
        return resolutions.filter(user=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        form.instance.update_sibling_counts()
        form.instance.nouns.clear()
        form.instance.save_nouns()
        form.instance.update_declaration_weights()
        form.instance.save()
        return response


class RandomResolutionView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        resolution = (
            Resolution.objects.annotate(declaration_count=Count("declarations"))
            .filter(
                declaration_count__gt=2,
                language=normalize_language_code(get_language()),
            )
            .order_by("?")[0]
        )
        return resolution.get_absolute_url()


class ResolutionPublishView(LoginRequiredMixin, DetailView):
    def get_queryset(self):
        return Resolution.objects.filter(user=self.request.user)

    def post(self, request, slug):
        resolution = self.get_object()
        resolution.is_published = True
        resolution.save()
        messages.info(request, u"Resolution is published now.")
        return redirect(resolution)


class ResolutionUnpublishView(LoginRequiredMixin, DetailView):
    def get_queryset(self):
        return Resolution.objects.filter(user=self.request.user)

    def post(self, request, slug):
        resolution = self.get_object()
        resolution.is_published = False
        resolution.save()
        messages.info(request, u"Resolution is unpublished now.")
        return redirect(resolution)


class ResolutionDeleteView(LoginRequiredMixin, DetailView):
    def get_queryset(self):
        return Resolution.objects.filter(user=self.request.user)

    def post(self, request, slug):
        resolution = self.get_object()
        if check_content_deletion(resolution):
            # remove notification
            Entry.objects.delete(resolution.get_newsfeed_type(), resolution.id)
            resolution.delete()
            messages.info(request, u"Resolution has been removed.")
            return redirect("home")
        else:
            messages.info(request, u"Resolution cannot be deleted.")
            return redirect(resolution)

    delete = post


class DeclarationEditView(LoginRequiredMixin, UpdateView):
    template_name = "declarations/edit_declaration.html"
    form_class = DeclarationEditForm

    help_texts = {
        "declaration_type": "declarations/examples/declaration_type.html",
        "text": "declarations/examples/declaration.html",
        "sources": "declarations/examples/declaration_source.html",
    }

    def get_form_class(self):
        form_class = self.form_class
        for key, value in self.help_texts.items():
            help_text = render_to_string(value)
            form_class.base_fields[key].help_text = help_text
        return form_class

    def get_queryset(self):
        declarations = Declaration.objects.all()
        # if self.request.user.is_superuser:
        #    return declarations
        # return declarations.filter(user=self.request.user)
        return declarations

    def form_valid(self, form):
        response = super().form_valid(form)
        form.instance.resolution.update_sibling_counts()
        return response

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)


class DeclarationCreationView(NextURLMixin, LoginRequiredMixin, CreateView):
    template_name = "declarations/new_declaration.html"
    form_class = DeclarationCreationForm

    help_texts = {
        "declaration_type": "declarations/examples/declaration_type.html",
        "text": "declarations/examples/declaration.html",
        "sources": "declarations/examples/declaration_source.html",
    }

    def get_form_class(self):
        form_class = self.form_class
        for key, value in self.help_texts.items():
            help_text = render_to_string(value)
            form_class.base_fields[key].help_text = help_text
        return form_class

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            resolution=self.get_resolution(),
            view=self.get_view_name(),
            parent=self.get_parent(),
            **kwargs
        )

    def form_valid(self, form):
        resolution = self.get_resolution()
        form.instance.user = self.request.user
        form.instance.resolution = resolution
        form.instance.parent = self.get_parent()
        form.instance.is_approved = True
        form.instance.ip_address = get_ip_address(self.request)
        form.save()
        resolution.update_sibling_counts()

        if form.instance.parent:
            added_declaration_for_declaration.send(
                sender=self, declaration=form.instance
            )
        else:
            added_declaration_for_resolution.send(
                sender=self, declaration=form.instance
            )

        resolution.date_modification = timezone.now()
        resolution.update_declaration_weights()
        resolution.save()

        return redirect(form.instance.get_absolute_url() + self.get_next_parameter())

    def get_resolution(self):
        return get_object_or_404(Resolution, slug=self.kwargs["slug"])

    def get_parent(self):
        parent_pk = self.kwargs.get("pk")
        if parent_pk:
            return get_object_or_404(Declaration, pk=parent_pk)


class DeclarationSupportView(NextURLMixin, LoginRequiredMixin, View):
    def get_declaration(self):
        declarations = Declaration.objects.all()
        # declarations = Declaration.objects.exclude(user=self.request.user)
        return get_object_or_404(declarations, pk=self.kwargs["pk"])

    def post(self, request, *args, **kwargs):
        declaration = self.get_declaration()
        declaration.supporters.add(self.request.user)
        supported_a_declaration.send(
            sender=self, declaration=declaration, user=self.request.user
        )
        declaration.resolution.update_declaration_weights()

        if request.is_ajax():
            return HttpResponse(status=201)

        return redirect(
            declaration.get_parent().get_absolute_url()
            + self.get_next_parameter()
            + "#%s" % declaration.pk
        )

    def get_resolution(self):
        return get_object_or_404(Resolution, slug=self.kwargs["slug"])


class DeclarationUnsupportView(DeclarationSupportView):
    def delete(self, request, *args, **kwargs):
        declaration = self.get_declaration()
        declaration.supporters.remove(self.request.user)
        declaration.resolution.update_declaration_weights()

        if request.is_ajax():
            return HttpResponse(status=204)

        return redirect(
            declaration.get_parent().get_absolute_url()
            + self.get_next_parameter()
            + "#%s" % declaration.pk
        )

    post = delete


class DeclarationDeleteView(LoginRequiredMixin, View):
    def get_declaration(self):
        if self.request.user.is_staff:
            declarations = Declaration.objects.all()
        else:
            declarations = Declaration.objects.filter(user=self.request.user)
        return get_object_or_404(declarations, pk=self.kwargs["pk"])

    def delete(self, request, *args, **kwargs):
        declaration = self.get_declaration()
        declaration.delete()
        declaration.update_sibling_counts()
        resolution = self.get_resolution()
        if not resolution.declarations.exists():
            resolution.is_published = False
            resolution.save()
        resolution.update_declaration_weights()
        return redirect(resolution)

    post = delete

    def get_resolution(self):
        return get_object_or_404(Resolution, slug=self.kwargs["slug"])


class ReportView(NextURLMixin, LoginRequiredMixin, CreateView):
    form_class = ReportForm
    template_name = "declarations/report.html"

    def get_form_class(self):
        form = self.form_class
        help_text = render_to_string("declarations/examples/fallacy.html")
        form.base_fields["fallacy_type"].help_text = help_text
        return form

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            declaration=self.get_declaration(), view=self.get_view_name(), **kwargs
        )

    def get_resolution(self):
        return get_object_or_404(Resolution, slug=self.kwargs["slug"])

    def get_declaration(self):
        return get_object_or_404(Declaration, pk=self.kwargs["pk"])

    def get_initial(self):
        return {
            "resolution": self.get_resolution(),
            "declaration": self.get_declaration(),
            "reporter": self.request.user,
        }

    def form_valid(self, form):
        resolution = self.get_resolution()
        declaration = self.get_declaration()
        form.instance.resolution = resolution
        form.instance.declaration = declaration
        form.instance.reporter = self.request.user
        form.save()
        reported_as_fallacy.send(sender=self, report=form.instance)
        resolution.update_declaration_weights()
        return redirect(
            declaration.get_parent().get_absolute_url()
            + self.get_next_parameter()
            + "#%s" % declaration.pk
        )


class RemoveReportView(NextURLMixin, LoginRequiredMixin, View):
    def get_declaration(self):
        return get_object_or_404(Declaration, pk=self.kwargs["pk"])

    def post(self, request, *args, **kwargs):
        declaration = self.get_declaration()
        declaration.reports.filter(
            reporter=request.user, fallacy_type=request.GET.get("type")
        ).delete()
        return redirect(
            declaration.get_parent().get_absolute_url()
            + self.get_next_parameter()
            + "#%s" % declaration.pk
        )
