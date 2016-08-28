from django.core.management import BaseCommand

from resolutions.models import Declaration


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        declarations = Declaration.objects.all()
        for declaration in declarations:
            score = declaration.calculate_score()
            declaration.score = score
            print declaration.title, ' == ', declaration.score
            declaration.save(skip_date_update=True)
