# -*- coding: utf-8 -*-
from collections import defaultdict
from django.utils import timezone
from datetime import datetime
from math import log
from operator import itemgetter
from uuid import uuid4
from markdown2 import markdown
from unidecode import unidecode

from django.utils.html import escape
from django.core import validators
from django.conf import settings
from django.template.loader import render_to_string
from django.db import models
from django.db.models import Count, Q
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_text
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _, get_language
from django.utils.html import strip_tags
from i18n.utils import normalize_language_code

from newsfeed.constants import (
    NEWS_TYPE_FALLACY, NEWS_TYPE_DECLARATION, NEWS_TYPE_RESOLUTION)
from declarations.constants import MAX_DECLARATION_CONTENT_LENGTH
from declarations.managers import LanguageManager, DeletePreventionManager
from declarations.mixins import DeletePreventionMixin
from declarations.utils import replace_with_link
from nouns.models import Noun
from nouns.utils import build_ngrams

OBJECTION = 0
SUPPORT = 1
SITUATION = 2
NEUTRAL = 3

epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)

DECLARATION_TYPES = (
    (OBJECTION, _("but")),
    (SUPPORT, _("because")),
    (SITUATION, _("however")),
    (NEUTRAL, _("neutral")),
)

FALLACY_TYPES = (
    ("BeggingTheQuestion,", _("Begging The Question")),
    ("IrrelevantConclusion", _("Irrelevant Conclusion")),
    ("FallacyOfIrrelevantPurpose", _("Fallacy Of Irrelevant Purpose")),
    ("FallacyOfRedHerring", _("Fallacy Of Red Herring")),
    ("ResolutionAgainstTheMan", _("Resolution Against TheMan")),
    ("PoisoningTheWell", _("Poisoning The Well")),
    ("FallacyOfTheBeard", _("Fallacy Of The Beard")),
    ("FallacyOfSlipperySlope", _("Fallacy Of Slippery Slope")),
    ("FallacyOfFalseCause", _("Fallacy Of False Cause")),
    ("FallacyOfPreviousThis", _("Fallacy Of Previous This")),
    ("JointEffect", _("Joint Effect")),
    ("WrongDirection", _("Wrong Direction")),
    ("FalseAnalogy", _("False Analogy")),
    ("SlothfulInduction", _("Slothful Induction")),
    ("AppealToBelief", _("Appeal To Belief")),
    ("PragmaticFallacy", _("Pragmatic Fallacy")),
    ("FallacyOfIsToOught", _("Fallacy Of Is To Ought")),
    ("ResolutionFromForce", _("Resolution From Force")),
    ("ResolutionToPity", _("Resolution To Pity")),
    ("PrejudicialLanguage", _("Prejudicial Language")),
    ("FallacyOfSpecialPleading", _("Fallacy Of Special Pleading")),
    ("AppealToAuthority", _("Appeal To Authority"))
)


class Resolution(DeletePreventionMixin, models.Model):
    from profiles.models import State

    title = models.CharField(
        max_length=512, verbose_name=_("Resolution"),
        help_text=render_to_string("declarations/examples/resolution.html"))
    slug = models.SlugField(max_length=512, blank=True)
    description = models.TextField(
        null=True, blank=True, verbose_name=_("Description"), )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="resolutions")
    owner = models.CharField(
        max_length=255, null=True, blank=True,
        verbose_name=_("Original Discourse"),
        help_text=render_to_string("declarations/examples/owner.html"))
    sources = models.TextField(
        null=True, blank=True,
        verbose_name=_("Sources"),
        help_text=render_to_string("declarations/examples/sources.html"))
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(default=timezone.now)
    #date_creation = models.DateTimeField(auto_now_add=True)
    #date_modification = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=255, null=True, blank=True)
    language = models.CharField(max_length=5, null=True,
                                choices=[(language, language) for language in
                                         settings.AVAILABLE_LANGUAGES])
    nouns = models.ManyToManyField('nouns.Noun', blank=True,
                                   related_name="resolutions")
    related_nouns = models.ManyToManyField('nouns.Noun', blank=True,
                                           related_name="resolutions_related")
    in_favour = models.ManyToManyField(State,
                                      related_name="in_favour")
    against = models.ManyToManyField(State,
                                     related_name="against")
    abstaining = models.ManyToManyField(State,
                                        related_name="abstaining")

    score = models.FloatField(blank=True, null=True)
    objects = LanguageManager()

    class Meta:
        ordering = ["-date_creation"]

    def __unicode__(self):
        return smart_text(self.title)

    def get_declarations(self):
        return (
            self.declarations
                .filter(is_approved=True)
                .select_related('speaker', 'related_resolution')
                .prefetch_related('supporters', 'reports')
                .annotate(
                    report_count=Count('reports', distinct=True),
                    supporter_count=Count('supporters', distinct=True))
                .order_by('-weight')
        )

    def serialize(self, authenticated_user=None):
        declarations = self.get_declarations()
        main_declarations = [
            declaration.serialize(declarations, authenticated_user)
            for declaration in declarations
            if (declaration.parent_id is None)
        ]

        return {
            'id': self.id,
            'user': self.user.serialize(),
            'title': self.title,
            'description': self.description,
            'owner': self.owner,
            'sources': self.sources,
            'is_published': self.is_published,
            'slug': self.slug,
            'absolute_url': self.get_absolute_url(),
            'language': self.language,
            'full_url': self.get_full_url(),
            'declarations': main_declarations,
            'date_creation': self.date_creation,
            'overview': self.overview(main_declarations)
        }

    def partial_serialize(self, parent_id, authenticated_user=None):
        declarations = self.get_declarations()

        parent = list(declaration.serialize(declarations, authenticated_user) for declaration in declarations
                      if declaration.parent_id == parent_id)

        return {
            'id': self.id,
            'slug': self.slug,
            'absolute_url': self.get_absolute_url(),
            'language': self.language,
            'full_url': self.get_full_url(),
            'declarations': parent,
            'date_creation': self.date_creation
        }

    def overview(self, declarations=None, show_percent=True):

        if declarations is None:
            declarations = self.published_children().values('weight', 'declaration_type')

        supported = sum(declaration['weight'] + 1 for declaration in declarations
                        if declaration['declaration_type'] == SUPPORT
                        if declaration['weight'] >= 0)

        objected = sum(declaration['weight'] + 1 for declaration in declarations
                       if declaration['declaration_type'] == OBJECTION
                       if declaration['weight'] >= 0)

        total = supported + objected

        if supported > objected:
            status = 'supported'
        elif supported < objected:
            status = 'objected'
        else:
            status = 'neutral'

        if total > 0 and show_percent:
            return {
                'support': 100 * float(supported) / total,
                'objection': 100 * float(objected) / total,
                'status': status
            }

        return {
            'support': supported,
            'objection': objected,
            'status': status
        }

    @models.permalink
    def get_absolute_url(self):
        return 'resolution_detail', [self.slug]

    def epoch_seconds(self, date):
        """Returns the number of seconds from the epoch to date."""
        td = date - epoch
        return td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)

    def calculate_score(self):
        """The hot formula. Should match the equivalent function in postgres."""
        s = self.declarations.exclude(speaker__id=self.speaker.id).count()
        if s < 1:
            return 0
        order = log(max(abs(s), 1), 10)
        sign = 1 if s > 0 else -1 if s < 0 else 0
        seconds = self.epoch_seconds(self.date_creation) - 1134028003
        return round(sign * order + seconds / 45000, 7)

    def get_full_url(self):
        return "http://%(language)s.%(domain)s%(path)s" % {
            "language": self.language,
            "domain": settings.BASE_DOMAIN,
            "path": self.get_absolute_url()
        }

    def save(self, *args, **kwargs):
        """
        - Make unique slug if it is not given.
        """
        if not self.slug:
            slug = slugify(unidecode(self.title))
            duplications = Resolution.objects.filter(slug=slug)
            if duplications.exists():
                self.slug = "%s-%s" % (slug, uuid4().hex)
            else:
                self.slug = slug

        if not kwargs.pop('skip_date_update', False):
            self.date_modification = datetime.now()

        return super(Resolution, self).save(*args, **kwargs)

    def published_declarations(self, parent=None, ignore_parent=False):
        declarations = self.declarations.filter(is_approved=True)
        if ignore_parent:
            return declarations
        return declarations.filter(parent=parent)

    published_children = published_declarations

    def children_by_declaration_type(self, declaration_type=None, ignore_parent=False):
        return (self.published_declarations(ignore_parent=ignore_parent)
                .filter(declaration_type=declaration_type))

    because = curry(children_by_declaration_type,
                    declaration_type=SUPPORT, ignore_parent=True)
    but = curry(children_by_declaration_type,
                declaration_type=OBJECTION, ignore_parent=True)
    however = curry(children_by_declaration_type,
                    declaration_type=SITUATION, ignore_parent=True)

    def update_sibling_counts(self):
        for declaration in self.declarations.filter():
            declaration.update_sibling_counts()

    def last_speaker(self):
        try:
            # add date_creation
            declaration = self.declarations.order_by("-pk")[0]
        except IndexError:
            speaker = self.speaker
        else:
            speaker = declaration.speaker
        return speaker

    def last_declaration(self):
        return self.published_declarations(ignore_parent=True).latest("pk")

    def width(self):
        return self.published_children(ignore_parent=True).count()

    def get_actor(self):
        """
        Encapsulated for newsfeed app.
        """
        return self.user

    def get_newsfeed_type(self):
        return NEWS_TYPE_RESOLUTION

    def get_newsfeed_bundle(self):
        return {
            "id": self.id,
            "language": self.language,
            "title": self.title,
            "owner": self.owner,
            "uri": self.get_absolute_url()
        }

    def get_overview_bundle(self):
        return {
            "id": self.id,
            "title": self.title,
            "sender": self.user.serialize(show_email=False),
            "date_creation": self.date_creation,
            "date_modification": self.date_modification,
            "declaration_count": self.declarations.count(),
            "absolute_url": self.get_full_url(),
            "support_rate": self.overview(show_percent=True)['support']
        }

    def contributors(self):
        from profiles.models import Speaker
        # avoid circular import

        return Speaker.objects.filter(
            id__in=self.declarations.values_list("speaker_id", flat=True)
        )

    def extract_nouns(self):
        ngrams = set(build_ngrams(self.title,
                                  language=self.language))

        nouns = (
            Noun
            .objects
            .prefetch_related('keywords')
            .filter(
                Q(is_active=True),
                Q(language=self.language),
                Q(text__in=ngrams) |
                Q(keywords__text__in=ngrams,
                  keywords__is_active=True)
            )
        )

        return nouns

    def save_nouns(self):
        nouns = self.extract_nouns()
        for noun in nouns:
            self.nouns.add(noun)

    def formatted_title(self, tag='a'):
        language = normalize_language_code(get_language())
        title = strip_tags(self.title)
        select = {'length': 'Length(nouns_noun.text)'}
        nouns = (self
                 .nouns
                 .extra(select=select)
                 .filter(language=language)
                 .prefetch_related('keywords')
                 .order_by('-length'))

        for noun in nouns:
            keywords = (
                noun.active_keywords().values_list(
                    'text', flat=True
                )
            )
            sorted_keywords = sorted(
                keywords,
                key=len,
                reverse=True
            )

            for keyword in sorted_keywords:
                replaced = replace_with_link(
                    title,
                    keyword,
                    noun.get_absolute_url(),
                    tag
                )

                if replaced is not None:
                    title = replaced
                    continue

            replaced = replace_with_link(
                title,
                noun.text,
                noun.get_absolute_url(),
                tag
            )

            if replaced is not None:
                title = replaced

        return title

    highlighted_title = curry(formatted_title, tag='span')

    def related_resolutions(self):
        if self.related_nouns.exists():
            source = self.related_nouns
        else:
            source = self.nouns

        nouns = source.prefetch_related('out_relations')
        noun_ids = set(nouns.values_list('pk', flat=True))

        for noun in nouns.all():
            relations = set(noun.out_relations.values_list('target', flat=True))
            noun_ids = noun_ids.union(relations)

        available_nouns = (
            Noun.objects.filter(
                language=normalize_language_code(get_language()),
                id__in=noun_ids
            ).annotate(
                resolution_count=Count('resolutions'),
            ).filter(
                resolutions__is_published=True
            ).prefetch_related(
                'resolutions'
            )
        )

        serialized = [{
            'noun': noun,
            'resolutions': (
                noun
                .resolutions
                .exclude(pk=self.pk)
                .values('title', 'slug')
                .order_by('?')  # find a proper way to randomize
                                # suggestions
                [:7]
            )
        } for noun in available_nouns]

        return filter(itemgetter('resolutions'), serialized)

    def update_declaration_weights(self):
        for child in self.published_children():
            child.update_weight()

    def channel(self):
        from nouns.models import Channel

        if self.related_nouns.exists():
            nouns = self.related_nouns.all()
        else:
            nouns = self.nouns.all()

        if not nouns:
            return

        channel = Channel.objects.filter(
            nouns__in=nouns,
            language=normalize_language_code(get_language())
        ).first()

        return channel


class Declaration(DeletePreventionMixin, models.Model):
    from profiles.models import Speaker
    # avoid circular import

    resolution = models.ForeignKey(Resolution, related_name="declarations")
    speaker = models.ForeignKey(Speaker, related_name='speaker_declarations', null=True)
    #speaker = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='speaker_declarations')
    parent = models.ForeignKey("self", related_name="children",
                               null=True, blank=True,
                               verbose_name=_("Parent"),
                               help_text=_("The parent of declaration. If you don't choose " +
                                           "anything, it will be a main declaration."))
    declaration_type = models.IntegerField(
        default=NEUTRAL,
        choices=DECLARATION_TYPES, verbose_name=_("Declaration Type"),
        help_text=render_to_string("declarations/examples/declaration_type.html"))
    text = models.TextField(
        null=True, blank=True,
        verbose_name=_("Declaration Content"),
        help_text=render_to_string("declarations/examples/declaration.html"),
        validators=[validators.MaxLengthValidator(MAX_DECLARATION_CONTENT_LENGTH)])
    sources = models.TextField(
        null=True, blank=True, verbose_name=_("Sources"),
        help_text=render_to_string("declarations/examples/declaration_source.html"))
    related_resolution = models.ForeignKey(Resolution, related_name="related_declarations",
                                           blank=True, null=True,
                                           verbose_name=_('Related Resolution'),
                                           help_text=_("You can also associate your declaration "
                                                       "with a resolution."))
    is_approved = models.BooleanField(default=True, verbose_name=_("Published"))
    collapsed = models.BooleanField(default=False)
    supporters = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                        related_name="supporting")
    sibling_count = models.IntegerField(default=1)  # denormalized field
    child_count = models.IntegerField(default=1)  # denormalized field
    max_sibling_count = models.IntegerField(default=1)  # denormalized field
    #date_creation = models.DateTimeField(auto_now_add=True)
    date_creation = models.DateTimeField(default=timezone.now)
    ip_address = models.CharField(max_length=255, null=True, blank=True)
    weight = models.IntegerField(default=0)

    objects = DeletePreventionManager()

    def __unicode__(self):
        return smart_text(self.text)

    def is_collapsed(self):
        return self.report_count > 3

    def serialize(self, declaration_lookup, authenticated_speaker=None):

        if authenticated_speaker is not None:
            supported = self.supporters.filter(
                id=authenticated_speaker.id
            ).exists()
        else:
            supported = False

        children = [
            declaration.serialize(declaration_lookup, authenticated_speaker)
            for declaration in declaration_lookup
            if declaration.parent_id == self.id
        ]

        related_resolution = None

        if self.related_resolution:
            related_resolution = {
                'title': self.related_resolution.title,
                'absolute_url': self.related_resolution.get_absolute_url()
            }

        return {
            'id': self.id,
            'children': children,
            'supported_by_authenticated_speaker': supported,
            'supporter_count': self.supporter_count,
            'speaker': self.speaker.serialize(),
            'declaration_type': self.declaration_type,
            'declaration_type_label': self.get_declaration_type_display(),
            'declaration_class': self.declaration_class(),
            'text': self.text,
            'formatted_text': self.formatted_text,
            'sources': self.sources,
            'is_approved': self.is_approved,
            'is_collapsed': self.is_collapsed(),
            'max_sibling_count': self.max_sibling_count,
            'child_count': self.child_count,
            'date_creation': self.date_creation,
            'fallacies': self.fallacies(authenticated_speaker),
            'fallacy_count': self.report_count,
            'weight': self.weight,
            'related_resolution': related_resolution
        }

    @models.permalink
    def get_absolute_url(self):
        return 'declaration_detail', [self.resolution.slug, self.pk]

    def get_list_url(self):
        return '%s?view=list' % self.get_absolute_url()

    @property
    def parent_speakers(self):
        current = self
        parent_speakers_ = []
        while current.parent:
            if current.parent.speaker != self.speaker:
                parent_speakers_.append(current.parent.speaker)
            current = current.parent
        return list(set(parent_speakers_))

    def update_sibling_counts(self):
        count = self.get_siblings().count()
        self.get_siblings().update(sibling_count=count)

    def get_siblings(self):
        return Declaration.objects.filter(parent=self.parent,
                                      resolution=self.resolution)

    def published_children(self):
        return self.children.filter(is_approved=True)

    def sub_tree_ids(self, current=None, children_ids=None):
        # RETURNS ALL THE CHILD RESOLUTION IDS
        current = self if current is None else current
        children_ids = children_ids if children_ids != None else []
        for child in current.children.all():
            children_ids.append(child.id)
            self.sub_tree_ids(current=child, children_ids=children_ids)
        return children_ids

    def declaration_class(self):
        return {
            OBJECTION: "but",
            SUPPORT: "because",
            SITUATION: "however",
            NEUTRAL: "neutral"
        }.get(self.declaration_type)

    def reported_by(self, user):
        return self.reports.filter(reporter=user).exists()

    def formatted_sources(self):
        return markdown(escape(self.sources), safe_mode=True)

    def formatted_text(self):
        return markdown(escape(self.text), safe_mode=True)

    def width(self):
        return self.published_children().count()

    def fallacies(self, authenticated_user=None):
        reports = self.reports.values('fallacy_type', 'reporter_id',
                                      'reporter__username', 'reason')
        fallacies = set(report['fallacy_type'] for report in reports)
        mapping = dict(FALLACY_TYPES)

        user_reports = set()
        reasons = defaultdict(list)

        for report in reports:
            if (authenticated_user is not None and
                    report['reporter_id'] == authenticated_user.id):
                user_reports.add(report['fallacy_type'])

            if report['reason'] is not None:
                reasons[report['fallacy_type']].append({
                    'reporter': report['reporter__username'],
                    'reason': report['reason']
                })

        return [{
            'type': fallacy,
            'label': mapping.get(fallacy),
            'reasons': reasons.get(fallacy),
            'reported_by_authenticated_user': fallacy in user_reports
        } for fallacy in fallacies if fallacy]

    def get_actor(self):
        # Encapsulated for newsfeed app.
        return self.speaker

    def get_newsfeed_type(self):
        return NEWS_TYPE_DECLARATION

    def get_newsfeed_bundle(self):
        related_resolution = None

        if self.related_resolution:
            related_resolution = self.related_resolution.get_newsfeed_bundle()

        return {
            "id": self.id,
            "language": self.resolution.language,
            "declaration_type": self.declaration_type,
            "declaration_class": self.declaration_class(),
            "text": self.text,
            "sources": self.sources,
            "resolution": self.resolution.get_newsfeed_bundle(),
            'related_resolution': related_resolution
        }

    def get_parent(self):
        return self.parent or self.resolution

    def recent_supporters(self):
        return self.supporters.values("id", "username")[0:5]

    def children_by_declaration_type(self, declaration_type=None):
        return self.published_children().filter(declaration_type=declaration_type)

    def save_karma_tree(self):
        for speaker in self.parent_speakers:
            karma = speaker.calculate_karma()
            speaker.karma = karma
            speaker.save()

    def save(self, *args, **kwargs):
        # self.save_karma_tree()
        return super(Declaration, self).save(*args, **kwargs)

    because = curry(children_by_declaration_type, declaration_type=SUPPORT)
    but = curry(children_by_declaration_type, declaration_type=OBJECTION)
    however = curry(children_by_declaration_type, declaration_type=SITUATION)
    neutral = curry(children_by_declaration_type, declaration_type=NEUTRAL)

    def update_weight(self):
        weight = 1 + self.supporters.count() - self.reports.count()

        for child in self.published_children():
            child_weight = child.update_weight()

            if child.declaration_type == OBJECTION:
                weight -= child_weight

            if child.declaration_type == SUPPORT:
                weight += child_weight

        self.weight = weight
        self.save()

        return weight


class Report(models.Model):
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 related_name='reports')
    declaration = models.ForeignKey(Declaration,
                                related_name='reports',
                                blank=True,
                                null=True)
    resolution = models.ForeignKey(Resolution,
                                   related_name='reports',
                                   blank=True,
                                   null=True)
    reason = models.TextField(verbose_name=_("Reason"), null=True, blank=False,
                              help_text=_('Please explain why the declaration is a fallacy.'))
    fallacy_type = models.CharField(
        _("Fallacy Type"), choices=FALLACY_TYPES, null=True, blank=False,
        max_length=255, default="Wrong Direction",
        help_text=render_to_string("declarations/examples/fallacy.html"))

    def __unicode__(self):
        return smart_text(self.fallacy_type)

    def save_karma(self):
        karma = self.declaration.speaker.calculate_karma()
        self.declaration.speaker.karma = karma
        self.declaration.speaker.save()

    def save(self, *args, **kwargs):
        self.save_karma()
        return super(Report, self).save(*args, **kwargs)

    def get_actor(self):
        """
        Encapsulated for newsfeed app.
        """
        return self.reporter

    def get_newsfeed_type(self):
        return NEWS_TYPE_FALLACY

    def get_newsfeed_bundle(self):
        return {
            "language": self.resolution.language,
            "reason": self.reason,
            "fallacy_type": self.fallacy_type,
            "declaration": self.declaration.get_newsfeed_bundle(),
            "resolution": self.resolution.get_newsfeed_bundle()
        }
