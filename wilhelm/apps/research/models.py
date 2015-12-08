'''
Models for the experimental archives.
'''

from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import logging

#=============================================================================
# Django imports.
#=============================================================================
from django.db import models

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.archives.models import Experiment as ArchiveExperiment

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

class Project(models.Model):

    experiment = models.ForeignKey(ArchiveExperiment, null=True)
    blurb = models.TextField(null=True)
