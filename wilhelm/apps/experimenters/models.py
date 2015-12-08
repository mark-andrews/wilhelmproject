'''
Models for experimenters.
'''

from __future__ import absolute_import
#=============================================================================
# Django imports
#=============================================================================
from django.db import models
from django.db.models import Model
from django.contrib.auth.models import User

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.archives.models import ExperimentRepository

#================================ End Imports ================================

class Experimenter(Model):

    '''
    An experimenter.
    '''

    user = models.ForeignKey(User, null=True)
    repository = models.ManyToManyField(ExperimentRepository)
