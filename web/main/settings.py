"""
Django settings for un_project project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

from django.core.exceptions import ImproperlyConfigured


def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the %s environment variable" % var_name
        raise ImproperlyConfigured(error_msg)


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "-)wb1dj0xxl(fi(!2q4uujp891i@-pf@614kyt()17z&!fj#pz"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.twitter",
    #'allauth.socialaccount.providers.facebook',
    #'allauth.socialaccount.providers.google',
    "typogrify",
    "django_gravatar",
    "rest_framework",
    "rest_framework.authtoken",
    "profiles",
    "declarations",
    "nouns",
    "newsfeed",
    "blog",
    "api",
]
SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "i18n.middleware.SubdomainLanguageMiddleware",
    "i18n.middleware.MultipleProxyMiddleware",
]

ROOT_URLCONF = "main.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        #'DIRS': [],
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ]
        },
    }
]


WSGI_APPLICATION = "main.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        #'NAME': get_env_variable('DATABASE_NAME'),
        #'USER': get_env_variable('DATABASE_USER'),
        #'PASSWORD': get_env_variable('DATABASE_PASSWORD'),
        "NAME": "un_project",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
    "sqlite": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    },
}

PREVENT_LANGUAGE_REDIRECTION = False

REDIRECTED_PATHS = (
    "/",
    "/newsfeed",
    "/news",
    "/stats",
    "/about",
    "/blog",
    "/new-resolution",
)

DEFAULT_LANGUAGE = "en"
# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

AUTH_USER_MODEL = "profiles.Profile"

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

# LANGUAGE_CODE = 'en-us'

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGE_CODE_MAPPING = {"ch": "zh-Hans"}

LANGUAGE_CODE_MAPPING_REVERSED = {
    v.lower(): k for k, v in LANGUAGE_CODE_MAPPING.items()
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_DIRS = (os.path.join(os.path.dirname(__file__), "../static"),)

MONGODB_HOST = "localhost"
MONGODB_DATABASE = "un-project"

# Markitup Settings
# MARKITUP_SET = 'markitup/sets/markdown'
# MARKITUP_FILTER = ('markdown2.markdown', {'safe_mode': False})

# markupfield settings
import markdown
from docutils.core import publish_parts


def render_rest(markup):
    parts = publish_parts(source=markup, writer_name="html4css1")
    return parts["fragment"]


MARKUP_FIELD_TYPES = (("markdown", markdown.markdown), ("ReST", render_rest))

BLOG_FEED_TITLE = "un-project.org Blog'u"
BLOG_FEED_DESCRIPTION = "United nations project"
BLOG_URL = "http://un-project.org/blog"

# default declaration view: 'tree' or 'list'
DEFAULT_DECLARATION_VIEW = "tree"

DEFAULT_LANGUAGE = "en"

BASE_DOMAIN = "un-project.org"

AVAILABLE_LANGUAGES = ("ar", "ch", "en", "es", "fr", "ru")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "NOTSET",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "NOTSET"},
        "django.request": {
            "handlers": ["console"],
            "propagate": False,
            "level": "ERROR",
        },
    },
}

try:
    from main.settings_local import *
except ImportError:
    print("settings_local.py not found!")
