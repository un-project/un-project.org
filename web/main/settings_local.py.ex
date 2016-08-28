DEFAULT_FROM_EMAIL = 'info@un-project.org'
POSTMARK_TOKEN = "xyz"
POSTMARK_API_URL = "https://api.postmarkapp.com/email"


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'db',
        'PORT': 5432,
    }
}
ALLOWED_HOSTS = ['*']
DEBUG = True

SERVER_EMAIL = 'info@un-project.org'
BASE_DOMAIN = 'localhost:8000' #your docker machine ip if running on virtual server
MONGODB_HOST = 'localhost' #your docker machine ip if running on virtual server
