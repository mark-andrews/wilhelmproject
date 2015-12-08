from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import os

#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

#================================ End Imports ================================

class Command(BaseCommand):

    help = ''' Remove sqlite3 database and re-create it again.'''

    def handle(self, *args, **options):

        db = settings.DATABASES['default']

        if db['ENGINE'] == 'django.db.backends.sqlite3':

            if os.path.exists(db['NAME']):
                os.remove(db['NAME'])

        management.call_command('syncdb', interactive = False)
