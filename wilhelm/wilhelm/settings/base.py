from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
from celery.schedules import crontab
from unipath import Path
import configobj
import errno
import os
import sh
import sys

#================================ End Imports ================================

def mk_archive_cache_dir(cache, mode=None):

    if not (os.path.exists(cache) and os.path.isdir(cache)):

        try:
            os.makedirs(cache)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(cache):
                pass
            else: raise

        if mode is not None:
            os.chmod(cache, mode)

#=============================================================================


SETTINGS_DIR = os.path.abspath(os.path.dirname(__file__))
WILHELM_ROOT = Path(SETTINGS_DIR).ancestor(2)

# We will assume you have a secrets.cfg and configs.cfg file in settings.
secrets_filename =  os.path.join(SETTINGS_DIR, 'secrets.cfg')
configs_filename =  os.path.join(SETTINGS_DIR, 'configs.cfg')

try:
    with open(secrets_filename, 'r') as secrets_cfg_file:
        secrets = configobj.ConfigObj(secrets_cfg_file)


    with open(configs_filename, 'r') as configs_cfg_file:
        configs = configobj.ConfigObj(configs_cfg_file)

except IOError:

    sys.stdout.write("""
No secrets.cfg or configs.cfg in your settings dir? You need them.

We're expecting a secrets.cfg like this

    secret_key = XXX
    broker_url = XXX

    [social_auth]
        [[facebook]]
            key = XXX
            secret = XXX
            scope = XXX
        [[google]]
            key = XXX
            secret = XXX
        [[twitter]]
            key = XXX
            secret = XXX


And a configs.cfg like this


    webmaster_email = "foo@foobar.org"
    project_name = "My project name"


""")
    raise



#=============================================================================
# Django project parameters.
#=============================================================================

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS
TIME_ZONE = 'Europe/London'
LANGUAGE_CODE = 'en-gb'
SITE_ID = 1
USE_I18N = True


#=============================================================================
# Wilhelm specific parameters.
#=============================================================================

WEBMASTEREMAIL = configs['webmaster_email']
WILHELMPROJECTNAME = configs['project_name']
UID_LENGTH = 40 
UID_SHORT_LENGTH = 7
NAME_LENGTH = 255 
LOGIN_URL = '/login'
UNLIMITED_EXPERIMENT_ATTEMPTS = False


#=============================================================================
# Media files settings. 
#=============================================================================

#MEDIA_ROOT
#MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = secrets['secret_key']

#=============================================================================
# Middleware settings. 
#=============================================================================

MIDDLEWARE_CLASSES = (
    'django_hosts.middleware.HostsRequestMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.presenter.middleware.ProfileMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
)

#=============================================================================
# Urls settings.
#=============================================================================
ROOT_URLCONF = 'wilhelm.urls'

#=============================================================================
# Django hosts information
#=============================================================================
ROOT_HOSTCONF = 'wilhelm.hosts'
DEFAULT_HOST = 'www'

#=============================================================================
# Installed apps settings.
#=============================================================================

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.humanize',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django_nose',
    'django_hosts',
    'django_user_agents',
    'social.apps.django_app.default',
    'apps.administration',
    'apps.archives',
    'apps.core',
    'apps.dataexport',
    'apps.research',
    'apps.experimenters',
    'apps.front',
    'apps.presenter',
    'apps.sessions',
    'apps.subjects',
    'apps.testing',
    'contrib.bartlett',
    'contrib.base',
    'contrib.stimuli.textual',
)

#=============================================================================
# Template settings.
#=============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
            os.path.join(WILHELM_ROOT,'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': False,
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "social.apps.django_app.context_processors.backends",
                "social.apps.django_app.context_processors.login_redirect",
                'wilhelm.context_processors.domain_name',
                'wilhelm.context_processors.data_subdomain',
                'wilhelm.context_processors.main_subdomain'
            ],
        },
    },
]
#
#TEMPLATE_DIRS = (
#os.path.join(WILHELM_ROOT,'templates'),
#)

## List of callables that know how to import templates from various sources.
#TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.load_template_source',
#    'django.template.loaders.app_directories.load_template_source',
##     'django.template.loaders.eggs.load_template_source',
#)
#TEMPLATE_CONTEXT_PROCESSORS = (
#    "django.contrib.auth.context_processors.auth",
#    "django.core.context_processors.debug",
#    "django.core.context_processors.i18n",
#    "django.core.context_processors.media",
#    "django.core.context_processors.static",
#    "django.core.context_processors.tz",
#    "django.contrib.messages.context_processors.messages",
#    "social.apps.django_app.context_processors.backends",
#    "social.apps.django_app.context_processors.login_redirect",
#    'wilhelm.context_processors.domain_name',
#    'wilhelm.context_processors.data_subdomain',
#    'wilhelm.context_processors.main_subdomain'
#)


#=============================================================================
# Authentication settings.
#=============================================================================
ALLOW_PASSWORDLESS_LOGIN = False
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "apps.presenter.utils.TempSubjectBackend",
    "social.backends.facebook.FacebookOAuth2",
    "social.backends.google.GoogleOAuth2",
    "social.backends.twitter.TwitterOAuth",
)

#=============================================================================
# Testing settings.
#=============================================================================
USE_NOSE_TEST_RUNNER = False

if USE_NOSE_TEST_RUNNER:

    # Use nose to run all tests
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

    NOSE_ARGS = [
        '--with-coverage',
        '--cover-package=contrib,apps',
    ]

else:

    TEST_RUNNER = 'django.test.runner.DiscoverRunner'

#=============================================================================
# Logging settings.
#=============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('\t'.join(['%(asctime)s.%(msecs)d',
                                  '%(process)d', 
                                  '%(levelname)s',
                                  '%(pathname)s',
                                  '%(lineno)s',
                                  '%(funcName)s', 
                                  '%(message)s'])),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'd',
            'interval':1,
            'backupCount': 1000,
            'filename': '/tmp/wilhelm.log', # Override this.
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'wilhelm': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

#=============================================================================
# Celery task manager settings.
#=============================================================================


BROKER_URL = secrets['broker_url']

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = "amqp"

CELERY_IMPORTS = ('apps.presenter.tasks', 
                  'apps.dataexport.tasks')

CELERYBEAT_SCHEDULE = {
    'stale_live_sessions': {
        'task': 'apps.presenter.tasks.flag_stale_live_sessions',
        'schedule': crontab(minute='*'), 
    },
    'purge_flagged_live_sessions': {
        'task': 'apps.presenter.tasks.purge_flagged_live_sessions',
        'schedule': crontab(minute='*'), 
    },
    'automated_data_export': {
        'task': 'apps.dataexport.tasks.automated_data_export',
        'schedule': crontab(minute='0', hour='*'), 
    }
}

#=============================================================================
# Social media login 
#=============================================================================
LOGIN_REDIRECT_URL = '/initialize'

fb_secrets = secrets['social_auth']['facebook']
google_secrets = secrets['social_auth']['google']
twitter_secrets = secrets['social_auth']['twitter']

# Facebook 
SOCIAL_AUTH_FACEBOOK_KEY = fb_secrets['key']
SOCIAL_AUTH_FACEBOOK_SECRET = fb_secrets['secret']
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email'] 
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id,name,email', # needed starting from protocol v2.4
}

# Google 
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = google_secrets['key']
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = google_secrets['secret']

# Twitter stuff
SOCIAL_AUTH_TWITTER_KEY = twitter_secrets['key']
SOCIAL_AUTH_TWITTER_SECRET = twitter_secrets['secret']


SOCIAL_AUTH_PIPELINE = (
    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. On some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    'social.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    'social.pipeline.social_auth.social_uid',

    # Verifies that the current auth process is valid within the current
    # project, this is were emails and domains whitelists are applied (if
    # defined).
    'social.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated in the site.
    'social.pipeline.social_auth.social_user',

    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    'social.pipeline.user.get_username',

    # Send a validation email to the user to verify its email address.
    # Disabled by default.
    # 'social.pipeline.mail.mail_validation',

    # Associates the current social details with another user account with
    # a similar email address. Disabled by default.
    # 'social.pipeline.social_auth.associate_by_email',

    # Create a user account if we haven't found one yet.
    'social.pipeline.user.create_user',

    # Create the record that associated the social account with this user.
    'social.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social.pipeline.social_auth.load_extra_data',

    # Update the user record with any changed info from the auth service.
    'social.pipeline.user.user_details',

    # Create the user's subject account.
    'apps.subjects.utils.social_media_user_subject_create',
)

#=============================================================================
# Demo accounts and passwords
#=============================================================================
DEMO_USERNAME = configs['demo_username']
DEMO_PASSWORD = configs['demo_password']

#=============================================================================
# Get current commit. Use this as wilhelm version.
#=============================================================================
WILHELM_VERSION = 'Unknown'

try:

    WILHELM_VERSION\
        = open(os.path.join(SETTINGS_DIR, 'version.txt')).read()

except IOError:

    try:

        git_cmd = sh.git.bake('--no-pager')
        WILHELM_VERSION\
            = git_cmd(['log', '--pretty=format:%H']).stdout.strip().split('\n')[0]

        with open(os.path.join(SETTINGS_DIR, 'version.txt'), 'w') as f:
            f.write(WILHELM_VERSION)

    except:

        WILHELM_VERSION = 'Unknown'

#=============================================================================
# Django user agent cache
#=============================================================================
#CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#        'LOCATION': '127.0.0.1:11211',
#    }
#}
#USER_AGENTS_CACHE = 'default'

# Geoip
GEOIP_PATH = os.path.join(WILHELM_ROOT, 
                          'apps/dataexport/geolite_databases')

IS_PRODUCTION_SERVER = False # Override for production
