from __future__ import absolute_import
from .base import *

#=============================================================================
# Django project parameters.
#=============================================================================

DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

DEVELOPMENT_SERVER = False
IS_PRODUCTION_SERVER = True 

ALLOWED_HOSTS = configs['allowed_hosts']['production']

PRODUCTION_VAR_ROOT = "/var/wilhelm-production/"

#=============================================================================
# domain/subdomain stuff
#=============================================================================
DOMAIN_NAME = configs['domain_names']['production']['name']
DATA_SUBDOMAIN_NAME = 'data' + '.' + DOMAIN_NAME
MAIN_SUBDOMAIN_NAME = 'www' + '.' + DOMAIN_NAME
WWWURL = 'https://www.%s' % DOMAIN_NAME
DATA_SUBDOMAIN_PROTOCOL = 'https'
DATA_PERMALINK_ROOT = DATA_SUBDOMAIN_PROTOCOL + '://' + DATA_SUBDOMAIN_NAME + '/' 
SESSION_COOKIE_DOMAIN\
    = configs['domain_names']['production']['session_cookie_domain']


#=============================================================================
# Static files settings.
#=============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = PRODUCTION_VAR_ROOT + 'static'

STATICFILES_DIRS = (
    os.path.join(WILHELM_ROOT, "static"),
)

#=============================================================================
# EXPERIMENT_ARCHIVES_CACHE
#=============================================================================
EXPERIMENT_ARCHIVES_CACHE = PRODUCTION_VAR_ROOT + 'data-archives'
mk_archive_cache_dir(EXPERIMENT_ARCHIVES_CACHE, 0775)

#=============================================================================
# DATA_ARCHIVES_CACHE & MEDIA 
#=============================================================================
DATA_ARCHIVES_CACHE = PRODUCTION_VAR_ROOT + 'cache/data'
mk_archive_cache_dir(DATA_ARCHIVES_CACHE, 0775)
MEDIA_ROOT = DATA_ARCHIVES_CACHE
MEDIA_URL = '/data-archives/'


#=============================================================================
# Database settings.
#=============================================================================
DATABASES = {
'default': {
    'ENGINE': 'django.db.backends.sqlite3', 
    'NAME': os.path.join(WILHELM_ROOT,'wilhelm.db'),                      
}
}

#=============================================================================
# Add django_extensions to INSTALLED_APPS
#=============================================================================
INSTALLED_APPS += ('django_extensions',)


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
LOGFILE_DIRECTORY = PRODUCTION_VAR_ROOT + 'logs/'
LOGFILE_FILENAME = DOMAIN_NAME + '.log'
mk_archive_cache_dir(LOGFILE_DIRECTORY, 0775)
LOGGING['handlers']['file']['filename']\
    = os.path.join(LOGFILE_DIRECTORY, LOGFILE_FILENAME)


# Passwordless passwords
AUTHENTICATION_BACKENDS\
    = ("apps.presenter.utils.PasswordlessAuthBackend",) + AUTHENTICATION_BACKENDS

ALLOW_PASSWORDLESS_LOGIN = True
PASSWORDLESS_AUTH_PASSWORD_HASH\
    = secrets['passwordless-admin']['production']['hash']
