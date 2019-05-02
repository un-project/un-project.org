from django.core.management import BaseCommand
from newsfeed.models import Entry
from declarations.models import Resolution


class Command(BaseCommand):
    def handle(self, *args, **options):
        for resolution in Resolution.objects.all():
            Entry.objects.create(
                object_id=resolution.id,
                news_type=resolution.get_newsfeed_type(),
                sender=resolution.get_actor(),
                related_object=resolution.get_newsfeed_bundle(),
                date_creation=resolution.date_creation,
            )
