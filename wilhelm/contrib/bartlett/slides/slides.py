from __future__ import absolute_import

#=============================================================================
# Wilhelm imports.
#=============================================================================
from contrib.base import models as basemodels
from apps.core import fields

#================================ End Imports ================================

class Slide(basemodels.Slide):

    '''
    The prototype of all slides in this module.
    '''

    class Meta:
        abstract = True
        app_label = 'bartlett'

    name = fields.nameField()

class SessionSlide(basemodels.SessionSlide):

    class Meta:
        abstract = True
        app_label = 'bartlett'
