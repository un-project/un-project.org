from django.core.management import BaseCommand
from declarations.models import Declaration


class Command(BaseCommand):
    def handle(self, *args, **options):
        declarations = Declaration.objects.all()

        for declaration in declarations:
            # denormalizes sibling counts
            declaration.save()
