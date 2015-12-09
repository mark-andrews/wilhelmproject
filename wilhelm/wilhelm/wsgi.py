"""
WSGI config for foobarjd project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.conf import settings

if settings.IS_PRODUCTION_SERVER:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "wilhelm.settings.production")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "wilhelm.settings.production")

application = get_wsgi_application()
