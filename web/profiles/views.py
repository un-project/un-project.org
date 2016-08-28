import json
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.translation import get_language
from django.views.generic import (
    FormView, CreateView, RedirectView, DetailView, UpdateView)
from django.db.models import Q, Count
from networkx import DiGraph
from networkx.readwrite import json_graph
from i18n.utils import normalize_language_code
from nouns.models import Noun, Channel

from profiles.mixins import LoginRequiredMixin
from profiles.forms import (RegistrationForm, AuthenticationForm,
                            ProfileUpdateForm)
from profiles.models import Profile, Speaker
from declarations.models import Resolution, Declaration, SUPPORT, OBJECTION, SITUATION, Report
from declarations.mixins import PaginationMixin
from newsfeed.models import Entry


class RegistrationView(CreateView):
    form_class = RegistrationForm
    template_name = "auth/register.html"

    def form_valid(self, form):
        response = super(RegistrationView, self).form_valid(form)
        user = authenticate(username=form.cleaned_data["username"],
                            password=form.cleaned_data["password1"])
        login(self.request, user)
        return response

    def get_success_url(self):
        return reverse("home")


class LoginView(FormView):
    form_class = AuthenticationForm
    template_name = "auth/login.html"

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super(LoginView, self).form_valid(form)

    def get_success_url(self):
        return self.request.GET.get("next") or reverse("home")

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context["next"] = self.request.GET.get("next", "")
        return context


class LogoutView(LoginRequiredMixin, RedirectView):
    def get(self, request, *args, **kwargs):
        logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)

    def get_redirect_url(self, **kwargs):
        return reverse("home")


class BaseSpeakerDetailView(DetailView):
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    context_object_name = "speaker"
    model = Speaker
    paginate_by = 20
    tab_name = "overview"

    def get_context_data(self, **kwargs):
        """
        Adds extra context to template
        """
        speaker = self.get_object()

        if self.request.user.is_authenticated():
            is_followed = self.request.user.following.filter(
                pk=speaker.id).exists()
        else:
            is_followed = False

        return super(BaseSpeakerDetailView, self).get_context_data(
            can_follow=True,
            is_followed=is_followed,
            tab_name=self.tab_name,
            **kwargs
        )


class SpeakerDetailView(BaseSpeakerDetailView):
    def get_context_data(self, **kwargs):
        """
        Adds extra context to template
        """
        speaker = self.get_object()
        return super(SpeakerDetailView, self).get_context_data(
            related_channels=self.get_related_channels(speaker),
            discussed_users=self.get_discussed_speakers(speaker),
            supported_declarations=self.get_supported_declarations(speaker),
            **kwargs
        )

    def get_supported_declarations(self, speaker):
        return Declaration.objects.filter(
            is_approved=True,
            speaker=speaker,
            resolution__language=normalize_language_code(get_language())
        ).annotate(
            supporter_count=Count('supporters', distinct=True)
        ).filter(
            supporter_count__gt=0
        ).order_by(
            '-supporter_count'
        )[:10]

    def get_discussed_speakers(self, speaker):
        lines = Declaration.objects.filter(
            speaker=speaker,
            parent__speaker__isnull=False,
        ).exclude(
            parent__speaker=speaker
        ).values(
            'parent__speaker'
        ).annotate(
            count=Count('parent__speaker')
        ).order_by(
            '-count'
        )[:5]

        profiles = [Profile.objects.get(id=line['parent__speaker'])
                    for line in lines]

        def make_bundle(target):
            because = self.declaration_count_by_speaker(speaker, target, SUPPORT)
            but = self.declaration_count_by_speaker(speaker, target, OBJECTION)
            however = self.declaration_count_by_speaker(speaker, target, SITUATION)
            total = because + but + however

            return {
                'speaker': profile,
                'because': 100 * float(because) / total,
                'but': 100 * float(but) / total,
                'however': 100 * float(however) / total
            }

        return [
            make_bundle(profile)
            for profile in profiles
        ]

    def declaration_count_by_speaker(self, speaker, target, declaration_type):
        return Declaration.objects.filter(
            speaker=speaker,
            parent__speaker=target,
            declaration_type=declaration_type
        ).count()

    def get_related_channels(self, speaker):
        resolution_nouns = Resolution.objects.filter(
            declarations__speaker=speaker,
            nouns__isnull=False,
            language=normalize_language_code(get_language())
        ).order_by(
            '-declarations__weight'
        ).values_list(
            'nouns',
            flat=True
        )

        #supported_nouns = Resolution.objects.filter(
        #    declarations__supporters=speaker,
        #    nouns__isnull=False,
        #    language=normalize_language_code(get_language())
        #).order_by(
        #    '-declarations__weight'
        #).values_list(
        #    'nouns',
        #    flat=True
        #)
        supported_nouns = []

        noun_ids = list(resolution_nouns) + list(supported_nouns)
        noun_set = set(noun_ids)

        channels = Channel.objects.filter(
            nouns__in=noun_ids,
            language=normalize_language_code(get_language())
        ).distinct()

        bundle = []
        total_score = 0

        for channel in channels:
            channel_dict = {
                'channel': channel.serialize(),
                'score': 0,
            }

            for noun in channel.nouns.all():
                if noun.pk in noun_set:
                    channel_dict['score'] += noun_ids.count(noun.pk)

            total_score += channel_dict['score']

            bundle.append(channel_dict)

        return sorted(bundle,
                      key=lambda c: c['score'],
                      reverse=True)


class BaseProfileDetailView(DetailView):
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = "profile"
    model = Profile
    paginate_by = 20
    tab_name = "overview"

    def get_context_data(self, **kwargs):
        """
        Adds extra context to template
        """
        user = self.get_object()

        can_follow = self.request.user != user

        if self.request.user.is_authenticated():
            is_followed = self.request.user.following.filter(
                pk=user.id).exists()
        else:
            is_followed = False

        return super(BaseProfileDetailView, self).get_context_data(
            can_follow=can_follow,
            is_followed=is_followed,
            tab_name=self.tab_name,
            **kwargs
        )


class ProfileDetailView(BaseProfileDetailView):
    def get_context_data(self, **kwargs):
        """
        Adds extra context to template
        """
        user = self.get_object()
        return super(ProfileDetailView, self).get_context_data(
            related_channels=self.get_related_channels(user),
            discussed_users=self.get_discussed_users(user),
            supported_declarations=self.get_supported_declarations(user),
            **kwargs
        )

    def get_supported_declarations(self, user):
        return Declaration.objects.filter(
            is_approved=True,
            user=user,
            resolution__language=normalize_language_code(get_language())
        ).annotate(
            supporter_count=Count('supporters', distinct=True)
        ).filter(
            supporter_count__gt=0
        ).order_by(
            '-supporter_count'
        )[:10]

    def get_discussed_users(self, user):
        lines = Declaration.objects.filter(
            user=user,
            parent__user__isnull=False,
        ).exclude(
            parent__user=user
        ).values(
            'parent__user'
        ).annotate(
            count=Count('parent__user')
        ).order_by(
            '-count'
        )[:5]

        profiles = [Profile.objects.get(id=line['parent__user'])
                    for line in lines]

        def make_bundle(target):
            because = self.declaration_count_by_user(user, target, SUPPORT)
            but = self.declaration_count_by_user(user, target, OBJECTION)
            however = self.declaration_count_by_user(user, target, SITUATION)
            total = because + but + however

            return {
                'user': profile,
                'because': 100 * float(because) / total,
                'but': 100 * float(but) / total,
                'however': 100 * float(however) / total
            }

        return [
            make_bundle(profile)
            for profile in profiles
        ]

    def declaration_count_by_user(self, user, target, declaration_type):
        return Declaration.objects.filter(
            user=user,
            parent__user=target,
            declaration_type=declaration_type
        ).count()

    def get_related_channels(self, user):
        resolution_nouns = Resolution.objects.filter(
            declarations__user=user,
            nouns__isnull=False,
            language=normalize_language_code(get_language())
        ).order_by(
            '-declarations__weight'
        ).values_list(
            'nouns',
            flat=True
        )

        supported_nouns = Resolution.objects.filter(
            declarations__supporters=user,
            nouns__isnull=False,
            language=normalize_language_code(get_language())
        ).order_by(
            '-declarations__weight'
        ).values_list(
            'nouns',
            flat=True
        )

        noun_ids = list(resolution_nouns) + list(supported_nouns)
        noun_set = set(noun_ids)

        channels = Channel.objects.filter(
            nouns__in=noun_ids,
            language=normalize_language_code(get_language())
        ).distinct()

        bundle = []
        total_score = 0

        for channel in channels:
            channel_dict = {
                'channel': channel.serialize(),
                'score': 0,
            }

            for noun in channel.nouns.all():
                if noun.pk in noun_set:
                    channel_dict['score'] += noun_ids.count(noun.pk)

            total_score += channel_dict['score']

            bundle.append(channel_dict)

        return sorted(bundle,
                      key=lambda c: c['score'],
                      reverse=True)


class ProfileResolutionsView(BaseProfileDetailView):
    tab_name = "resolutions"
    template_name = "auth/resolutions.html"

    def get_context_data(self, **kwargs):
        user = self.get_object()
        resolutions = Resolution.objects.filter(
            user=user
        ).order_by("-date_creation")

        if user != self.request.user:
            resolutions = resolutions.filter(is_published=True)

        return super(ProfileResolutionsView, self).get_context_data(
            resolutions=resolutions
        )


class ProfileFallaciesView(BaseProfileDetailView):
    tab_name = "fallacies"
    template_name = "auth/fallacies.html"

    def get_context_data(self, **kwargs):
        user = self.get_object()
        fallacies = Report.objects.filter(
            reason__isnull=False,
            reporter=user
        ).order_by('-id')

        return super(ProfileFallaciesView, self).get_context_data(
            fallacies=fallacies
        )


class ProfileDeclarationsView(BaseProfileDetailView, PaginationMixin):
    tab_name = "declarations"
    template_name = "auth/declarations.html"
    paginate_by = 20

    def get_objects(self, paginate=True):
        user = self.get_object()
        declarations = Declaration.objects.filter(user=user).order_by("-date_creation")

        if user != self.request.user:
            declarations = declarations.filter(is_approved=True)

        if paginate:
            declarations = declarations[self.get_offset():self.get_limit()]

        return declarations

    def has_next_page(self):
        total = self.get_objects(paginate=False).count()
        return total > (self.get_offset() + self.paginate_by)

    def get_context_data(self, **kwargs):
        declarations = self.get_objects()

        return super(ProfileDeclarationsView, self).get_context_data(
            declarations=declarations,
            has_next_page=self.has_next_page(),
            next_page_url=self.get_next_page_url(),
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileUpdateForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return self.request.user.get_absolute_url()


class ProfileChannelsGraphView(ProfileDetailView):
    def render_to_response(self, context, **response_kwargs):
        user = self.get_object()
        return HttpResponse(json.dumps(self.get_bundle(user)),
                            content_type="application/json")

    def get_bundle(self, user):
        graph = self.build_graph(user)
        return json_graph.node_link_data(graph)

    def build_graph(self, user):
        resolution_nouns = Resolution.objects.filter(
            declarations__user=user,
            nouns__isnull=False,
            language=normalize_language_code(get_language())
        ).order_by(
            '-declarations__weight'
        ).values_list(
            'nouns',
            flat=True
        )

        supported_nouns = Resolution.objects.filter(
            declarations__supporters=user,
            nouns__isnull=False,
            language=normalize_language_code(get_language())
        ).order_by(
            '-declarations__weight'
        ).values_list(
            'nouns',
            flat=True
        )

        noun_ids = set(resolution_nouns) ^ set(supported_nouns)

        channels = Channel.objects.filter(
            nouns__in=noun_ids,
            language=normalize_language_code(get_language())
        ).distinct()

        graph = DiGraph()

        last_channel = None
        first_channel = None

        label = lambda x: x.title()

        for channel in channels:
            graph.add_node(channel.title, {
                "label": label(channel.title),
                "type": "channel"
            })

            if last_channel:
                graph.add_edge(last_channel.title, channel.title)

            channel_nouns = channel.nouns.all()
            for channel_noun in channel_nouns:

                if channel_noun.id in noun_ids:
                    graph.add_edge(channel_noun.text, channel.title)

                    graph.add_node(channel_noun.text, {
                        "label": label(channel_noun.text),
                        "type": "noun"
                    })

            last_channel = channel
            if not first_channel:
                first_channel = channel

        graph.add_edge(first_channel.title, last_channel.title)

        return graph
