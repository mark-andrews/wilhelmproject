'''
The experiment scripts for

* Experiment `Brisbane`: An experiment on memory for texts
* Experiment `Malmo`: An experiment on memory for word lists

'''

from __future__ import absolute_import

# ============================================================================
# Standard library imports.
# ============================================================================
import os

# ============================================================================
# Third party imports.
# ============================================================================
import configobj

# ============================================================================
# Wilhelm imports
# ============================================================================
from apps.core.utils import sys, strings
from contrib.bartlett.models import (Playlist,
                                     TextRecognitionMemoryTest,
                                     TextRecallMemoryTest,
                                     WordlistRecognitionMemoryTest,
                                     WordlistRecallMemoryTest)


# =============================== End Imports ================================

def stimuluspath(filename):

    '''
    Return the full path of the stimulus file `filename`.

    '''

    this_dir = sys.thisDir(__file__)
    stimuli_dir = os.path.join(this_dir, 'stimuli')

    return os.path.abspath(os.path.join(stimuli_dir, filename))


class PlaylistFactory(object):

    @classmethod
    def new(cls):

        brismo = cls(configuration_file='Brismo.cfg')

        return Playlist.new(brismo.slides, 
                            brismo.max_number_of_parts, 
                            brismo.instructions)


class Brismo(PlaylistFactory):

    def __init__(self, configuration_file):

        self.configuration_file = configuration_file

        configfile = stimuluspath(self.configuration_file)
        sys.assert_file_exists(configfile)
        self.config = configobj.ConfigObj(configfile)

        self.parameters = self.config['parameters'].dict()
        self.text_memoranda = self.config['text_memoranda']
        self.wordlist_memoranda = self.config['wordlist_memoranda']
        self.start_msg = self.config['start_msg'].dict()

        self.recognition_test_parameters = self.parameters['recognition']

        self.wordlist_recognition_test_times = dict(
            isi=float(self.recognition_test_parameters['isi']),
            fadeInDuration=float(self.recognition_test_parameters['fadeInDuration']),
            fadeOutDuration=float(self.recognition_test_parameters['fadeOutDuration']),
            timeOutDuration=float(self.recognition_test_parameters['timeOutDuration'])
            )

        self.word_recall_parameters = self.parameters['recall']

        self.game_parameters = dict(
            game_duration = int(self.parameters['tetris']['game_duration']),
            game_speed = int(self.parameters['tetris']['game_speed'])
        )

        _slide_types\
            = ['TextRecallMemoryTest',
               'TextRecognitionMemoryTest',
               'WordlistRecallMemoryTest',
               'WordlistRecognitionMemoryTest']

        _make_slide_functions\
            = [self._make_text_recall_memory_test,
               self._make_text_recognition_memory_test,
               self._make_wordlist_recall_memory_test,
               self._make_wordlist_recognition_memory_test]

        self.max_number_of_parts\
            = int(self.parameters['maximum_number_of_parts'])

        self._make_slide_function_map\
            = dict(zip(_slide_types, _make_slide_functions))

    def _make_text_recognition_memory_test(self, name, memorandum):

        slide = TextRecognitionMemoryTest.new(
                    name=name,
                    title=memorandum['text_title'],
                    text=strings.fill(memorandum['text']),
                    inwords=memorandum['inwords'].split(','),
                    outwords=memorandum['outwords'].split(','),
                    start_text_msg=self.start_msg['start_text_msg'],
                    start_memorytest_msg=self.start_msg['start_memorytest_msg'],
                    test_times=self.wordlist_recognition_test_times,
                    reading_times=self.text_reading_times,
                    **self.game_parameters
                )

        return slide

    def _make_wordlist_recognition_memory_test(self, name, memorandum):

        slide = WordlistRecognitionMemoryTest.new(
                        name=name,
                        inwords=memorandum['inwords'].split(','),
                        outwords=memorandum['outwords'].split(','),
                        wordlist=memorandum['wordlist'].split(','),
                        start_wordlist_msg=self.start_msg['start_wordlist_msg'],
                        start_memorytest_msg=self.start_msg['start_memorytest_msg'],
                        test_times=self.wordlist_recognition_test_times,
                        wordlist_display_times=self.wordlist_display_times,
                        **self.game_parameters
                    )

        return slide

    def _make_text_recall_memory_test(self, name, memorandum):

        slide = TextRecallMemoryTest.new(
                    name=name,
                    option_length=self.parameters['recall']['option_length'],
                    title=memorandum['text_title'],
                    start_text_msg=self.start_msg['start_text_msg'],
                    text=strings.fill(memorandum['text']),
                    start_memorytest_msg=self.start_msg['start_memorytest_msg'],
                    reading_times=self.text_reading_times,
                    **self.game_parameters
                )

        return slide

    def _make_wordlist_recall_memory_test(self, name, memorandum):

        slide = WordlistRecallMemoryTest.new(
                    name=name,
                    option_length=self.word_recall_parameters['option_length'],
                    wordlist=memorandum['wordlist'].split(','),
                    start_wordlist_msg=self.start_msg['start_wordlist_msg'],
                    start_memorytest_msg=self.start_msg['start_memorytest_msg'],
                    wordlist_display_times=self.wordlist_display_times,
                    **self.game_parameters
                )

        return slide

    def make_slide(self, slide_type, memorandum_name, memorandum):

        return self._make_slide_function_map[slide_type](memorandum_name,
                                                         memorandum)

    def parse_instructions(self):

        '''
        Given a ConfigObj dict of instructions, return a list of rst strings.
        As my instructions have variables in them, I need to give these variables
        values using .format().
        '''

        self.instructions[2]\
            = self.instructions[2].format(maximum_number_of_parts
                                     = self.parameters['maximum_number_of_parts'],
                                     expected_duration_of_part
                                     = self.parameters['expected_duration_of_part'])


class Brisbane(Brismo):

    def __init__(self, configuration_file):

        super(Brisbane, self).__init__(configuration_file)

        self.text_parameters = self.parameters['text']

        self.text_reading_times = dict(
            minimum_reading_time=float(self.text_parameters['minimum_reading_time']),
            maximum_reading_time=float(self.text_parameters['maximum_reading_time'])
            )

        self.instructions\
            = [ins.strip() for ins in
               self.config['text-memory-instructions'].values()]


        self.get_slides()
        self.parse_instructions()

    def get_slides(self):

        self.slides = []
        for key, memorandum in self.text_memoranda.items():

            _text, _text_number = key.split('_')

            memorandum['text_title']\
                = _text.title() + ' ' + str(int(_text_number)+1)

            recall_slide = self.make_slide('TextRecallMemoryTest',
                                     key + '_recallmemory',
                                     memorandum)

            recognition_slide = self.make_slide('TextRecognitionMemoryTest',
                                     key + '_recognitionmemory',
                                     memorandum)

            self.slides.extend([recall_slide, recognition_slide])


class Malmo(Brismo):

    def __init__(self, configuration_file):

        super(Malmo, self).__init__(configuration_file)

        self.wordlist_parameters = self.parameters['wordlist']

        self.wordlist_display_times = dict(
            isi=float(self.wordlist_parameters['isi']),
            fadeInDuration=float(self.wordlist_parameters['fadeInDuration']),
            fadeOutDuration=float(self.wordlist_parameters['fadeOutDuration']),
            stimulusDuration=float(self.wordlist_parameters['StimulusDuration'])
            )

        self.instructions\
            = [ins.strip() for ins in
               self.config['wordlist-memory-instructions'].values()]

        self.get_slides()
        self.parse_instructions()

    def get_slides(self):

        self.slides = []
        for key, memorandum in self.wordlist_memoranda.items():

            recall_slide = self.make_slide('WordlistRecallMemoryTest',
                                     key + '_recallmemory',
                                     memorandum)

            recognition_slide = self.make_slide('WordlistRecognitionMemoryTest',
                                     key + '_recognitionmemory',
                                     memorandum)


            self.slides.extend([recall_slide, recognition_slide])

    def parse_instructions(self):

        super(Malmo, self).parse_instructions()

        self.instructions[0]\
            = self.instructions[0].format(avg_words_per_list
                                     = self.parameters['avg_words_per_list'])
