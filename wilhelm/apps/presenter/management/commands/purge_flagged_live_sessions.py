from __future__ import absolute_import

#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.presenter.utils.live_sessions_utils import purge_flagged_live_sessions

#================================ End Imports ================================

class Command(BaseCommand):
    def handle(self, *args, **options):
        purge_flagged_live_sessions()
