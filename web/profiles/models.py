# -*- coding: utf-8 -*-

from unidecode import unidecode
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Count
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
#from declarations.models import Report, Declaration
from declarations.signals import (reported_as_fallacy, added_declaration_for_declaration,
                              added_declaration_for_resolution,
                              supported_a_declaration)
from profiles.signals import follow_done
from django.utils.translation import ugettext_lazy as _

from django.core.mail import send_mail


class State(models.Model):
    iso_3166_alpha2 = models.CharField(max_length=2, default="")
    iso_3166_alpha3 = models.CharField(max_length=3, default="")
    iso_3166_numeric = models.CharField(max_length=3, default="")
    fips = models.CharField(max_length=2, default="")
    name = models.CharField(max_length=255, default="")
    capital = models.CharField(max_length=255, default="")
    area_in_km2 = models.FloatField(blank=True, null=True)
    population = models.IntegerField(blank=True, null=True)
    continent = models.CharField(max_length=2, default="")
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_created']


class Speaker(models.Model):
    first_name = models.CharField(max_length=255, db_index=True, default="")
    last_name = models.CharField(max_length=255, db_index=True, default="")
    date_creation = models.DateTimeField(auto_now_add=True)
    followers = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                        related_name="following")
    slug = models.CharField(max_length=255, blank=True)
    state = models.ForeignKey(State, related_name="speakers", null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            slug = slugify(unidecode(self.last_name))
            duplications = Speaker.objects.filter(slug=slug)
            if duplications.exists():
                self.slug = "%s-%s" % (slug, uuid4().hex)
            else:
                self.slug = slug
        return super(Speaker, self).save(*args, **kwargs)

    def serialize(self):
        bundle = {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'state': self.state,
            'id': self.id
        }

        return bundle

    @property
    def supported_declaration_count(self):
        return self.declaration_set.aggregate(Count('supporters'))[
            'supporters__count']

    @models.permalink
    def get_absolute_url(self):
        return 'speaker_detail', [self.slug]

    #def calculate_karma(self):
    #    from declarations.models import Declaration
    #    # avoid circular import

    #    # CALCULATES THE KARMA POINT OF REPRESENTATIVE
    #    # ACCORDING TO HOW MANY TIMES SUPPORTED * 2
    #    # DECREASE BY FALLACY COUNT * 2
    #    # HOW MANY CHILD DECLARATIONS ARE ADDED TO REPSENTATIVE'S DECLARATIONS
    #    karma = 0
    #    support_sum = self.speaker_declarations.aggregate(
    #        Count('supporters'))
    #    karma += 2 * support_sum['supporters__count']
    #    main_declarations = self.speaker_declarations.all()
    #    all_sub_declarations = []
    #    for declaration in main_declarations:
    #        all_sub_declarations += declaration.published_children().values_list('pk',
    #                                                                     flat=True)
    #        karma -= 2 * (declaration.reports.count())
    #    not_owned_sub_declarations = Declaration.objects.\
    #        filter(id__in=all_sub_declarations).\
    #        exclude(speaker__id=self.id).count()
    #    karma += not_owned_sub_declarations
    #    return karma


class Profile(AbstractUser):
    notification_email = models.BooleanField(_('email notification'), default=True)
    karma = models.IntegerField(null=True, blank=True)
    twitter_username = models.CharField(max_length=255, blank=True, null=True)

    def serialize(self, show_email=True):
        bundle = {
            'username': self.username,
            'id': self.id
        }

        if show_email:
            bundle.update({
                'email': self.email
            })

        return bundle

    @property
    def supported_declaration_count(self):
        return self.declaration_set.aggregate(Count('supporters'))[
            'supporters__count']

    @models.permalink
    def get_absolute_url(self):
        return "auth_profile", [self.username]

    def calculate_karma(self):
        from declarations.models import Declaration
        # avoid circular import

        # CALCULATES THE KARMA POINT OF USER
        # ACCORDING TO HOW MANY TIMES SUPPORTED * 2
        # DECREASE BY FALLACY COUNT * 2
        # HOW MANY CHILD DECLARATIONS ARE ADDED TO USER'S DECLARATIONS
        karma = 0
        support_sum = self.user_declarations.aggregate(Count('supporters'))
        karma += 2 * support_sum['supporters__count']
        main_declarations = self.user_declarations.all()
        all_sub_declarations = []
        for declaration in main_declarations:
            all_sub_declarations += declaration.published_children().values_list('pk',
                                                                         flat=True)
            karma -= 2 * (declaration.reports.count())
        not_owned_sub_declarations = Declaration.objects.\
            filter(id__in=all_sub_declarations).\
            exclude(user__id=self.id).count()
        karma += not_owned_sub_declarations
        return karma


NOTIFICATION_ADDED_DECLARATION_FOR_RESOLUTION = 0
NOTIFICATION_ADDED_DECLARATION_FOR_DECLARATION = 1
NOTIFICATION_REPORTED_AS_FALLACY = 2
NOTIFICATION_FOLLOWED_A_SPEAKER = 3
NOTIFICATION_SUPPORTED_A_DECLARATION = 4

NOTIFICATION_TYPES = (
    (NOTIFICATION_ADDED_DECLARATION_FOR_RESOLUTION,
     "added-declaration-for-resolution"),
    (NOTIFICATION_ADDED_DECLARATION_FOR_DECLARATION,
     "added-declaration-for-declaration"),
    (NOTIFICATION_REPORTED_AS_FALLACY,
     "reported-as-fallacy"),
    (NOTIFICATION_FOLLOWED_A_SPEAKER,
     "followed"),
    (NOTIFICATION_SUPPORTED_A_DECLARATION,
     "supported-a-declaration"),
)


class Notification(models.Model):
    # sender can be `null` for system notifications
    sender = models.ForeignKey(settings.AUTH_USER_MODEL,
                               null=True, blank=True,
                               related_name="sent_notifications")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  related_name="notifications")
    date_created = models.DateTimeField(auto_now_add=True)
    notification_type = models.IntegerField(choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    target_object_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['is_read', '-date_created']

    def get_target_object(self):
        from declarations.models import Report, Declaration
        # avoid circular import

        model = {
            NOTIFICATION_ADDED_DECLARATION_FOR_RESOLUTION: Declaration,
            NOTIFICATION_ADDED_DECLARATION_FOR_DECLARATION: Declaration,
            NOTIFICATION_REPORTED_AS_FALLACY: Report,
            NOTIFICATION_FOLLOWED_A_SPEAKER: Speaker,
            NOTIFICATION_SUPPORTED_A_DECLARATION: Declaration,
        }.get(self.notification_type)

        try:
            instance = model.objects.get(pk=self.target_object_id)
        except ObjectDoesNotExist:
            instance = None

        return instance

    def render(self):
        template_name = ("notifications/%s.html" %
                         self.get_notification_type_display())
        return render_to_string(template_name, {
            "notification": self,
            "target_object": self.get_target_object()
        })


@receiver(reported_as_fallacy)
def create_fallacy_notification(sender, report, *args, **kwargs):
    Notification.objects.create(
        sender=None,  # notification should be anonymous
        recipient=report.declaration.user,
        notification_type=NOTIFICATION_REPORTED_AS_FALLACY,
        target_object_id=report.id
    )


@receiver(added_declaration_for_declaration)
def create_declaration_answer_notification(sender, declaration, *args, **kwargs):
    if declaration.user != declaration.parent.user:
        Notification.objects.create(
            sender=declaration.user,
            recipient=declaration.parent.user,
            notification_type=NOTIFICATION_ADDED_DECLARATION_FOR_DECLARATION,
            target_object_id=declaration.id
        )


@receiver(supported_a_declaration)
def create_declaration_support_notification(declaration, user, *args, **kwargs):
    Notification.objects.create(
        sender=user,
        recipient=declaration.user,
        notification_type=NOTIFICATION_SUPPORTED_A_DECLARATION,
        target_object_id=declaration.id
    )


@receiver(added_declaration_for_resolution)
def create_resolution_contribution_notification(sender, declaration, *args, **kwargs):
    if declaration.user != declaration.resolution.user:
        Notification.objects.create(
            sender=declaration.user,
            recipient=declaration.resolution.user,
            notification_type=NOTIFICATION_ADDED_DECLARATION_FOR_RESOLUTION,
            target_object_id=declaration.id
        )


@receiver(follow_done)
def create_following_notification(following, follower, **kwargs):
    """
    Sends notification to the followed user from the follower.
    """
    Notification.objects.create(
        target_object_id=follower.id,
        notification_type=NOTIFICATION_FOLLOWED_A_SPEAKER,
        sender=follower,
        recipient_id=following.id
    )
