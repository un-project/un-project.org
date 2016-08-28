# coding=utf-8
from django.core.management import BaseCommand

from resolutions.models import Declaration


class Command(BaseCommand):
    def handle(self, language='en', **kwargs):
        declarations = Declaration.objects.all()

        Declaration.nouns.through.objects.all().delete()

        for declaration in declarations:
            declaration.save_nouns()
            print declaration.title, declaration.nouns.all()
