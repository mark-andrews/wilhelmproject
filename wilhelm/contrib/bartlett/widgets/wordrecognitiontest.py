from __future__ import absolute_import, division

#=============================================================================
# Standard library imports
#=============================================================================
import json
import logging
from collections import OrderedDict, defaultdict

#=============================================================================
# Django imports.
#=============================================================================
from django.contrib.contenttypes.models import ContentType
from django.db import models
 
#=============================================================================
# Wilhelm imports
#=============================================================================
from .widgets import (Widget, 
                      WordlistMixin,
                      SessionWidget,
                      SessionWordlistMixin)

from .choicemodel import BinaryChoiceModel
from contrib.bartlett.conf import data_export as bartlett_data_export
from contrib.stimuli.textual.models import (WordlistStimulus, 
                                            WordlistTestStimulus)
from apps.core.utils import datetime
from apps.dataexport.utils import safe_export_data

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

class WordRecognitionTest(Widget, WordlistMixin):

    '''
    A widget to display words in a wordlist as a word recognition test.

    - wordliststimulus: A link to a WordlistTestStimulus
    - isi: The interval between the presentation of each word.
    - fadeInDuration: How long it takes for the word to fade in.
    - fadeOutDuration: How long it takes for the word to fade out.
    - timeOutDuration: How long the subject has to make a response.

    '''

    wordliststimulus = models.ForeignKey(WordlistTestStimulus, null=True)
    isi = models.FloatField(default=0.2)
    fadeInDuration = models.FloatField(default=0.2)
    fadeOutDuration = models.FloatField(default=0.2)
    timeOutDuration = models.FloatField(default=3)

    @classmethod
    def new(cls, 
            inwords, 
            outwords,
            start_msg,
            isi, 
            fadeInDuration, 
            fadeOutDuration,
            timeOutDuration):


        wordlist = inwords + outwords
        expected_responses = ([True] * len(inwords)) + ([False] * len(outwords))

        wordliststimulus\
            = WordlistTestStimulus.new(wordlist = wordlist,
                                       expected_responses = expected_responses)

        return cls._new(wordliststimulus = wordliststimulus, 
                        start_msg = start_msg,
                        isi = isi, 
                        fadeInDuration = fadeInDuration, 
                        fadeOutDuration = fadeOutDuration,
                        timeOutDuration = timeOutDuration)

    @property
    def wordlist_length(self):
        return self.wordliststimulus.length

    @property
    def wordlist_with_expected_responses(self):
        return self.wordliststimulus.wordlist_with_expected_responses

    @property
    def widget_data(self):

        '''
        Return a dictionary of the data needed for the client side.

        '''

        return dict(wordlist = self.wordlist, 
                    start_msg = self.start_msg,
                    isi = self.isi,
                    fadeInDuration = self.fadeInDuration, 
                    fadeOutDuration = self.fadeOutDuration, 
                    timeOutDuration = self.timeOutDuration)

    def get_widget_template_data(self):

        timeout_duration_str\
            = str(int(self.timeOutDuration)) + ' seconds'

        return dict(wordlist_length = self.wordlist_length,
                    stimulus_timeout_duration = timeout_duration_str)


class SessionWordRecognitionTest(SessionWordlistMixin, SessionWidget):

    def get(self):

        self.set_started()

        return super(SessionWordRecognitionTest, self).get()

    def post(self, data):

        '''
        Process the deserialized data and load it into the session object.
        '''
        logger.debug('Processing SessionWordRecongitionTest POST data') 

        print("Hello. Am I completed %s" % self.completed)

        try:
            responses = json.loads(data['responses'])

            logger.debug('Processing data: %s' % repr(responses))


            for datum in responses:

                stimulus_onset_datetime\
                    = datetime.fromtimestamp(datum['onset'])

                if datum['responseTime'] is None:
                    response_datetime = None
                    logger.debug('No responseTime. Missed trial?')
                else:
                    response_datetime\
                        = datetime.fromtimestamp(datum['responseTime'])

                stimulus\
                    = self.widget.wordliststimulus.get_item(datum['word'])

                try:

                    if datum['response'] == 'present':
                        response = True
                    elif datum['response'] == 'absent':
                        response = False
                    else:
                        response = None

                    try:
                        assert datum['response'] in ('absent', 'present', None)
                    except AssertionError as e:
                        logger.error(
                            'Response should be "absent" or "present" or None')


                    BinaryChoiceModel.new(self,
                                          stimulus,
                                          response = response,
                                          order = datum['order'],
                                          stimulus_onset_datetime = stimulus_onset_datetime,
                                          response_datetime = response_datetime)
                except Exception as e:
                    logger.warning(
                        'Could not process binary response datum: %s' % e.message)

            self.set_completed()

        except Exception as e:
            logger.warning('Could not process data. %s ' % e.message)

    def get_response_data(self):

        """
        Return all binary choice items from the BinaryChoiceModel corresponding
        to this session widget.

        Order items by presentation order.

        """

        sessionwidget_ct = ContentType.objects.get_for_model(self)
        sessionwidget_uid = self.uid

        return BinaryChoiceModel\
            .objects.filter(sessionwidget_ct = sessionwidget_ct,
                            sessionwidget_uid = sessionwidget_uid)\
            .order_by('order')

    @property
    def response_data_denormalized(self):

        """
        Return a list of the items and responses in the word recognition test.
        This will be a list of tuples. Each tuple will be 
        (word, expected_response, latency, response, accuracy, hit).

        """

        denormalized_data = []

        for binary_choice_item in self.get_response_data():

            hit = binary_choice_item.response != None

            if hit:
                accuracy = (binary_choice_item.response == 
                            binary_choice_item.stimulus.expected_response)
            else:
                accuracy = None

            denormalized_data.append(
                OrderedDict(
                    [('stimulus_word', binary_choice_item.stimulus.word),
                     ('presentation_datetime',
                      binary_choice_item.stimulus_onset_datetime),
                     ('expected_response',
                      binary_choice_item.stimulus.expected_response),
                     ('response',  binary_choice_item.response),
                     ('response_datetime', binary_choice_item.response_datetime),
                     ('response_latency', binary_choice_item.response_latency),
                     ('response_accuracy', accuracy),
                     ('hit', hit),
                     ('order', binary_choice_item.order)]
                )
            )

        return denormalized_data

    def data_export(self):

        """
        Export SessionWordRecognitionTest data.

        """

        export_dict = super(SessionWordRecognitionTest, self).data_export()

        key = bartlett_data_export.word_recognition_test_data
        f = lambda: self.response_data_denormalized

        export_dict, exception_raised, exception_msg\
            = safe_export_data(export_dict, key, f)

        if exception_raised:
            logger.warning(exception_msg)

        return export_dict

    def feedback(self):

        """

        Provide the items and the counts of the number of items in the
        following 2x2 table.

                            Condition Positive | Condition Negative
                            =======================================

        Response Positive  |  True Positive    |  False Positive
        Response Negative  |  False Negative   |  True Negative

        """

        summary = dict(hit_total = 0,
                       miss_total = 0,
                       xtimeout_duration = self.widget.timeOutDuration,
                       Test_type = 'Recognition')

        response_classification_table = defaultdict(list)

        for item_dict in self.response_data_denormalized:

            if item_dict['hit']:

                summary['hit_total'] += 1

                present = item_dict['expected_response'] # True or False
                response = item_dict['response']  # True or False

                assert present in (True, False)
                assert response in (True, False)

                response_classification_table[(response, present)].append(
                    item_dict['stimulus_word']
                )

            else:

                summary['miss_total'] += 1

        summary['total'] = summary['hit_total'] + summary['miss_total']

        assert (summary['hit_total'] + summary['miss_total']
                == summary['total']
                == len(self.response_data_denormalized))

        try:
            summary['hit_rate'] = summary['hit_total']/summary['total']
        except ZeroDivisionError:
            summary['hit_rate'] = None

        try:
            summary['miss_rate'] = summary['miss_total']/summary['total']
        except ZeroDivisionError:
            summary['miss_rate'] = None

        for new_key, old_key in [('false_positive', (True, False)),
                                 ('true_positive', (True, True)),
                                 ('false_negative', (False, True)),
                                 ('true_negative', (False, False))]:

            summary[new_key] = response_classification_table[old_key]

        for key in ['false_positive', 
                    'true_positive', 
                    'false_negative',
                    'true_negative']:

            count_key = key + '_count'
            summary[count_key] = len(summary[key])

        # Diagonals
        summary['total_true']\
            = summary['true_positive_count'] + summary['true_negative_count']

        summary['total_false']\
            = summary['false_positive_count'] + summary['false_negative_count']

        # Row totals
        summary['response_positive_count']\
            = summary['true_positive_count'] + summary['false_positive_count']

        summary['response_negative_count']\
            = summary['true_negative_count'] + summary['false_negative_count']

        # Column totals
        summary['condition_positive_count']\
            = summary['true_positive_count'] + summary['false_negative_count']

        summary['condition_negative_count']\
            = summary['false_positive_count'] + summary['true_negative_count']

        try:
            summary['accuracy'] = summary['total_true'] / summary['total']
        except ZeroDivisionError:
            summary['accuracy'] = None

        try:
            summary['false_positive_rate']\
                = summary['false_positive_count'] / summary['response_positive_count']
        except ZeroDivisionError:
            summary['false_positive_rate'] = None

        try:
            summary['false_negative_rate']\
                = summary['false_negative_count'] / summary['response_negative_count']
        except ZeroDivisionError:
            summary['false_negative_rate'] = None


        return summary

    #=============================================================================
    # Deprecated properties
    #=============================================================================

    @property
    def latencies(self):

        return [response.response_latency 
                for response in self.get_response_data()]

    @property
    def responses(self):

        return [response.response for response in self.get_response_data()]

    @property
    def response_items(self):

        return [response.stimulus.word 
                for response in self.get_response_data()]


