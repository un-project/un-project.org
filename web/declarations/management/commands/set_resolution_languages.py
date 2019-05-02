from django.core.management import BaseCommand

from declarations.models import Resolution


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        (Resolution.objects.filter(language__isnull=True).update(language="tr"))
