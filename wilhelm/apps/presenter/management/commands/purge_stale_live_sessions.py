from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import logging


#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.presenter.models import LiveExperimentSession

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

class Command(BaseCommand):


    def handle(self, *args, **options):

        for live_session in LiveExperimentSession.objects.all():

            if not live_session.keep_alive:

                live_session_uid = live_session.uid
                live_session.delete()

                logger.info(
                    'Purging live_session %s.' % live_session_uid
                )


