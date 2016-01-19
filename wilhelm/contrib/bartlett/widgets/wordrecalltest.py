from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import json
import logging

#=============================================================================
# Third party
#=============================================================================
from jsonfield import JSONField


#=============================================================================
# Wilhelm imports
#=============================================================================
from .widgets import (Widget, 
                      SessionWidget)

from apps.core import fields
from contrib.bartlett.conf import data_export as bartlett_data_export
from apps.dataexport.utils import safe_export_data

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

class WordRecallTest(Widget):

    '''
    This simple widget presents the subject a list of options where they can
    recall the words they rememember.

    '''

    option_length = fields.PositiveSmallIntegerField(default=5)

    @classmethod
    def new(cls, 
            start_msg,
            option_length):

        return cls._new(start_msg = start_msg,
                        option_length = option_length)

    @property
    def widget_data(self):

        return dict(start_msg = self.start_msg,
                    option_length = self.option_length)

class SessionWordRecallTest(SessionWidget):

    '''
    What is the list of the recalled words?
    '''

    recalledwords_json = JSONField(null=True)

    def get(self):
        self.set_started()
        return self.widget.get_widget_data()

    def post(self, data):

        recalledwords = json.loads(data['responses'])[0]

        self.recalledwords_json = json.dumps(recalledwords)

        self.save()

        self.set_completed()

        return recalledwords

    @property
    def recalledwords(self):
        if self.recalledwords_json:
            return json.loads(self.recalledwords_json)
        else:
            return ''

    def data_export(self, to_json=True):

        export_dict = super(SessionWordRecallTest, self).data_export()

        for key, f in [
                (bartlett_data_export.word_recall_option_length, 
                 lambda: self.widget.option_length),
                (bartlett_data_export.word_recall_test_data,
                 lambda: self.recalledwords)]:


            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict

    def feedback(self):

        """
        What words are recalled and how many.
        """

        summary = {}
        summary['Test_type'] = 'Recall'
        summary['recalled_words'] = self.recalledwords

        return summary
