from __future__ import absolute_import

#=============================================================================
# Django imports.
#=============================================================================
from django.core.management.base import BaseCommand

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.subjects.utils import list_all_nontemp_subjects

#================================ End Imports ================================

class Command(BaseCommand):

    def handle(self, *args, **options):

        S = list_all_nontemp_subjects()
        
        if S:
            self.stdout.write('\n\n'.join(S))
