from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Refresh the unified search index materialized view (search_index).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Use a blocking full refresh instead of the default CONCURRENTLY mode.',
        )

    def handle(self, *args, **options):
        mode = '' if options['full'] else 'CONCURRENTLY'
        sql = f'REFRESH MATERIALIZED VIEW {mode} search_index'
        self.stdout.write(f'Running: {sql} ...')
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
        except Exception as e:
            self.stderr.write(self.style.WARNING(f'search_index refresh skipped: {e}'))
            return
        self.stdout.write(self.style.SUCCESS('search_index refreshed successfully.'))
