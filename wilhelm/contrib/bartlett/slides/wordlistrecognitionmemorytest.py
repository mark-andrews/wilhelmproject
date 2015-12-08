from __future__ import absolute_import

#=============================================================================
# Standard library
#=============================================================================
import logging


#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.core import fields
from .slides import Slide, SessionSlide
from ..utils import WordRecognitionTestStimuliCheck
from ..widgets import WordlistDisplay, WordRecognitionTest, Tetris

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

class WordlistRecognitionMemoryTest(Slide):

    wordlist_display = fields.ForeignKey(WordlistDisplay)
    word_recognition_test = fields.ForeignKey(WordRecognitionTest)
    tetris = fields.ForeignKey(Tetris)

    @classmethod
    def new(cls,
            name,
            wordlist,
            inwords,
            outwords,
            start_wordlist_msg,
            start_memorytest_msg,
            test_times,
            wordlist_display_times,
            game_duration=120,
            game_speed=500):

        WordRecognitionTestStimuliCheck(wordlist, inwords, outwords)

        wordlist_display\
            = WordlistDisplay.new(wordlist = wordlist,
                                  start_msg = start_wordlist_msg,
                                  **wordlist_display_times)

        tetris = Tetris.new(duration = game_duration,
                            speed = game_speed)

        word_recognition_test\
            = WordRecognitionTest.new(inwords = inwords,
                                      outwords = outwords, 
                                      start_msg = start_memorytest_msg,
                                      **test_times)

        return cls._new(
            name = name,
            wordlist_display = wordlist_display,
            word_recognition_test = word_recognition_test,
            tetris = tetris)

    def get_slide_template_data(self):
        return dict(memorandum_type = 'word list')

    @property
    def widgets(self):
        return (self.wordlist_display, self.tetris, self.word_recognition_test)

class SessionWordlistRecognitionMemoryTest(SessionSlide):

    class Meta:
        verbose_name = 'SessWrdLstRecogMemTest'


    def feedback(self):

        try:
            session_widgets_feedback\
                = super(SessionWordlistRecognitionMemoryTest, self).feedback()

            summary = {}

            summary.update(session_widgets_feedback['WordlistDisplay'])
            summary.update(session_widgets_feedback['WordRecognitionTest'])

            return summary

        except Exception as e:
            exception_type = e.__class__.__name__
            exception_msg = e.message
            logger.warning('Could not provide feedback. %s: %s.'\
                           % (exception_type, exception_msg))
                
            return None
