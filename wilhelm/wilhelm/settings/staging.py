from __future__ import absolute_import

from .base import *

DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

DEVELOPMENT_SERVER = False

ALLOWED_HOSTS = configs['allowed_hosts']['staging']

STAGING_VAR_ROOT = "/tmp/var/wilhelm/"

#=============================================================================
# domain/subdomain stuff
#=============================================================================
DOMAIN_NAME = configs['domain_names']['staging']['name']
DATA_SUBDOMAIN_NAME = 'data' + '.' + DOMAIN_NAME
MAIN_SUBDOMAIN_NAME = 'www' + '.' + DOMAIN_NAME
WWWURL = 'https://www.%s' % DOMAIN_NAME
DATA_SUBDOMAIN_PROTOCOL = 'https'
DATA_PERMALINK_ROOT = DATA_SUBDOMAIN_PROTOCOL + '://' + DATA_SUBDOMAIN_NAME + '/' 
SESSION_COOKIE_DOMAIN\
    = configs['domain_names']['staging']['session_cookie_domain']


#=============================================================================
# Static files settings.
#=============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = STAGING_VAR_ROOT + 'static'

STATICFILES_DIRS = (
    os.path.join(WILHELM_ROOT, "static"),
)

#=============================================================================
# EXPERIMENT_ARCHIVES_CACHE
#=============================================================================
EXPERIMENT_ARCHIVES_CACHE = STAGING_VAR_ROOT + 'data-archives'
mk_archive_cache_dir(EXPERIMENT_ARCHIVES_CACHE, 0775)

#=============================================================================
# DATA_ARCHIVES_CACHE & MEDIA 
#=============================================================================
DATA_ARCHIVES_CACHE = STAGING_VAR_ROOT + 'cache/data'
mk_archive_cache_dir(DATA_ARCHIVES_CACHE, 0775)
MEDIA_ROOT = DATA_ARCHIVES_CACHE
MEDIA_URL = '/data-archives/'


#=============================================================================
# Database settings.
#=============================================================================
DATABASE_SETTINGS = secrets['database']['postgresql-staging']
DATABASES = {
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
# Django lockdown
#=============================================================================
MIDDLEWARE_CLASSES += ('lockdown.middleware.LockdownMiddleware',)
INSTALLED_APPS += ('lockdown',)
LOCKDOWN_PASSWORDS = configs['lockdown_passwords']

#=============================================================================
# Email on staging server
#=============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

#=============================================================================
# Xsendfile
#=============================================================================
SENDFILE_BACKEND =  'sendfile.backends.xsendfile'

#=============================================================================
# Override loggging settings
#=============================================================================
LOGFILE_DIRECTORY = '/tmp/var/wilhelm/logs/'
LOGFILE_FILENAME = DOMAIN_NAME + '.log'
mk_archive_cache_dir(LOGFILE_DIRECTORY, 0775)
LOGGING['handlers']['file']['filename']\
    = os.path.join(LOGFILE_DIRECTORY, LOGFILE_FILENAME)

#=============================================================================
# Add django_extensions to INSTALLED_APPS
#=============================================================================
INSTALLED_APPS += ('django_extensions',)


# Facebook 
fb_secrets = secrets['social_auth']['facebook-for-staging']

SOCIAL_AUTH_FACEBOOK_KEY = fb_secrets['key']
SOCIAL_AUTH_FACEBOOK_SECRET = fb_secrets['secret']

