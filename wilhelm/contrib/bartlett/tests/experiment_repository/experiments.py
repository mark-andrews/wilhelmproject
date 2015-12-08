'''
This is a wilhelm_experiments directory.
'''
from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import os

#=============================================================================
# Third party imports.
#=============================================================================
import configobj

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.core.utils import sys, strings
from contrib.bartlett.models import (Playlist, 
                                   TextRecognitionMemoryTest,
                                   WordlistRecognitionMemoryTest,
                                   WordlistRecallMemoryTest)


#================================ End Imports ================================

class PlaylistFactory(object):

    @classmethod
    def new(cls):

        return Playlist.new(cls.slides, cls.instructions)

def stimuluspath(filename):

    '''
    Return the full path of the stimulus file `filename`.

    '''

    this_dir = sys.thisDir(__file__)
    stimuli_dir = os.path.join(this_dir, 'stimuli')

    return os.path.abspath(os.path.join(stimuli_dir, filename))

def parse_instructions(instructions):

    '''
    Given a ConfigObj dict of instructions, return a list of rst strings.
    '''
    
    return [ins.strip() for ins in instructions.values()]

class Brisbane(PlaylistFactory):

    configfile = stimuluspath('Brisbane.cfg')
    sys.assert_file_exists(configfile)
    config = configobj.ConfigObj(configfile)

    parameters = config['parameters'].dict()
    memoranda = config['memoranda'].dict()
    start_msg = config['start_msg'].dict()

    recognition_test_parameters = parameters['recognition']
    text_parameters = parameters['text']
    wordlist_parameters = parameters['wordlist']

    wordlist_recognition_test_times = dict(
        isi = float(recognition_test_parameters['isi']),
        fadeInDuration = float(recognition_test_parameters['fadeInDuration']),
        fadeOutDuration = float(recognition_test_parameters['fadeOutDuration']),
        timeOutDuration = float(recognition_test_parameters['timeOutDuration'])
        )

    text_reading_times = dict(
        minimum_reading_time = float(text_parameters['minimum_reading_time']),
        maximum_reading_time = float(text_parameters['maximum_reading_time'])
        )

    wordlist_display_times = dict(
        isi = float(wordlist_parameters['isi']),
        fadeInDuration = float(wordlist_parameters['fadeInDuration']),
        fadeOutDuration = float(wordlist_parameters['fadeOutDuration']),
        stimulusDuration = float(wordlist_parameters['StimulusDuration'])
        )

    word_recall_parameters = parameters['recall']

    instructions = parse_instructions(config['instructions'])

    slides = []

    for key, description in config['slides'].items():

        memorandum_name = description['memorandum']

        try:
            memorandum = memoranda[memorandum_name]
        except KeyError:
            errmsg = 'We do not have a record of the memorandum: %s' \
                    % description['memorandum']
            raise KeyError, errmsg

        if description['type'] == 'TextRecognitionMemoryTest':

            slide = TextRecognitionMemoryTest.new(
                name = memorandum_name,
                title = memorandum['title'],
                text = strings.fill(memorandum['text']),
                inwords = memorandum['inwords'].split(),
                outwords = memorandum['outwords'].split(),
                start_text_msg = start_msg['start_text_msg'],
                start_memorytest_msg = start_msg['start_memorytest_msg'],
                test_times = wordlist_recognition_test_times,
                reading_times = text_reading_times
            )

        elif description['type'] == 'WordListRecognitionMemoryTest':
        
            slide = WordlistRecognitionMemoryTest.new(
                name = memorandum_name,
                inwords = memorandum['inwords'].split(),
                outwords = memorandum['outwords'].split(),
                wordlist = memorandum['wordlist'].split(),
                start_wordlist_msg = start_msg['start_wordlist_msg'],
                start_memorytest_msg = start_msg['start_memorytest_msg'],
                test_times = wordlist_recognition_test_times,
                wordlist_display_times = wordlist_display_times
            )

        elif description['type'] == 'WordListRecallMemoryTest':

            slide = WordlistRecallMemoryTest.new(
                name = memorandum_name,
                option_length = word_recall_parameters['option_length'],
                wordlist = memorandum['wordlist'].split(),
                start_wordlist_msg = start_msg['start_wordlist_msg'],
                start_memorytest_msg = start_msg['start_memorytest_msg'],
                wordlist_display_times = wordlist_display_times
            )

        slides.append(slide)
