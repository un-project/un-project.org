import os

from .settings import *  # noqa: F401, F403

# Use a fast password hasher in tests
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Skip whitenoise manifest — no collectstatic needed in CI
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m.lower()]  # noqa: F405

# Tests run against the Docker postgres (mapped to 5433 locally).
# myuser is superuser there so it can create/drop test_unproject.
# Override with DB_PORT env var if your setup differs.
DATABASES['default']['PORT'] = os.environ.get('DB_PORT', '5433')  # noqa: F405

# Use in-memory cache in tests — DatabaseCache requires DB access on every
# cache.clear() call which breaks tests that lack the django_db mark.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Skip all project-app migrations: every model is unmanaged so migrations don't
# create tables. Some migrations contain RunSQL that references tables which
# don't exist yet at migrate-time during test DB setup — skipping them avoids
# that chicken-and-egg problem. The schema is loaded by tests/conftest.py.
MIGRATION_MODULES = {
    'core': None,
    'countries': None,
    'meetings': None,
    'speeches': None,
    'speakers': None,
    'votes': None,
    'search': None,
    'debate': None,
    'api': None,
}
