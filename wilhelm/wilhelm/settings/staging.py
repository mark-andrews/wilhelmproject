from __future__ import absolute_import

from .base import *

DEBUG = False
TEMPLATE_DEBUG = True

DEVELOPMENT_SERVER = False

ALLOWED_HOSTS = configs['allowed_hosts']['staging']

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
STATIC_ROOT = '/tmp/var/static'

STATICFILES_DIRS = (
    os.path.join(WILHELM_ROOT, "static"),
)

#=============================================================================
# EXPERIMENT_ARCHIVES_CACHE
#=============================================================================
EXPERIMENT_ARCHIVES_CACHE = '/tmp/var/wilhelm/data-archives'
mk_archive_cache_dir(EXPERIMENT_ARCHIVES_CACHE, 0775)

#=============================================================================
# DATA_ARCHIVES_CACHE & MEDIA 
#=============================================================================
DATA_ARCHIVES_CACHE = '/tmp/var/wilhelm/cache/data'
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


# Facebook 
fb_secrets = secrets['social_auth']['facebook-for-staging']

SOCIAL_AUTH_FACEBOOK_KEY = fb_secrets['key']
SOCIAL_AUTH_FACEBOOK_SECRET = fb_secrets['secret']

