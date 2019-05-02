from datetime import datetime
from django.db.models.signals import post_delete, post_save

from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import get_language

from i18n.utils import normalize_language_code
from newsfeed.utils import get_collection
from main.utils import send_complex_mail
from declarations.models import Resolution, Declaration, Report
from declarations.signals import (
    reported_as_fallacy,
    added_declaration_for_declaration,
    added_declaration_for_resolution,
)
from profiles.signals import follow_done, unfollow_done
from newsfeed.constants import (
    NEWS_TYPE_RESOLUTION,
    NEWS_TYPE_DECLARATION,
    NEWS_TYPE_FALLACY,
    NEWS_TYPE_FOLLOWING,
)

RELATED_MODELS = {
    NEWS_TYPE_RESOLUTION: Resolution,
    NEWS_TYPE_DECLARATION: Declaration,
    NEWS_TYPE_FALLACY: Report,
}


class EntryManager:
    """
    A manager that allows you to manage newsfeed items.
    """

    def __init__(self):
        self.load()

    def load(self):
        self.collection = get_collection("newsfeed")

    def create(
        self,
        object_id,
        news_type,
        sender,
        recipients=None,
        related_object=None,
        date_creation=None,
    ):
        """
        Creates newsfeed item from provided parameters
        """

        followers = sender.followers.values_list("id", flat=True)
        recipients = (
            recipients if recipients is not None else list(followers) + [sender.pk]
        )

        entry_bundle = {
            "object_id": object_id,
            "news_type": news_type,
            "date_created": date_creation or datetime.now(),
            "sender": {"first_name": sender.first_name, "last_name": sender.las_name},
            "recipients": recipients,
        }

        # sometimes we have to create custom related object bundle.
        # for example: following actions. because user actions are
        # holding on relational database.
        if related_object is not None:
            entry_bundle["related_object"] = related_object

        self.collection.insert(entry_bundle)

    def add_to_recipients(self, following, follower):
        """
        Adds the id of follower to the recipients of
        followed profile's entries.
        """
        self.collection.update(
            {"sender.last_name": following.last_name},
            {"$push": {"recipients": follower.id}},
            multi=True,
        )

    def remove_from_recipients(self, following, follower):
        """
        Removes follower id from the recipients of followed profile's entries.
        """
        self.collection.update(
            {"sender.last_name": following.last_name},
            {"$pull": {"recipients": follower.id}},
            multi=True,
        )

    def delete(self, object_type, object_id):
        """
        Removes news entry from provided object type and object id.
        """
        self.collection.remove({"news_type": object_type, "object_id": object_id})

    def get_private_newsfeed(self, offset, limit, user):
        """
        Fetches news items from the newsfeed database
        """
        parameters = {
            "recipients": {"$in": [user.id]},
            "news_type": {
                "$in": [
                    NEWS_TYPE_RESOLUTION,
                    NEWS_TYPE_DECLARATION,
                    NEWS_TYPE_FALLACY,
                    NEWS_TYPE_FOLLOWING,
                ]
            },
        }

        newsfeed = (
            Entry.objects.collection.find(parameters)
            .sort([("date_created", -1)])
            .skip(offset)
            .limit(limit)
        )
        return map(Entry, newsfeed)

    def get_language(self):
        return normalize_language_code(get_language())

    def get_public_newsfeed(self, offset, limit):
        """
        Fetches news items from the newsfeed database
        """
        language = self.get_language()

        parameters = {
            "news_type": {
                "$in": [NEWS_TYPE_RESOLUTION, NEWS_TYPE_DECLARATION, NEWS_TYPE_FALLACY]
            },
            "related_object.language": language,
        }

        newsfeed = (
            Entry.objects.collection.find(parameters)
            .sort([("date_created", -1)])
            .skip(offset)
            .limit(limit)
        )
        return map(Entry, newsfeed)

    def get_newsfeed_of(self, user, offset, limit):
        """
        Fetches news items of specific user
        """
        parameters = {
            "sender.username": user.username,
            "news_type": {
                "$in": [
                    NEWS_TYPE_RESOLUTION,
                    NEWS_TYPE_DECLARATION,
                    NEWS_TYPE_FOLLOWING,
                ]
            },
        }

        newsfeed = (
            Entry.objects.collection.find(parameters)
            .sort([("date_created", -1)])
            .skip(offset)
            .limit(limit)
        )
        return map(Entry, newsfeed)


class Entry(dict):
    """
    A model that wraps mongodb document for newsfeed.
    """

    objects = EntryManager()

    def render(self):
        return render_to_string(
            self.get_template(), {"entry": self, "related_object": self.related_object}
        )

    __getattr__ = dict.get

    def get_template(self):
        return {
            NEWS_TYPE_RESOLUTION: "newsfeed/resolution.html",
            NEWS_TYPE_DECLARATION: "newsfeed/declaration.html",
            NEWS_TYPE_FALLACY: "newsfeed/fallacy.html",
            NEWS_TYPE_FOLLOWING: "newsfeed/following.html",
        }.get(self.news_type)

    def entry_class(self):
        return {
            NEWS_TYPE_RESOLUTION: "resolution_entry",
            NEWS_TYPE_DECLARATION: "declaration_entry",
            NEWS_TYPE_FALLACY: "fallacy_entry",
            NEWS_TYPE_FOLLOWING: "following_entry",
        }.get(self.news_type)


@receiver(post_save, sender=Resolution)
def create_resolution_entry(instance, created, **kwargs):
    """
    Creates news entries for resolutions.
    """
    # if created:
    #    Entry.objects.create(
    #        object_id=instance.id,
    #        news_type=instance.get_newsfeed_type(),
    #        sender=instance.get_actor(),
    #        related_object=instance.get_newsfeed_bundle()
    #    )


@receiver(added_declaration_for_resolution)
@receiver(added_declaration_for_declaration)
def create_declaration_entry(declaration, **kwargs):
    """
    Creates news entries for the following types:
        - Declaration
        - Report
    That models have `get_news_type` method.
    """
    user_emails = [
        user.email
        for user in declaration.parent_users
        if user.email and user.notification_email
    ]
    send_complex_mail(
        "New declaration for %s" % declaration.resolution.title,
        "email/declaration_notification.txt",
        "email/declaration_notification.html",
        "info@un-project.org",
        bcc=user_emails,
        context={"declaration": declaration},
    )

    Entry.objects.create(
        object_id=declaration.id,
        news_type=declaration.get_newsfeed_type(),
        sender=declaration.get_actor(),
        related_object=declaration.get_newsfeed_bundle(),
    )


@receiver(reported_as_fallacy)
def create_fallacy_entry(report, **kwargs):
    """
    Creates fallacy entries.
    """
    Entry.objects.create(
        object_id=report.id,
        news_type=report.get_newsfeed_type(),
        sender=report.get_actor(),
        related_object=report.get_newsfeed_bundle(),
    )


@receiver(follow_done)
def create_following_entry(follower, following, **kwargs):
    """
    Creates news entry for following actions.
    """
    Entry.objects.create(
        object_id=following.id,
        news_type=NEWS_TYPE_FOLLOWING,
        sender=follower,
        related_object=dict(
            first_name=following.first_name, last_name=following.last_name
        ),
    )


@receiver(follow_done)
def add_to_recipients(follower, following, **kwargs):
    """
    Adds the entries of followed profile to follower's newsfeed.
    """
    Entry.objects.add_to_recipients(following=following, follower=follower)


@receiver(unfollow_done)
def remove_from_recipients(follower, following, **kwargs):
    """
    Removes the entries of unfollowed profile.
    """
    Entry.objects.remove_from_recipients(following=following, follower=follower)


@receiver(post_delete, sender=Resolution)
@receiver(post_delete, sender=Declaration)
def remove_news_entry(instance, **kwargs):
    Entry.objects.delete(
        object_type=instance.get_newsfeed_type(), object_id=instance.id
    )
