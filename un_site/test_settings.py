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
