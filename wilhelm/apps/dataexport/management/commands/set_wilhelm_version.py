from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import os
import sh
import sys
import logging

#=============================================================================
# Django imports
#=============================================================================
from django.conf import settings
from django.core.management.base import BaseCommand


#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

version_filename = os.path.join(settings.SETTINGS_DIR, 'version.txt')

class Command(BaseCommand):


    def handle(self, *args, **options):

        try:
            git_cmd = sh.git.bake('--no-pager')
            WILHELM_VERSION\
                = git_cmd(['log', '--pretty=format:%H']).stdout.strip().split('\n')[0]

            with open(version_filename, 'w') as f:
                f.write(WILHELM_VERSION)

        except:
            sys.stdout('Could not write wilhelm version to file.')
