"""
Management command: listen for PostgreSQL NOTIFY on channel 'un_data_updated'.

When a notification arrives the command:
  1. Calls refresh_search_index --full to rebuild the search materialized view.
  2. Clears the Django cache so all Gunicorn workers pick up fresh data on the
     next request.

Run as a long-lived process (one container / systemd unit).  The connection is
kept alive with a periodic keepalive SELECT and reconnects automatically on
transient failures.
"""

import logging
import select
import time

import psycopg2
import psycopg2.extensions
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

CHANNEL = 'un_data_updated'
RECONNECT_DELAY = 10   # seconds between reconnect attempts
KEEPALIVE_INTERVAL = 60  # seconds between idle keepalive SELECTs


def _dsn():
    db = settings.DATABASES['default']
    return (
        f"dbname={db['NAME']} user={db['USER']} password={db['PASSWORD']} "
        f"host={db['HOST']} port={db['PORT']}"
    )


class Command(BaseCommand):
    help = 'Listen for un_data_updated NOTIFY and refresh search index + cache'

    def handle(self, *args, **options):
        self.stdout.write(f'Listening on PostgreSQL channel "{CHANNEL}" …')
        while True:
            try:
                self._listen_loop()
            except Exception as exc:
                logger.error('Listener error: %s — reconnecting in %ds', exc, RECONNECT_DELAY)
                self.stderr.write(f'Error: {exc}  (retry in {RECONNECT_DELAY}s)')
                time.sleep(RECONNECT_DELAY)

    def _listen_loop(self):
        conn = psycopg2.connect(_dsn())
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            cur.execute(f'LISTEN {CHANNEL};')
        self.stdout.write('Connected and listening.')

        last_keepalive = time.monotonic()
        while True:
            # Block until data arrives or keepalive timeout
            timeout = max(0, KEEPALIVE_INTERVAL - (time.monotonic() - last_keepalive))
            ready = select.select([conn], [], [], timeout)[0]

            if ready:
                conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop(0)
                    self._on_notify(notify.payload)
            else:
                # Keepalive: send a trivial query to prevent idle disconnects
                with conn.cursor() as cur:
                    cur.execute('SELECT 1')
                last_keepalive = time.monotonic()

    def _on_notify(self, payload):
        self.stdout.write(f'Received notification: payload={payload!r}')
        logger.info('Received %s notification: %s', CHANNEL, payload)

        self.stdout.write('Refreshing search index …')
        try:
            call_command('refresh_search_index', full=True, verbosity=0)
            self.stdout.write('Search index refreshed.')
        except Exception as exc:
            logger.error('refresh_search_index failed: %s', exc)
            self.stderr.write(f'refresh_search_index error: {exc}')

        self.stdout.write('Clearing cache …')
        try:
            cache.clear()
            self.stdout.write('Cache cleared.')
        except Exception as exc:
            logger.error('cache.clear() failed: %s', exc)
            self.stderr.write(f'cache.clear() error: {exc}')
