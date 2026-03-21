"""
Production settings — import this instead of settings.py in production:

    DJANGO_SETTINGS_MODULE=un_site.settings_prod

All base settings are inherited from settings.py; this file only overrides
or adds production-specific values.
"""

from .settings import *  # noqa: F401, F403

# ── Security ──────────────────────────────────────────────────────────────────

DEBUG = False

# Enforce HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS: tell browsers to use HTTPS for 1 year; enable subdomains + preload
# once you're confident the site is HTTPS-only.
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Prevent browsers from guessing content-type
SECURE_CONTENT_TYPE_NOSNIFF = True

# Block pages from being embedded in iframes (also set by XFrameOptionsMiddleware)
X_FRAME_OPTIONS = 'DENY'

# Session / CSRF cookies only sent over HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ── Database ──────────────────────────────────────────────────────────────────

# Keep DB connections alive for 5 minutes to reduce connection overhead
DATABASES['default']['CONN_MAX_AGE'] = 300  # noqa: F405

# ── Static files ──────────────────────────────────────────────────────────────

# STATIC_ROOT is already set in settings.py (BASE_DIR / 'staticfiles').
# Run `manage.py collectstatic` before deploying; WhiteNoise serves from there.
# If you serve static files via a CDN or separate server, set STATIC_URL here:
# STATIC_URL = 'https://cdn.example.com/static/'
