from __future__ import absolute_import

#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.presenter.utils.live_sessions_utils import flag_stale_live_sessions

#================================ End Imports ================================

class Command(BaseCommand):
    # TODO (Tue 30 Dec 2014 04:45:59 GMT): It would be nice to pass a
    # live_session_keep_alive_duration argument to this command.
    def handle(self, *args, **options):
        flag_stale_live_sessions()
