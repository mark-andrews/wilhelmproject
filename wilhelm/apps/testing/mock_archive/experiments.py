'''
This is an test experiments.py. So far, basically just a copy of experiment
brisbane. It would be better to turn this into a minimal working example. 
'''
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
from contrib.bartlett.models import Playlist

#================================ End Imports ================================

class PlaylistFactory(object):

    @classmethod
    def new(cls):

        return Playlist.new(cls.slides)

def stimuluspath(filename):

    '''
    Return the full path of the stimulus file `filename`.

    '''

    this_dir = sys.thisDir(__file__)
    stimuli_dir = os.path.join(this_dir, 'stimuli')

    return os.path.abspath(os.path.join(stimuli_dir, filename))

class Fribs(PlaylistFactory):

    configfile = stimuluspath('brisbane.cfg')
    sys.assert_file_exists(configfile)
    config = configobj.ConfigObj(configfile)

    parameters = config['parameters'].dict()
    memoranda = config['memoranda'].dict()
    instructions = config['instructions'].dict()

    slides = []

    for key, description in config['slides'].items():

        slidetype = description['type']

        memorandum_name = description['memorandum']

        try:
            memorandum = memoranda[memorandum_name]
        except KeyError:
            errmsg = 'We do not have a record of the memorandum: %s' \
                    % description['memorandum']
            raise KeyError, errmsg

        if description['type'] == 'TextRecognitionMemoryTest':

            text_parameters = parameters['text']
            test_parameters = parameters['recognition']
            wordlist_parameters = parameters['wordlist']

            slide = slides.TextRecognitionMemoryTest.new(
                name = memorandum_name,
                title = memorandum['title'],
                text = strings.fill(memorandum['text']),
                inwords = memorandum['inwords'].split(),
                outwords = memorandum['outwords'].split(),
                start_text_msg = instructions['start_text_msg'],
                start_memorytest_msg = instructions['start_memorytest_msg'],
                test_times = (
                    test_parameters['isi'],
                    test_parameters['fadeInSpeed'],
                    test_parameters['fadeOutSpeed']
                    ),
                reading_times = (
                    text_parameters['minimum_reading_time'],
                    text_parameters['maximum_reading_time']
                    )
                )

        elif description['type'] == 'WordListRecognitionMemoryTest':
    
            wordlist_parameters = parameters['wordlist']
            test_parameters = parameters['recognition']
        
            slide = slides.WordListRecognitionMemoryTest.new(
                name = memorandum_name,
                inwords = memorandum['inwords'].split(),
                outwords = memorandum['outwords'].split(),
                wordlist = memorandum['wordlist'].split(),
                start_wordlist_msg = instructions['start_wordlist_msg'],
                start_memorytest_msg = instructions['start_memorytest_msg'],
                test_times = (
                    test_parameters['isi'],
                    test_parameters['fadeInSpeed'],
                    test_parameters['fadeOutSpeed']
                    ),
                wordlist_times = (
                    wordlist_parameters['isi'],
                    wordlist_parameters['duration'],
                    wordlist_parameters['fadeInSpeed'],
                    wordlist_parameters['fadeOutSpeed']
                    )
            )

        elif description['type'] == 'WordListRecallMemoryTest':
    
            wordlist_parameters = parameters['wordlist']
            recall_parameters = parameters['recall']

            slide = slides.WordListRecallMemoryTest.new(
                name = memorandum_name,
                optionlen = recall_parameters['optionlen'],
                wordlist = memorandum['wordlist'].split(),
                start_wordlist_msg = instructions['start_wordlist_msg'],
                start_memorytest_msg = instructions['start_memorytest_msg'],
                wordlist_times = (
                    wordlist_parameters['isi'],
                    wordlist_parameters['duration'],
                    wordlist_parameters['fadeInSpeed'],
                    wordlist_parameters['fadeOutSpeed']
                    )
            )

        slide.test()
        slides.append(slide)

## Where this module lives.
#this_dir = sys.thisDir(__file__)
#
## Full path of this directory where the experiment stimuli live.
#stimuli_dir = os.path.join(this_dir, 'stimuli')
#
#def stimuluspath(filename):
#    '''
#    Return the full path of the stimulus file `filename`.
#
#    '''
#    return os.path.abspath(os.path.join(stimuli_dir, filename))
#
#class Fribs(projector.Playlist):
#    ''' Playlist class for the brisbane experiment.'''
#
#    # Read in the stimulus configuration file.
#    configfile = stimuluspath('fribs.cfg')
#    sys.assert_file_exists(configfile)
#    config = configobj.ConfigObj(configfile)
#
#    def __init__(self):
#        ''' Initialize the experiment.
#
#        Experimental stimuli are in random order. 
#
#        '''
#        super(Fribs, self).__init__()
#
#        # Extract the parameters, memoranda, instructions.
#        parameters = self.config['parameters'].dict()
#        memoranda = self.config['memoranda'].dict()
#        instructions = self.config['instructions'].dict()
#
#        _slides = [] # Where we save the slides.
#
#        for key, description in self.config['slides'].items():
#
#            # Get the slide type and the memorandum.
#
#            # Slide type.
#            slidetype = description['type']
#
#            # Name of the memorandum
#            memorandum_name = description['memorandum']
#
#            # Try to get the memorandum information from the cfg file.
#            try:
#                memorandum = memoranda[memorandum_name]
#            except KeyError:
#                errmsg = 'We do not have a record of the memorandum: %s' \
#                        % description['memorandum']
#                raise KeyError, errmsg
#                
#
#            if description['type'] == 'TextRecognitionMemoryTest':
#
#                text_parameters = parameters['text']
#                test_parameters = parameters['recognition']
#                wordlist_parameters = parameters['wordlist']
#
#                slide = slides.TextRecognitionMemoryTest(
#                    name = memorandum_name,
#                    title = memorandum['title'],
#                    text = strings.fill(memorandum['text']),
#                    inwords = collections.rshuffle(memorandum['inwords'].split()),
#                    outwords = collections.rshuffle(memorandum['outwords'].split()),
#                    start_text_msg = instructions['start_text_msg'],
#                    start_memorytest_msg = instructions['start_memorytest_msg'],
#                    test_times = (
#                        test_parameters['isi'],
#                        test_parameters['fadeInSpeed'],
#                        test_parameters['fadeOutSpeed']
#                        ),
#                    reading_times = (
#                        text_parameters['minimum_reading_time'],
#                        text_parameters['maximum_reading_time']
#                        )
#                    )
#
#            elif description['type'] == 'WordListRecallMemoryTest':
#        
#                wordlist_parameters = parameters['wordlist']
#                recall_parameters = parameters['recall']
#
#                slide = slides.WordListRecallMemoryTest(
#                    name = memorandum_name,
#                    optionlen = recall_parameters['optionlen'],
#                    wordlist = collections.rshuffle(memorandum['wordlist'].split()),
#                    start_wordlist_msg = instructions['start_wordlist_msg'],
#                    start_memorytest_msg = instructions['start_memorytest_msg'],
#                    wordlist_times = (
#                        wordlist_parameters['isi'],
#                        wordlist_parameters['duration'],
#                        wordlist_parameters['fadeInSpeed'],
#                        wordlist_parameters['fadeOutSpeed']
#                        )
#                )
#
#            slide.test()
#            _slides.append(slide)
#
#
#        experimentalslides = [
#        s for s in _slides 
#        if isinstance(s, slides.TextRecognitionMemoryTest) or
#        isinstance(s, slides.WordListRecallMemoryTest)
#        ]
#
#    
#        random.shuffle(experimentalslides) # in-place shuffle
#
#        self.make_slidedeque(experimentalslides)
