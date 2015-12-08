from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import json
import logging

#=============================================================================
# Django imports
#=============================================================================
from django.db import models

#=============================================================================
# Wilhelm imports
#=============================================================================
from .widgets import (Widget, 
                      SessionWidget)

from apps.core import fields
from apps.dataexport.utils import safe_export_data
from apps.core.utils.datetime import approximate_minutes_from_seconds

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

class Tetris(Widget):

    '''
    This is a tetris game widget. The game lasts for a fixed duration
    (`duration` in seconds) and the pieces move at speed `speed` (in
    milliseconds).

    '''

    duration = fields.DurationField(default=120)
    speed = models.FloatField(default=300)

    @classmethod
    def new(cls, duration, speed):

        return cls._new(duration = duration,
                        speed = speed)

    @property
    def widget_data(self):

        return dict(duration = self.duration,
                    speed = self.speed)

    def get_widget_template_data(self):
        return dict(approx_game_time\
                    = approximate_minutes_from_seconds(self.duration))

class SessionTetris(SessionWidget):

    '''
    A session model for Tetris. We just need their score.

    '''

    score = models.PositiveIntegerField(default=0)

    def get(self):
        logger.debug('Getting Tetris data.')
        self.set_started()
        return self.widget.get_widget_data()

    def post(self, data):
        logger.debug('Posting Tetris data: %s.' % data['responses'])

        posted_data = json.loads(data['responses'])[0]
        score = posted_data['score']

        logger.debug(score)

        self.score = score

        self.save()

        self.set_completed()

        return posted_data 

    def data_export(self, to_json=True):

        export_dict = super(SessionTetris, self).data_export()

        for key, f in [('score', lambda : self.score),]:

            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict

    def feedback(self):

        """
        What's your tetris score.
        """

        summary = {}
        summary['Game_type'] = 'Tetris'
        summary['score'] = self.score

        return summary
