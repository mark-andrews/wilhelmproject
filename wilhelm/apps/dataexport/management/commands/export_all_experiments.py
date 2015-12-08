from __future__ import absolute_import

#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.dataexport.models import ExperimentDataExport

#================================ End Imports ================================

class Command(BaseCommand):

    help = """export all experiment data"""

    def handle(self, *args, **options):

        try:
            ExperimentDataExport.objects.release()
        except Exception as e:
            self.stdout.write('%s: %s' % (e.__class__.__name__, e.message))
