from __future__ import absolute_import

#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.presenter.utils import live_sessions_utils

#================================ End Imports ================================

class Command(BaseCommand):


    def handle(self, *args, **options):

        live_sessions_utils.purge_flagged_live_sessions()
