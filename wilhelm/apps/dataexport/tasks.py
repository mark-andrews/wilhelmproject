'''
Automated data export task to be run by a celery cron job.
'''

from __future__ import absolute_import

#=============================================================================
# Django imports.
#=============================================================================
from celery import shared_task

#=============================================================================
# Wilhelm imports.
#=============================================================================
from .models import ExperimentDataExport

#================================ End Imports ================================

@shared_task
def automated_data_export(*args, **kwargs):
    ExperimentDataExport.objects.release(new_data_only=True)
