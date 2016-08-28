from django.core.management import BaseCommand

from resolutions.models import Declaration


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        declarations = Declaration.objects.all()

        for declaration in declarations:
            print declaration.update_declaration_weights()
