from __future__ import absolute_import
from .base import *

#=============================================================================
# Django project parameters.
#=============================================================================

DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

DEVELOPMENT_SERVER = True

#=============================================================================
# EXPERIMENT_ARCHIVES_CACHE
#=============================================================================
EXPERIMENT_ARCHIVES_CACHE\
    = os.path.join(os.environ['HOME'], 'tmp/var/wilhelm/cache/archives')

mk_archive_cache_dir(EXPERIMENT_ARCHIVES_CACHE)

#=============================================================================
# DATA_ARCHIVES_CACHE
#=============================================================================
DATA_ARCHIVES_CACHE\
    = os.path.join(os.environ['HOME'], 'tmp/var/wilhelm/data-archives')

mk_archive_cache_dir(DATA_ARCHIVES_CACHE)
MEDIA_ROOT = DATA_ARCHIVES_CACHE
MEDIA_URL = '/data-archives/'

#=============================================================================
# Database settings.
#=============================================================================
DATABASE_SETTINGS = secrets['database']['postgresql-development']
DATABASES = {
#'default': {
#    'ENGINE': 'django.db.backends.sqlite3', 
#    'NAME': os.path.join(WILHELM_ROOT,'wilhelm.db'),                      
#}
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DATABASE_SETTINGS['name'],
        'USER': DATABASE_SETTINGS['username'],
        'PASSWORD': DATABASE_SETTINGS['password'],
        'HOST': 'localhost',
        'PORT': '',
    }
}

#=============================================================================
# Static files settings.
#=============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(os.environ['HOME'], 'tmp/var/wilhelm/static')

STATICFILES_DIRS = (
    os.path.join(WILHELM_ROOT, "static"),
)

#=============================================================================
# Email settings on development
#=============================================================================
gmail_settings = configs['email']['gmail']

EMAIL_HOST = gmail_settings['host']
EMAIL_HOST_USER = gmail_settings['host_user']
EMAIL_HOST_PASSWORD = secrets['email']['gmail_secret']
EMAIL_PORT = 587
EMAIL_USE_TLS = True

#=============================================================================
# Xsendfile
#=============================================================================
SENDFILE_BACKEND = 'sendfile.backends.development'

#=============================================================================
# Development subdomain stuff
#=============================================================================
DOMAIN_NAME = configs['domain_names']['development']['name']
DATA_SUBDOMAIN_NAME = 'data' + '.' + DOMAIN_NAME + ':8000'
MAIN_SUBDOMAIN_NAME = 'www' + '.' + DOMAIN_NAME + ':8000'
WWWURL = 'https://www.%s' % DOMAIN_NAME
DATA_SUBDOMAIN_PROTOCOL = 'http'
DATA_PERMALINK_ROOT = DATA_SUBDOMAIN_PROTOCOL + '://' + DATA_SUBDOMAIN_NAME + '/' 

#=============================================================================
# Override loggging settings
#=============================================================================
LOGFILE_DIRECTORY = os.path.join(os.environ['HOME'], 'tmp/var/wilhelm/logs/')
LOGFILE_FILENAME = DOMAIN_NAME + '.log'
mk_archive_cache_dir(LOGFILE_DIRECTORY)
LOGGING['handlers']['file']['filename']\
    = os.path.join(LOGFILE_DIRECTORY, LOGFILE_FILENAME)

#=============================================================================
# Unlimited attempts
#=============================================================================
UNLIMITED_EXPERIMENT_ATTEMPTS = True # Setting to True is useful for development

#=============================================================================
# Add django_extensions to INSTALLED_APPS
#=============================================================================
INSTALLED_APPS += ('django_extensions',)

# Facebook 
fb_secrets = secrets['social_auth']['facebook-for-development']

SOCIAL_AUTH_FACEBOOK_KEY = fb_secrets['key']
SOCIAL_AUTH_FACEBOOK_SECRET = fb_secrets['secret']
