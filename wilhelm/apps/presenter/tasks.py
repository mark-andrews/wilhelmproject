'''
A task to be run by a celery cron job that is set up in settings.py.
'''

from __future__ import absolute_import

#=============================================================================
# Django imports.
#=============================================================================
from celery import shared_task

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.presenter.utils import live_sessions_utils
#================================ End Imports ================================

@shared_task
def purge_flagged_live_sessions(*args, **kwargs):
    live_sessions_utils.purge_flagged_live_sessions()

@shared_task
def flag_stale_live_sessions(*args, **kwargs):
    live_sessions_utils.flag_stale_live_sessions()
