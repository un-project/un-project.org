from datetime import timedelta, datetime
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum, F
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import get_language
from django.views.generic import DetailView, CreateView, ListView
from i18n.utils import normalize_language_code
from nouns.models import Noun, Relation, Channel
from nouns.forms import RelationCreationForm
from declarations.models import Resolution
from declarations.views import HomeView
from profiles.mixins import LoginRequiredMixin
from profiles.models import Profile


class NounDetail(DetailView):
    queryset = (Noun
                .objects
                .prefetch_related('resolutions')
                .select_related('resolutions__user')
                .order_by('-date_creation'))
    template_name = "nouns/detail.html"
    partial_template_name = "nouns/partial.html"
    context_object_name = "noun"

    def get_template_names(self):
        if self.request.GET.get('partial'):
            return [self.partial_template_name]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        resolutions = (self.get_object().active_resolutions())
        indirect_resolutions = (self.get_object().indirect_resolutions())
        source = self.request.GET.get('source')
        if source:
            resolutions = resolutions.exclude(id=source)
            indirect_resolutions = indirect_resolutions.exclude(id=source)
        return super(NounDetail, self).get_context_data(
            resolutions=resolutions,
            indirect_resolutions=indirect_resolutions,
            **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.queryset,
            slug=self.kwargs['slug'],
            language=normalize_language_code(get_language())
        )


class RelationCreate(LoginRequiredMixin, CreateView):
    model = Relation
    template_name = "nouns/new_relation.html"
    form_class = RelationCreationForm
    initial = {
        'relation_type': Relation.HYPERNYM
    }

    def form_valid(self, form):
        form.instance.source = self.get_noun()
        form.instance.target = form.get_target()
        form.instance.user = self.request.user
        form.instance.is_active = False
        form.save()
        return redirect(form.instance.source)

    def get_context_data(self, **kwargs):
        noun = self.get_noun()
        return super(RelationCreate, self).get_context_data(
            noun=noun, **kwargs)

    def get_noun(self):
        return get_object_or_404(
            Noun,
            slug=self.kwargs.get('slug'),
            language=normalize_language_code(get_language())
        )


class ChannelDetail(HomeView):
    template_name = "nouns/channel_detail.html"
    paginate_by = 20
    context_object_name = "resolutions"

    def get_channel(self):
        language = normalize_language_code(get_language())
        return get_object_or_404(Channel, slug=self.kwargs['slug'],
                                 language=language)

    def get_context_data(self, **kwargs):
        channel = self.get_channel()
        return super(ChannelDetail, self).get_context_data(
            active_users=self.get_active_users(),
            channel=channel, **kwargs)

    def get_resolutions(self, paginate=True):
        channel = self.get_channel()
        nouns = channel.nouns.all()
        resolutions = (Resolution
                       .objects
                       .language()
                       .filter(is_published=True,
                               nouns__in=nouns)
                       .distinct()
                       .order_by("-date_modification"))

        if paginate:
            resolutions = (resolutions[self.get_offset(): self.get_limit()])

        return resolutions

    def get_active_users(self):
        channel = self.get_channel()
        nouns = channel.nouns.all()
        return Profile.objects.filter(
            user_declarations__resolution__nouns__in=nouns,
            user_declarations__resolution__is_published=True,
            user_declarations__date_creation__gte=datetime.today() - timedelta(days=30)
        ).annotate(
            score=Count('user_declarations__resolution', distinct=True)
        ).order_by(
            '-score'
        )[:5]
