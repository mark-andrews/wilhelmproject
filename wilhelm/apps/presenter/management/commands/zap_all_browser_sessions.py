from __future__ import absolute_import

#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

#================================ End Imports ================================

class Command(BaseCommand):


    def handle(self, *args, **options):

        for browser_session in Session.objects.all():
            SessionStore(session_key=browser_session.session_key).delete()
